from LOLApp import *
from flask import render_template, redirect, url_for, escape, request, session, flash, Response, jsonify
import regex, json, pygal, _pickle
from playhouse.shortcuts import model_to_dict, dict_to_model
from pygal.style import DefaultStyle
from pygal import Config
from APIConstants import *
from .summoner import Summoner
from .apiCalls import APICalls
from .DBModels import *
from .statGraphs import StatGraphs
from .parseChampStats import *
from geolite2 import geolite2

"""
	Find a way to link getting player data with adding champ data (of course check if the game has already been visited)
	Should the data of other players being looked at each game also be calculated? Will potentially save a ton of time in the future, as will
	reduce the number of calls needed to make
"""

riot_api = APICalls()
global_avg = get_global_avg(ChampOverallStatsByRole.select())
rank_tiers = {"diamondPlus":"Diamond Plus", "gold":"Gold", "platinum":"Platinum", "siver":"Silver Below", "bronze":"Silver Below"}

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
	reader = geolite2.reader()
	ip = request.remote_addr
	ip_lookup = reader.get(ip)
	print(ip_lookup)
	if(ip_lookup is not None):
		continent = ip_lookup["continent"]
		if(continent != "NA" or continent != "EU"):
			region = ip_lookup["country"]["iso_code"]
		else:
			region = continent["code"]
		if(region == "EU"):
			region = "EUW"
		if(region not in PLATFORMS):
			region = "NA"
	else:
		region = "NA"
	print(region)
	return render_template("index.html", region_data=region_overall_stats(region), region=region)

