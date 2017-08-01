from LOLApp import *
from flask import render_template, redirect, url_for, escape, request, session, flash, Response, jsonify
import regex, json, ast, pygal, _pickle
from pygal.style import DefaultStyle
from pygal import Config
from .APIConstants import *
from .summoner import Summoner
from .apiCalls import APICalls
from .DBModels import *
from .statGraphs import StatGraphs
from .parseChampStats import *

"""
	Find a way to link getting player data with adding champ data (of course check if the game has already been visited)
	Should the data of other players being looked at each game also be calculated? Will potentially save a ton of time in the future, as will
	reduce the number of calls needed to make
"""

riot_api = APICalls()
print(GamesVisited.select().where(GamesVisited.patch == CURRENT_PATCH).count())
global_avg = get_global_avg(ChampRoleOverallStats.select())

@app.before_request
def before_request():
	#create and initialize db
	initialize_db()

#close database whether the request succeeds or fails
@app.teardown_request
def teardown_request(exception):
	postgres_db.close()
	return exception

@app.route('/')
def index():
	default_region = "NA"

	return render_template("index.html", region_data=region_overall_stats(default_region), region=default_region)

@app.route('/search', methods=["GET", "POST"])
def get_data():
	if request.method == "POST":
		name = request.form["name"].title()
		if("region" in request.form):
			session.pop("region", None)
			session["region"] = request.form["region"]
		region = escape(session["region"])
		print(name)
		champ_query = ChampBase.select().where(ChampBase.name == name.strip())
		if(champ_query.exists()):
			return redirect(url_for('get_champ', name=name, region=region))
		elif(valid_name(name)):
			return redirect(url_for('get_summoner', name=name, region=region))
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		if("region" in request.form):
			return redirect(url_for("index"))
		else:
			return redirect(url_for('get_champ', name=escape(session["champ"]), region=region))

def valid_name(name):
	expression = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	if((len(name) >= 3 and len(name) <= 16) and expression.match(name) is not None):
		return True
	return False