@app.route('/search', methods=["GET", "POST"])
def get_data():
	if request.method == "POST":
		name = request.form["name"].title()
		if("region" in request.form):
			session.pop("region", None)
			session["region"] = request.form["region"]
		region = escape(session["region"])
		print("NAME: ", name)
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
	if(name != "Wukong"):
		champ_key = name
	else:
		champ_key = "MonkeyKing"
	latest_longest_patch = LAST_PATCH
	item_boxes = [None, "Start", "Consumables", "Core", "Boots", "Early Ahead", "Early Behind", "Situational"]
	session["champ"] = name
	total_games_by_rank_q = GamesVisited.select(GamesVisited, StatsBase).join(StatsBase).where(StatsBase.region == region).aggregate_rows()
	total_games_by_rank = {}
	for rank_key,rank_tier in rank_tiers.items():
		total_games_by_rank[rank_tier] = GamesVisited.select().join(StatsBase).where(StatsBase.region == region, StatsBase.leagueTier == rank_key).count()
	print("name: ", name)
	print("region: ", region)
	champ_basic = ChampBase.get(ChampBase.name == name)
	passive = _pickle.loads(champ_basic.passive)
	abilities = _pickle.loads(champ_basic.abilities)
	champ_id = champ_basic.champId
	movespeed_placement = ChampBase.select().where(ChampBase.movespeed > champ_basic.movespeed).count() + 1
	armor_placement = ChampBase.select().where(ChampBase.armor > champ_basic.armor).count() + 1
	armorPL_placement = ChampBase.select().where(ChampBase.armorPL > champ_basic.armorPL).count() + 1
	ad_placement = ChampBase.select().where(ChampBase.ad > champ_basic.ad).count() + 1
	adPL_placement = ChampBase.select().where(ChampBase.adPL > champ_basic.adPL).count() + 1
	hp_placement = ChampBase.select().where(ChampBase.hp > champ_basic.hp).count() + 1
	hpPL_placement = ChampBase.select().where(ChampBase.hpPL > champ_basic.hpPL).count() + 1
	hpRegen_placement = ChampBase.select().where(ChampBase.hpRegen > champ_basic.hpRegen).count() + 1
	hpRegenPL_placement = ChampBase.select().where(ChampBase.hpRegenPL > champ_basic.hpRegenPL).count() + 1
	mr_placement = ChampBase.select().where(ChampBase.mr > champ_basic.mr).count() + 1
	mrPL_placement = ChampBase.select().where(ChampBase.mrPL > champ_basic.mrPL).count() + 1
	attackspeed_placement = ChampBase.select().where(ChampBase.attackspeed > champ_basic.attackspeed).count() + 1
	attackspeedPL_placement = ChampBase.select().where(ChampBase.attackspeedPL > champ_basic.attackspeedPL).count() + 1
	if( champ_basic.resource == "Mana"):
		mana_placement = ChampBase.select().where(ChampBase.mana > champ_basic.mana).count()
		manaPL_placement = ChampBase.select().where(ChampBase.manaPL > champ_basic.manaPL).count()
		manaRegen_placement = ChampBase.select().where(ChampBase.manaRegen > champ_basic.manaRegen).count()
		manaRegenPL_placement = ChampBase.select().where(ChampBase.manaRegenPL > champ_basic.manaRegenPL).count()

	similar_champs = ChampBase.select().where(
		(ChampBase.champId != champ_id) &
		(
		((ChampBase.role1 == champ_basic.role1) | (ChampBase.role2 == champ_basic.role2)) &
		((ChampBase.tag1 == champ_basic.tag1) & (ChampBase.tag2 == champ_basic.tag2))
		)
		)[:4]
	players = PlayerRankStats.select(PlayerRankStats, PlayerBasic).join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
		PlayerBasic.region == region,
		ChampBasic.champId == champ_id
		).aggregate_rows()
	print("total games: ", GamesVisited.select().count())
	champ_basic.statsRanking = _pickle.loads(champ_basic.statsRanking)
	print(champ_basic.statsRanking)
	total_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == "NA").count()
	print("total games this patch: ", total_games)
	champ_overall = ChampOverallStats.get(ChampOverallStats.region == region, ChampOverallStats.champId == champ_id)
	tips = _pickle.loads(champ_basic.tips)
	#enemy_tips = _pickle.loads(champ_basic.enemyTips)[0]
	#print("img: ", champ.image)
	total_plays = champ_overall.totalPlays
	total_wins = champ_overall.totalWins
	total_rating = champ_overall.totalRating
	total_bans = champ_overall.totalBans	
	#only taking into account current patch
	splash = champ_basic.image.split(".")[0]
	print("t wins: ", total_wins, " t_plays: ", total_plays, " t_rating: ", total_rating, " t_bans: ", total_bans)
	"""
	roles_vis = []
	for champ_role in champ_data:
		if(champ_role not in roles_vis):
			print("role: ", champ_role, " plays: ", champ_roleTotalPlays)
			total_plays += champ_roleTotalPlays
			total_wins += champ_roleTotalWins
			total_rating += champ_roleTotalRating
			roles_vis.append(champ_role)
	"""
	min_plays = total_plays*.05
	print("total plays: ", total_plays, " minimum number of plays: ", min_plays)
	champ_roles_q = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).switch(ChampStatsByRank).join(StatsBase).where(
		(ChampStatsByRank.champId == champ_id) & 
		(StatsBase.region == region) & 
		(ChampOverallStatsByRole.roleTotalPlays > min_plays)).order_by(ChampOverallStatsByRole.roleTotalPlays.desc())

	champ_roles_q2 = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).switch(ChampStatsByRank).join(StatsBase).where(
		(ChampStatsByRank.champId == champ_id) & 
		(StatsBase.region == region))
	for role in champ_roles_q2:
		print("r: ", role.role, " plays: ", role.roleTotalPlays)

	most_common_roles = []
	roles_added = []
	total_laning = 0
	for champ_role in champ_roles_q:
		print("cur role: ", champ_role.role, " plays: ", champ_role.roleTotalPlays)
		if(champ_role.role not in roles_added):
			#print("adding to roles: ", champ_role.role)
			most_common_roles.append(champ_role)
			roles_added.append(champ_role.role)
			total_laning += champ_role.laning
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

	total_dpg = total_dmpg = total_vis = total_obj = total_cspm = total_gpm = 0
	kills = deaths = assists = 0
	in_game_stats = {}
	real_total_plays = 0
	roles_added = []
	role_true_total_plays = {}
	champs_by_tier = ChampStatsByRank.select().join(StatsBase).where(StatsBase.region == region, ChampStatsByRank.champId == champ_id)
	for role_champ in champs_by_tier:
		kills += role_champ.kills
		deaths += role_champ.deaths
		assists += role_champ.assists
		role_champ.gameStats = _pickle.loads(role_champ.gameStats)
		#print("dmpg: ", role_champ.gameStats["dmpg"], " tier: ", role_champ.baseInfo.leagueTier)
		total_dmpg += role_champ.gameStats["dmpg"]
		total_dpg += role_champ.gameStats["dpg"]
		total_vis += role_champ.gameStats["visScore"]
		total_obj += role_champ.gameStats["objScore"]
		total_cspm += role_champ.cspm
		total_gpm += role_champ.gpm
		if(role_champ.overallStats.role not in in_game_stats):
			role_true_total_plays[role_champ.overallStats.role] = 0
			if(role_champ.gameStats is not None):
				role_champ.gameStats["cspm"] = role_champ.cspm
				role_champ.gameStats["gpm"] = role_champ.gpm
				in_game_stats[role_champ.overallStats.role] = role_champ.gameStats
		else:
			in_game_stats[role_champ.overallStats.role]["dmpg"] += role_champ.gameStats["dmpg"]
			in_game_stats[role_champ.overallStats.role]["dpg"] += role_champ.gameStats["dpg"]
			in_game_stats[role_champ.overallStats.role]["visScore"] += role_champ.gameStats["visScore"]
			in_game_stats[role_champ.overallStats.role]["objScore"] += role_champ.gameStats["objScore"]
			in_game_stats[role_champ.overallStats.role]["cspm"] += role_champ.cspm
			in_game_stats[role_champ.overallStats.role]["gpm"] += role_champ.gpm
		patch_stats = _pickle.loads(role_champ.patchStats)
		for patch,patch_stat in patch_stats.items():
			role_true_total_plays[role_champ.overallStats.role] += patch_stat["plays"]

	true_total_plays = 0
	for role,plays in role_true_total_plays.items():
		true_total_plays += plays

	print("dmpg: ", total_dmpg, " t plays: ", total_plays, " real t plays? ", real_total_plays)
	cum_stats = {
				"rating":round(total_rating/total_plays,2),
				"laning":round((total_laning/true_total_plays)*2,2), 
				"dpg":round(total_dpg/true_total_plays,2), 
				"dmpg":round(total_dmpg/true_total_plays,2),
				"vis":round(total_vis/true_total_plays,2),
				"objectives": round(total_obj/true_total_plays,2),
				"cspm": round(total_cspm/true_total_plays, 2),
				"gpm": round(total_gpm/true_total_plays, 2),
				"avg_kills": round(kills/total_plays,2),
				"avg_deaths": round(deaths/total_plays,2),
				"avg_assists": round(assists/total_plays,2)
				}
	rank_stats = load_champ_details(most_common_roles, _pickle.loads(champ_overall.totalPlaysByPatch), champ_key)
	kda = round((cum_stats["avg_kills"]+cum_stats["avg_assists"])/cum_stats["avg_deaths"],2)
	#tags = _pickle.loads(champ_basic.tags)
	graphs = StatGraphs()
	overall_wr = round(total_wins/total_plays,3)
	overall_wr_str = '%.1f' % round((total_wins/total_plays)*100, 1)
	overall_wr_graph = graphs.get_half_pie([total_wins, total_plays], overall_wr, ('#007E33', '#CC0000'), ["Wins", "Losses"])
	
	overall_pr = round(total_plays/total_games,3)
	overall_pr_str = '%.1f' % round((total_plays/total_games)*100, 1)	
	overall_pr_graph = graphs.get_half_pie([total_plays, total_games], overall_pr, ('#0d47a1', '#757575'), ["Plays", "Total Games"])

	overall_br = round(total_bans/total_games,3)
	overall_br_str = '%.1f' % round((total_bans/total_games)*100, 1)		
	overall_br_graph = graphs.get_half_pie([total_bans, total_games], overall_br, ('#CC0000', '#757575'), ["Bans", "Total Games"])
	
	all_champs_played = ChampOverallStats.select().where(
		ChampOverallStats.region == region,
		ChampOverallStats.totalPlays > 0)

	rating_placement= (all_champs_played.select().where(
	 	(ChampOverallStats.totalRating/ChampOverallStats.totalPlays) > cum_stats["rating"]).count()) + 1
	pr_placement = br_placement = wr_placement = 1

	for champ in ChampOverallStats.select().where(ChampOverallStats.region == region):
		if(champ.totalPlays > 0):
			#print(champ.champId, champ.totalPlays)
			if((champ.totalWins/champ.totalPlays) > overall_wr):
				wr_placement += 1
			if((champ.totalPlays/total_games) > overall_pr):
				pr_placement += 1
			if((champ.totalBans/total_games) > overall_br):
				br_placement += 1
	
	overall_stats_graph = graphs.get_stacked_bar(
					['Rating', 'KDA', 'Laning', 'DPG', 'DMPG', 'Vision', 'Objectives'],
					{
					"Average":global_avg,
					name: [cum_stats['rating'], kda,  cum_stats["laning"], {'value': cum_stats["dpg"], 'label': "Damage per gold"}, 
							{'value':cum_stats["dmpg"], 'label': "Damage mitigated per gold"}, cum_stats["vis"], cum_stats["objectives"]]
					},
					colors=("#2E2E2E","#0d47a1")
				)
	#print(rank_stats[1])
	print(total_games_by_rank)
	print(rank_stats[4])
	return render_template("champ.html", **locals())