@app.route('/<region>/champ/<name>')
def get_champ(name, region):
	#should display 3 roles at most to avoid awkward formatting
	this_patch = CURRENT_PATCH
	session["champ"] = name
	print("name: ", name)
	print("region: ", region)
	champ_basic = ChampBase.get(ChampBase.name == name)
	players = PlayerRankStats.select().join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
		PlayerBasic.region == region,
		ChampBasic.champId == champ_basic.champId
		)
	print("total games: ", GamesVisited.select().count())
	champ_basic.statsRanking = _pickle.loads(champ_basic.statsRanking)
	print(champ_basic.statsRanking)
	total_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == "NA").count()
	print("total games this patch: ", total_games)
	champ_data = ChampRoleOverallStats.select().join(ChampRankStats).join(StatsBase).where(
		ChampRankStats.champId == champ_basic.champId, 
		StatsBase.region == region)
	tips = _pickle.loads(champ_basic.tips)
	#enemy_tips = _pickle.loads(champ_basic.enemyTips)[0]
	splash = champ_basic.image.split(".")[0]
	#print("img: ", champ.image)
	total_plays = total_wins = total_rating = 0
	total_dpg = total_dmpg = total_vis = total_obj = 0
	#only taking into account current patch
	roles_vis = []
	for champ_role in champ_data:
		if(champ_role.role not in roles_vis):
			print("role: ", champ_role.role, " plays: ", champ_role.roleTotalPlays)
			total_plays += champ_role.roleTotalPlays
			total_wins += champ_role.roleTotalWins
			total_rating += champ_role.roleTotalRating
			roles_vis.append(champ_role.role)
	min_plays = total_plays*.07
	print("total plays: ", total_plays, " minimum number of plays: ", min_plays)
	most_common_roles = ChampRoleOverallStats.select(ChampRoleOverallStats, ChampRankStats).join(ChampRankStats).join(StatsBase).where(
		ChampRankStats.champId == champ_basic.champId, 
		StatsBase.region == region, 
		ChampRoleOverallStats.roleTotalPlays > min_plays).order_by(ChampRoleOverallStats.roleTotalPlays.desc()).aggregate_rows()
	print("number of roles: ", len(most_common_roles))
	"""
	for league in TeamBase.select().where(TeamBase.region == region):
		q = TeamStats.select().join(TeamBase).where(TeamBase.region == region, TeamBase.leagueTier == league.leagueTier)
		if(q.exists()):
			if(league.leagueTier not in total_games_by_tier):
				total_games_by_tier[league.leagueTier] = _pickle.loads(league.team_stats.get().teamGameStats)["wins"]
			else:
				total_games_by_tier[league.leagueTier] += _pickle.loads(league.team_stats.get().teamGameStats)["wins"]
	"""
	#print(total_games_by_tier)	
	bans_by_patch = _pickle.loads(most_common_roles[0].totalBansByPatch)
	total_bans = bans_by_patch[this_patch]

	kills = deaths = assists = 0
	in_game_stats = {}
	champs_by_tier = ChampRankStats.select().join(StatsBase).where(StatsBase.region == region, ChampRankStats.champId == champ_basic.champId)
	for role_champ in champs_by_tier:
		kills += role_champ.kills
		deaths += role_champ.deaths
		assists += role_champ.assists
		role_champ.gameStats = _pickle.loads(role_champ.gameStats)

		total_dmpg += role_champ.gameStats["dmpg"]
		total_dpg += role_champ.gameStats["dpg"]
		total_vis += role_champ.gameStats["visScore"]
		total_obj += role_champ.gameStats["objScore"]
		if(role_champ.overallStats.role not in in_game_stats):
			if(role_champ.gameStats is not None):
				in_game_stats[role_champ.overallStats.role] = role_champ.gameStats
		else:
			in_game_stats[role_champ.overallStats.role]["dmpg"] += role_champ.gameStats["dmpg"]
			in_game_stats[role_champ.overallStats.role]["dpg"] += role_champ.gameStats["dpg"]
			in_game_stats[role_champ.overallStats.role]["visScore"] += role_champ.gameStats["visScore"]
			in_game_stats[role_champ.overallStats.role]["objScore"] += role_champ.gameStats["objScore"]

	cum_stats = {"rating":round(total_rating/total_plays,2), 
				"dpg":round(total_dpg/total_plays,2), 
				"dmpg":round(total_dmpg/total_plays,2),
				"vis":round(total_vis/total_plays,2),
				"objectives": round(total_obj/total_plays,2)
				}
	rank_stats = load_champ_details(most_common_roles)
	
	avg_kills = round(kills/total_plays,2)
	avg_deaths = round(deaths/total_plays,2)
	avg_assists = round(assists/total_plays,2)
	avg_dpg = round(total_dpg/total_plays, 2)
	avg_dmpg = round(total_dmpg/total_plays, 2)
	print("average kills: ", avg_kills, " avg deaths: ", avg_deaths, " average assists: ", avg_assists)
	if(deaths == 0):
		deaths = 1
	kda = round((kills+assists)/deaths,2)
	#tags = _pickle.loads(champ_basic.tags)

	graphs = StatGraphs()
	overall_wr = graphs.get_half_pie([total_wins, total_plays], ('#007E33', '#CC0000'))
	
	overall_pr = graphs.get_half_pie([total_plays, total_games], ('#0d47a1', '#757575'))

	overall_br = graphs.get_half_pie([total_bans, total_games], ('#CC0000', '#757575'))
	
	"""
	overall_wr = pygal.Pie(inner_radius=.65, print_values=True)
	overall_wr.title = 'Winrate'
	overall_wr.add('Wins', total_wins)
	overall_wr.add('Loses', total_plays-total_wins)
	overall_wr = overall_wr.render_data_uri()
	"""
	overall_stats = graphs.get_stacked_horizontal_bar(
					['KDA', 'Rating', 'DPG', 'DMPG', 'Vision', 'Objectives'],
					{
					"Average":global_avg,
					name: [kda,  cum_stats["rating"], {'value': cum_stats["dpg"], 'label': "Damage per gold"}, 
							{'value':cum_stats["dmpg"], 'label': "Damage mitigated per gold"}, cum_stats["vis"], cum_stats["objectives"]]
					},
					colors=("#2E2E2E","#0d47a1")
				)
	"""
	patch_stats_graph = pygal.Line(
							print_labels=True,
							width=1200,
							human_readable = True,
							style=custom_style_1
						)
	patch_stats_graph.x_labels = "7.12.1", "7.13.1", "7.14.1"
	for patch in patch_list:
		if(patch not in patch_stats_cum):
			patch_stats_cum[patch] = {"wins":None, "plays":None, "rating":None}
		if(patch not in bans_by_patch):
			bans_by_patch[patch] = None
	patch_stats_graph.add("Plays", [patch_stats_cum["7.12.1"]["plays"], patch_stats_cum["7.13.1"]["plays"], patch_stats_cum["7.14.1"]["plays"]])
	patch_stats_graph.add("Bans", [bans_by_patch["7.12.1"], bans_by_patch["7.13.1"], bans_by_patch["7.14.1"]])
	patch_stats_graph = patch_stats_graph.render_data_uri()
	"""
	return render_template("champ.html", **locals())