def load_champ_details(most_common_roles, t_plays, champ_key):
	graphs = StatGraphs()
	rank_stats = {}
	patch_stats_cum = {}
	kda_by_role = {}
	total_plays_by_patch = t_plays
	wr_by_game_length = {}
	matchups_by_role = {}
	for champ_role in most_common_roles:
		role = champ_role.role

		#print("id: ", champ_role.id)
		#print("num wins: ", champ_role.roleTotalWins, " num plays: ", champ_role.roleTotalPlays, " role: ", champ_role.role)
		if(role not in rank_stats):
			rank_stats[role] = [None, None, None, None]
		if(role not in patch_stats_cum):
			patch_stats_cum[role] = {}	
		if(role not in kda_by_role):
			kda_by_role[role] = {"kills":0, "assists":0, "deaths":0}		
		if(role not in wr_by_game_length):
			wr_by_game_length[role] = {}

		addons = champ_role.addons
		if(addons is not None):
			addons.skillOrder = get_skill_order(_pickle.loads(addons.skillOrder), champ_key)
			addons.keystone = filter_attribute(_pickle.loads(addons.keystone), 2, "keystone")
			addons.spells = filter_attribute(_pickle.loads(addons.spells), 1, "spells")
			addons.items = get_best_build(_pickle.loads(addons.items), champ_role.roleTotalPlays, role, champ_key)
			addons.runes = filter_runes(_pickle.loads(addons.runes), champ_role.roleTotalPlays)
			#print(addons.runes)
			#print(addons.spells)
			#print("runes: ", role.addons.runes)
			if(role not in matchups_by_role):
				matchups_by_role[role] = get_matchups(_pickle.loads(addons.matchups))
			print(addons.matchups)
			
		else:
			print("no addons: ", role)		

		patch_stats = patch_stats_cum[role]
		r_stats = rank_stats[role] 
		wins_by_length = {}
		for rank in champ_role.stats_by_league:
			tier = rank.baseInfo.leagueTier
			print("most role rank: ", tier)
			rank.patchStats = _pickle.loads(rank.patchStats)
			total_plays_this_rank = total_rating_this_rank = total_wins_this_rank = 0
			for patch,stats in rank.patchStats.items():
				if(patch not in patch_stats_cum[role]):
					patch_stats[patch] = stats
				else:
					patch_stats[patch]["wins"] += stats["wins"]
					patch_stats[patch]["plays"] += stats["plays"]
					patch_stats[patch]["rating"] += stats["rating"]	
				total_plays_this_rank += stats["plays"]
				total_rating_this_rank += stats["rating"]
				total_wins_this_rank += stats["wins"]
				print("patch: ", patch, " plays: ", stats, " t plays: ", t_plays)	
			result_by_game_length = _pickle.loads(rank.resultByTime)
			for game_period,result in result_by_game_length.items():
				if(game_period not in wins_by_length):
					wins_by_length[game_period] = result
				else:
					wins_by_length[game_period]["wins"] += result["wins"]
					wins_by_length[game_period]["games"] += result["games"]
			kda_by_role[role]["kills"] += rank.kills
			kda_by_role[role]["deaths"] += rank.deaths
			kda_by_role[role]["assists"] += rank.assists

			#print(rank.patchStats)
			if(tier == "diamondPlus"):
				rank_name = "Diamond Plus"
			elif(tier == "silverMinus"):
				rank_name = "Silver Below"
			else:
				rank_name = tier.title()
			print(rank_name)
			if(rank_name == "Diamond Plus"):
				r_stats[0] = {
				"rank": rank_name, 
				"rank_stats": rank, 
				"total_plays": total_plays_this_rank, 
				"total_rating": total_rating_this_rank, 
				"total_wins": total_wins_this_rank
				}
			elif(rank_name == "Platinum"):
				r_stats[1] = {
				"rank": rank_name, 
				"rank_stats": rank, 
				"total_plays": total_plays_this_rank, 
				"total_rating": total_rating_this_rank, 
				"total_wins": total_wins_this_rank
				}
			elif(rank_name == "Gold"):
				r_stats[2] = {
				"rank": rank_name, 
				"rank_stats": rank, 
				"total_plays": total_plays_this_rank, 
				"total_rating": total_rating_this_rank, 
				"total_wins": total_wins_this_rank
				}			
			else:
				r_stats[3] = {
				"rank": rank_name, 
				"rank_stats": rank, 
				"total_plays": total_plays_this_rank, 
				"total_rating": total_rating_this_rank, 
				"total_wins": total_wins_this_rank
				}		#print("p stats", role)
		patch_stats["stats_chart"] = graphs.get_patch_line(patch_stats, ('#0d47a1', '#007E33', '#757575'), total_plays_by_patch)
		wr_by_game_length[role] = graphs.get_wr_line(wins_by_length, ('#0d47a1', '#007E33', '#757575'))
	#print(wr_by_game_length)
	return rank_stats, patch_stats_cum, kda_by_role, wr_by_game_length, matchups_by_role