def load_champ_details(most_common_roles):
	rank_stats = {}
	patch_stats_cum = {}
	for role in most_common_roles:
		print("id: ", role.id)
		print("num wins: ", role.roleTotalWins, " num plays: ", role.roleTotalPlays, " role: ", role.role)
		if(role.addons is not None):
			role.addons.spells = _pickle.loads(role.addons.spells)
			role.addons.skillOrder = _pickle.loads(role.addons.skillOrder)
			role.addons.keystone = _pickle.loads(role.addons.keystone)
			role.addons.items = _pickle.loads(role.addons.items)
			role.addons.runes = _pickle.loads(role.addons.runes)
			#print("runes: ", role.addons.runes)
			role.addons.matchups = _pickle.loads(role.addons.matchups)
		else:
			print("no addons: ", role.role)		
		if(role not in rank_stats):
			rank_stats[role.role] = [None, None, None, None]
		for rank in role.stats_by_rank:
			#print("most role rank: ", rank.leagueTier)
			rank.resultByTime = _pickle.loads(rank.resultByTime)
			rank.patchStats = _pickle.loads(rank.patchStats)
			for patch,stats in rank.patchStats.items():
				if(patch not in patch_stats_cum):
					patch_stats_cum[patch] = stats
				else:
					patch_stats_cum[patch]["wins"] += stats["wins"]
					patch_stats_cum[patch]["plays"] += stats["plays"]
					patch_stats_cum[patch]["rating"] += stats["rating"]			

			print(rank.patchStats)
			if(rank.baseInfo.leagueTier == "diamondPlus"):
				rank_name = "Diamond Plus"
			elif(rank.baseInfo.leagueTier == "silverMinus"):
				rank_name = "Silver Below"
			else:
				rank_name = rank.baseInfo.leagueTier.title()
			print(rank_name)
			if(rank_name == "Diamond Plus"):
				rank_stats[role.role][0] = {"rank":rank_name, "rank_data":rank}
			elif(rank_name == "Platinum"):
				rank_stats[role.role][1] = {"rank":rank_name, "rank_data":rank}
			elif(rank_name == "Gold"):
				rank_stats[role.role][2] = {"rank":rank_name, "rank_data":rank}
			else:
				rank_stats[role.role][3] = {"rank":rank_name, "rank_data":rank}				
		print(len(rank_stats[role.role]))
	return rank_stats, patch_stats_cum

@app.route('/_compare_champs')
def get_additional_champ():
	champ_name = request.args.get('name', None, type=str)
	print(champ_name)
	champ_data = ChampBase.get(ChampBase.name == champ_name)
	champ_stats = ChampRoleData.select().where(ChampRoleData.champId == champ_data.champId, ChampRoleData.region == escape(session["region"]))
	#a = request.args.get('a', None, type=str)
	return jsonify(result=_pickle.loads(champ_data.abilities))