@app.route('/_compare_champs')
def get_additional_champ():
	champ_name = request.args.get('name', None, type=str)
	region = request.args.get('region', "NA", type=str)
	champ_data_dict = model_to_dict(ChampBase.get(ChampBase.name == champ_name))
	champ_stats_overall_dict = model_to_dict(ChampOverallStats.get(
		ChampOverallStats.champId == champ_data_dict["champId"], 
		ChampOverallStats.region == region))
	champ_stats_by_rank = ChampStatsByRank.select().join(StatsBase).where(
		ChampStatsByRank.champId == champ_data_dict["champId"],
		StatsBase.region == region
		)
	total_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == region).count()
	scores = {"cspm":0, "gpm":0, "kills":0, "deaths":0, "assists":0}
	for rank_stats in champ_stats_by_rank:
		in_game_scores = _pickle.loads(rank_stats.gameStats)
		for score_name,val in in_game_scores.items():
			if(score_name not in scores):
				scores[score_name] = val
			else:
				scores[score_name] += val
		scores["cspm"] += rank_stats.cspm
		scores["gpm"] += rank_stats.gpm
		scores["kills"] += rank_stats.kills
		scores["deaths"] += rank_stats.deaths
		scores["assists"] += rank_stats.assists
	champ_stats_overall_dict["ingame_scores"] = scores
	#champ_stats = ChampRoleData.select().where(ChampRoleData.champId == champ_data.champId, ChampRoleData.region == escape(session["region"]))
	#a = request.args.get('a', None, type=str)
	del champ_stats_overall_dict["totalRatingByPatch"]
	del champ_stats_overall_dict["totalBansByPatch"]
	del champ_stats_overall_dict["totalPlaysByPatch"]
	del champ_stats_overall_dict["totalWinsByPatch"]

	champ_data_dict["abilities"] = _pickle.loads(champ_data_dict["abilities"])
	champ_data_dict["passive"] = _pickle.loads(champ_data_dict["passive"])
	champ_data_dict["tips"] = _pickle.loads(champ_data_dict["tips"])
	champ_data_dict["statsRanking"] = _pickle.loads(champ_data_dict["statsRanking"])
	champ_data_dict["rank_stats"] = champ_stats_overall_dict
	champ_data_dict["total_games"] = total_games

	return jsonify(result=champ_data_dict)

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
	champ_data = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).join(StatsBase).where(
		StatsBase.region == region, ChampOverallStatsByRole.roleTotalPlays > 0).aggregate_rows().order_by(
		(ChampOverallStatsByRole.roleTotalRating/ChampOverallStatsByRole.roleTotalPlays).desc())
	champs_basic = ChampBase.select()
	player_data = PlayerRankStats.select().join(PlayerBasic).where(
		PlayerBasic.region == region).order_by((PlayerRankStats.performance/PlayerRankStats.plays).desc())
	print("num players: ", player_data.count())
	top_5_champs = []
	top_5_offmeta_champs = []
	top_5_players = {}
	for player in player_data:
		if(player.plays >= 15 and player.basicInfo.rank is not None):
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
			champ_id = champion.stats_by_league[0].champId
			champ_total_plays = ChampOverallStats.get(ChampOverallStats.champId == champ_id, ChampOverallStats.region == region).totalPlays
			#print(ChampBase.select().count())
			name = ChampBase.get(ChampBase.champId == champ_id).name
			#print("name: ", name)
			if("Bot" in champion.role):
				champion.role = champion.role.split(" ")[1]
			if((champion.roleTotalPlays >= num_games*.017) and len(top_5_champs) < 5):
				#print("name: ", name)
				top_5_champs.append({
					"name":name, "role":champion.role, 
					"wr":winrate, 
					"rating":rating
				})
			elif(len(top_5_offmeta_champs) < 5 and ((.001 < (champion.roleTotalPlays/num_games) <= .005) and (champion.roleTotalPlays/champ_total_plays >= .05))):
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