@app.route('/_region_overall_stats')
def region_overall():
	region = request.args.get('region', None, type=str)
	
	return jsonify(result=region_overall_stats(region))

"""
@app.route('/_get_all_champs')
def get_all_champs():
	champ_names = []
	for champ in ChampBase.select():
		champ_names.append(champ.name)
	print(champ_names)
	return jsonify(result=champ_names)
"""
def region_overall_stats(region):
	num_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == region).count()
	champ_data = ChampRoleOverallStats.select(ChampRoleOverallStats, ChampRankStats).join(ChampRankStats).join(StatsBase).where(
		StatsBase.region == region).aggregate_rows().order_by(
		(ChampRoleOverallStats.roleTotalRating).desc())
	champs_basic = ChampBase.select()
	player_data = PlayerRankStats.select().join(PlayerBasic).where(
		PlayerBasic.region == region).order_by((PlayerRankStats.performance/PlayerRankStats.plays).desc())
	print("num players: ", player_data.count())
	top_5_champs = []
	top_5_offmeta_champs = []
	top_5_players = {}
	for player in player_data:
		if(player.plays >= 2 and player.basicInfo.rank is not None):
			if(len(top_5_players) < 5):
				#print("num players with the same id: ", PlayerBasic.select().where(PlayerBasic.accountId == player.basicInfo.accountId).count())
				#summoner_data = Summoner(default_region, riot_api, player.basicInfo.accountId)
				top_5_players[player.basicInfo.name] = {
									"rank": player.basicInfo.rank, 
									"player":
										{
										"rating":round(player.performance/player.plays,2), 
										"winrate":round((player.wins/player.plays)*100,2)
										} 
									}
			else:
				break
	for champion in champ_data:
		#if(champion.addons is not None):
			#print("items: ", _pickle.loads(champion.addons.runes))
		#print("id: ", champ.champId, " role: ", champ.role, " playrate: ", champ.roleroleTotalPlays/num_games)
		if(len(top_5_offmeta_champs) < 5 or len(top_5_champs) < 5 and champion.roleTotalPlays > 0):
			#print("champ t plays: ", champion.roleTotalPlays)
			rating = round(champion.roleTotalRating/champion.roleTotalPlays, 2)
			winrate = round((champion.roleTotalWins/champion.roleTotalPlays)*100, 2)
			#print(ChampBase.select().count())
			name = ChampBase.get(ChampBase.champId == champion.stats_by_rank[0].champId).name
			#print("name: ", name)
			if("Bot" in champion.role):
				champion.role = champion.role.split(" ")[1]
			if((champion.roleTotalPlays >= num_games*.01) and len(top_5_champs) < 5):
				#print("name: ", name)
				top_5_champs.append({
					"name":name, "role":champion.role, 
					"wr":winrate, 
					"rating":rating
				})
			elif(len(top_5_offmeta_champs) < 5 and (.001 < (champion.roleTotalPlays/num_games) <= .01)):
				top_5_offmeta_champs.append({
					"name":name, 
					"role":champion.role, 
					"wr":winrate, 
					"rating":rating
				})		
		else:
			break
	#print("top 5 champs: ", top_5_champs)
	print("yahoo")
	top_5_champs = sorted(top_5_champs, key=lambda k: k['rating'], reverse=True)
	top_5_offmeta_champs = sorted(top_5_offmeta_champs, key=lambda k: k['rating'], reverse=True)
	region_rank_data = [top_5_champs, top_5_players, top_5_offmeta_champs]
	print(region_rank_data)
	return region_rank_data	

@app.route('/<region>/summoner/<name>')#@cache.cached(timeout=500)
def get_summoner(name, region):
	#cache = MemcachedCache(['127.0.0.1:11211'])
	session["player"] = name
	#print("API: " , api)
	name_l = len(name)
	query = Player.select().where(Player.name == name, Player.region == region)
	if(not query.exists()):
		summoner_data = Summoner(name, region, riot_api)
		if(summoner_data.account_exists):
			#match_history = None #cache.get("mh-"+name)
			#league_data = None #cache.get("rank-"+name)
			#if(match_history is None and league_data is None):
			#match_history = summoner_data.get_ranked_match_history()
			league_data = summoner_data.get_league_rank()
				#cache.set("mh-"+name, match_history, timeout=3600)
				#cache.set("rank-"+name, league_data, timeout=7200)
			#p_icon = summoner_data.get_profile_icon()
			winrate = league_data["player"]["wins"]/(league_data["player"]["losses"]+league_data["player"]["wins"])
			"""
			#print(match_history)
			if(match_history == "Inactive"):
				return render_template("user.html",
					name=name,
					lvl=summoner_data.get_lvl(),
					region=region,
					profile_icon=p_icon)
			Player.create(
				account_id = summoner_data.acc_id,
				name = summoner_data.name,
				region = region,
				league = str(league_data),
				matches = str(match_history)
			)
			#print(match_history)
			#send_to_js(match_history)
			return render_template("user.html",
				name=name, lvl=summoner_data.get_lvl(),
				region=region, profile_icon=p_icon,
				matches=match_history, league=league_data)
			"""
			return render_template("player.html", name=name, region=region, rank_data=league_data, wr=winrate)

	else:
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		return render_template("index.html")



"""
@app.route('/search', methods=["GET", "POST"])
def get_data():
	global api
	name = request.form["name"]
	region = request.form["region"]
	if(name != ""):
		validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
		if((len(name) >= 3 and len(name) <= 16) and validate.match(name) is not None):
			if(region != "NA"):
				api = APICalls(region)
			#print("API: " , api)
			name_l = len(name)
			summoner_data = Summoner(name, region, api)
			match_history = None #cache.get("mh-"+name)
			league_data = None #cache.get("rank-"+name)
			if(summoner_data.account_exists):
				if(match_history is None and league_data is None):
					match_history = summoner_data.get_ranked_match_history()
					league_data = summoner_data.get_league_rank()
					#cache.set("mh-"+name, match_history, timeout=3600)
					#cache.set("rank-"+name, league_data, timeout=7200)
				p_icon = summoner_data.get_profile_icon()
			else:
				error = "Invalid Summoner name"
				lash("Please enter a valid summoner name")
				return render_template("index.html")
		return json.dumps(match_history)
"""

@app.route('/<region>/summoner/')
def re_route(region):
	error = "Invalid Summoner name"
	flash("Please enter a valid summoner name")
	return render_template("index.html")

#region specific, select region based of dropdown
@app.route('/teams_statistics')
def teams_stats():
	extra_stats = {}
	stats_base = TeamBase.select().join(StatsBase).where(StatsBase.region == "NA")

	for tier in stats_base:
		if(tier.baseInfo.leagueTier not in extra_stats):
			extra_stats[tier.baseInfo.leagueTier] = {}
		print(tier.baseInfo.leagueTier)
		for team in tier.team_stats:
			temp = _pickle.loads(team.teamGameStats)
			print(tier.baseInfo.leagueTier, temp)
			if("games" not in extra_stats[tier.baseInfo.leagueTier]):
				extra_stats[tier.baseInfo.leagueTier]["games"] = temp["wins"]
			else:
				extra_stats[tier.baseInfo.leagueTier]["games"] += temp["wins"]
			print("t: ", team)
			extra_stats[tier.baseInfo.leagueTier ][tier.teamId] = temp
		for monster in tier.monster_stats:
			if(monster.subtypeData):
				extra_stats[tier.baseInfo.leagueTier][monster.monsterType] = _pickle.loads(monster.subtypeData)
	total_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == "NA").count()
	return render_template("teams.html", **locals())

@app.route('/all_champs_statistics')
def all_champs_stats():
	all_champs = ChampRoleData.select().where(ChampRoleData.region == "NA")
	all_champs_d = {}
	for champ in all_champs:
		if(champ.champId not in all_champs_d):
			all_champs_d[champ.champId] = champ
	return render_template("allChamps.html", **locals())

@app.route('/faq')
def faq():
	#all_champs = 
	return render_template("faq.html")