@app.route('/<region>/summoner/<name>')
def get_summoner(name, region):
	#cache = MemcachedCache(['127.0.0.1:11211'])
	session["player"] = name
	#print("API: " , api)
	name_l = len(name)
	summoner_data = Summoner(region, name, riot_api)
	lvl = summoner_data.get_lvl()
	print(summoner_data.account_exists(), lvl)
	if(summoner_data.account_exists() and lvl >= 30):
		print(summoner_data.acc_id)
		league_data = cache.get(region+"-league_data-"+name)		
		match_history = cache.get(region+"-mh-"+name)
		if(match_history is None or league_data is None):
			league_data = summoner_data.get_league_rank()
			match_history = summoner_data.get_ranked_match_history()
			cache.set(region+"-mh-"+name, match_history, timeout=3600)
			cache.set(region+"-league_data-"+name, league_data, timeout=7200)
		#print(league_data)
		#p_icon = summoner_data.get_profile_icon()
		if(league_data is not None):
			total_games = (league_data["losses"]+league_data["wins"])
			winrate = round((league_data["wins"]/(total_games*1.0)*100),2)
			profile_icon = summoner_data.profile_icon
			print("winrate: ", winrate)
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
			"""
			return render_template(
				"player.html", 
				this_patch=CURRENT_PATCH,
				matches_data=match_history, 
				league_data=league_data, 
				winrate=winrate, 
				player_tags_des=player_tags,
				summoner_data=summoner_data)
		return render_template(
			"player.html", 
			this_patch=CURRENT_PATCH, 
			summoner_data=summoner_data, 
			matches_data=match_history)
	else:
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		return redirect(url_for("index"))

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
	team_stats = {}
	rank_tier_key = ["diamondPlus", "platinum", "gold", "silverMinus"]
	for tier in stats_base:
		rank_tier = tier.baseInfo.leagueTier 
		if(rank_tier not in team_stats):
			team_stats[rank_tier] = {"teams":{}, "mons":{}}
		for team in tier.team_stats:
			temp = _pickle.loads(team.teamGameStats)
			if("games" not in team_stats[rank_tier]):
				team_stats[rank_tier]["games"] = temp["wins"]
			else:
				team_stats[rank_tier]["games"] += temp["wins"]
			team_stats[rank_tier]["teams"][tier.teamId] = temp
		for monster in tier.monster_stats:
			team_stats[rank_tier]["mons"][monster.monsterType] = model_to_dict(monster)
	print("team stats", team_stats)
	total_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == "NA").count()
	print(total_games)
	return render_template("teams.html", **locals())

@app.route('/all_champs_statistics')
def all_champs_stats():
	na_all_champs = ChampOverallStats.select().where(ChampOverallStats.region == "NA")
	euw_all_champs = ChampOverallStats.select().where(ChampOverallStats.region == "EUW")
	eune_all_champs = ChampOverallStats.select().where(ChampOverallStats.region == "EUNE")
	kr_all_champs = ChampOverallStats.select().where(ChampOverallStats.region == "KR")
	all_champs_data = {
		"na": na_all_champs, 
		"euw": euw_all_champs, 
		"eune": eune_all_champs,
		"kr": kr_all_champs
		}
	#all_champs_d = {}
	return render_template("allChamps.html", all_champs_data=all_champs_data)

@app.route('/faq')
def faq():
	#all_champs = 
	return render_template("faq.html")
