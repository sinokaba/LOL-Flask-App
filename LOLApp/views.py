from LOLApp import *
from flask import render_template, redirect, url_for, escape, request, session, flash, Response
import regex, json, ast, pygal
from .summoner import Summoner
from .api_calls import APICalls
from .models import *

app.secret_key = "change this to something super secret"

@app.before_request
def before_request():
	#create and initialize db
	initialize_db()

#close database whether the request succeeds or fails
@app.teardown_request
def teardown_request(exception):
	database.close()
	return exception

@app.route('/')
def index():
	champ_data = ChampStats.select().where(ChampStats.rankTier == "diamondPlus").order_by((ChampStats.oaRating/ChampStats.totalPlays).desc())
	champs_basic = Champion.select()
	player_data = Player.select().where(Player.region == "NA").order_by(Player.oaRating.desc())
	top_5_champs = {}
	top_5_offmeta_champs = {}
	top_5_players = player_data[:5]
	for champ in champ_data:
		if(champ.totalPlays >= 10 and len(top_5_champs) < 5):
			if(champ not in top_5_champs):
				name = Champion.get(Champion.champId == champ.champId).name
				top_5_champs[champ] = {"name":name, "role":champ.role, "wr":round(champ.totalWins/champ.totalPlays, 2)*100, "rating":round(champ.oaRating/champ.totalPlays,2)}
		if(len(top_5_offmeta_champs) < 5 and (int(champ.rolePlays)/champ.totalPlays) <= .2):
			if(champ not in top_5_offmeta_champs):
				champ_ob = Champion.get(Champion.champId == champ.champId).name
				top_5_offmeta_champs[champ] = {"name":name, "role":champ.role, "wr":round(champ.totalWins/champ.totalPlays, 2)*100, "rating":round(champ.oaRating/champ.totalPlays,2)}
	return render_template("index.html", best_champs=top_5_champs, best_offmeta_champs=top_5_offmeta_champs, best_players=top_5_players, champ_info=champs_basic)

@app.route('/search', methods=["GET", "POST"])
def get_data():
	if request.method == "POST":
		name = request.form["name"]
		region = request.form["region"]
		champ_query = Champion.select().where(Champion.name == name)
		print(Champion.get(Champion.champId == 31).name, " vs ", name)
		if(champ_query.exists()):
			return redirect(url_for('get_champ', name=name, region=region))
		elif(valid_name(name)):
			return redirect(url_for('get_summoner', name=name, region=region))
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		return render_template("index.html")

def valid_name(name):
	expression = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	if((len(name) >= 3 and len(name) <= 16) and expression.match(name) is not None):
		return True
	return False

@app.route('/<region>/champ/<name>')
def get_champ(name, region):
	return render_template("champ.html", champ=name, region=region)

@app.route('/<region>/summoner/<name>')#@cache.cached(timeout=500)
def get_summoner(name, region):
	api
	#cache = MemcachedCache(['127.0.0.1:11211'])
	validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	if(region != "NA"):
		api = APICalls(region)
	#print("API: " , api)
	name_l = len(name)
	summoner_data = Summoner(name, region, api)
	query = Player.select().where(Player.name == summoner_data.name)
	if(not query.exists()):
		if(summoner_data.account_exists):
			match_history = None #cache.get("mh-"+name)
			league_data = None #cache.get("rank-"+name)
			if(match_history is None and league_data is None):
				match_history = summoner_data.get_ranked_match_history()
				league_data = summoner_data.get_league_rank()
				#cache.set("mh-"+name, match_history, timeout=3600)
				#cache.set("rank-"+name, league_data, timeout=7200)
			p_icon = summoner_data.get_profile_icon()
		
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

@app.route('/test')
def react_test():
	items = api.get_items_info()
	tags = []
	for k,v in items["data"].items():
		for tag in v["tags"]:
			if(tag not in tags):
				tags.append(tag)
	print(tags)
	print(items["data"]["1001"])
	return "boo"

@app.route("/crawl")
def crawl():
	global api
	champ_data = ChampStats.select().where(ChampStats.rankTier == "diamondPlus", ChampStats.region == "NA")
	player_data = Player.select().where(Player.region == "NA").order_by(Player.oaRating.desc())
		#print("Champ id: ", champ.champ_id, " bans: ", champ.bans)
		#print("Insufficient data.")
	def convert_to_dict(champ_data):
		return ast.literal_eval(champ_data)
	def get_kda(kda):
		if(kda["deaths"] == 0):
			kda["deaths"] = 1
		return round((kda["kills"]+kda["assists"])/kda["deaths"],2)
	def get_percent(nume, dem):
		if(dem == 0):
			dem = 1
		return round((nume/dem)*100,2)
	#Champions.delete_instance()
	line_chart = pygal.HorizontalBar(height=1500, spacing=10, width=500)
	line_chart.title = "Overall stats"
	index = 0
	champion = []
	champ_wr = []
	champ_pr = []
	champ_rating = []
	#champ_rr = []
	champ_br = []
	"""
	for role in roles:
		plays = champ.plays - roles[role]["count"]
		for matchup,stats in roles[role]["matchups"].items():
			pick_rate_against = round((stats["against"]/plays)*100,2)
			if(pick_rate_against > 1):
				enemy = (Champions.get(Champions.champId == matchup, Champions.rank == "gold", Champions.region == "NA"))
				champion.append(ast.literal_eval(enemy.info)["name"])
				champ_wr.append(round((stats["wins"]/stats["against"])*100,2))
				champ_pr.append(pick_rate_against)
	
	for champ in champ_data:
		roles = ast.literal_eval(champ.roles)
		for role in roles:
			print("rank:",champ.rank)
			info = ast.literal_eval(champ.info)
			champion.append(info["name"] + "-" + role)
			champ_pr.append(get_percent(champ.plays, 10000))
			champ_rating.append(round(roles[role]["rating"]/roles[role]["plays"], 2))
			champ_wr.append(get_percent(roles[role]["wins"], champ.plays))
			champ_br.append(get_percent(champ.bans, 10000))
	"""
	top_10_players = []
	top_10_id = []
	top_10_players_rating = []
	top_10_ds = []
	top_10_wins = []
	top_10_vis_sc = []
	top_10_obj_sc = []
	wpm = []
	for player in player_data:
		games = player.wins + player.loses
		print(player.name, " wins: ", player.wins, " loses: ", player.loses, " total: ", games)
		wpm.append((player.kp/games)*100)
		#top_10_wins.append((player.wins/games)*100)
		top_10_vis_sc.append(player.visScore/games)
		top_10_obj_sc.append(player.objScore/games)
		top_10_ds.append((player.dmgShare/games)*100)
		top_10_players.append(player.name + "-" + player.currRank)
		top_10_id.append(player.accountId)
		top_10_players_rating.append(player.oaRating/games)
	print(top_10_id)
	line_chart.x_labels = map(str, top_10_players)
	line_chart.add("Rating", top_10_players_rating)
	#line_chart.add("kill %", wpm)
	#line_chart.add("Damage %", top_10_ds)
	line_chart.add("Vision score per game ", top_10_vis_sc)
	line_chart.add("Objective score per game", top_10_obj_sc)
	#line_chart.add("wins", top_10_wins)
	#line_chart.add("Wirate", champ_wr)
	#line_chart.add("Pickrate", champ_pr)
	#line_chart.add("Banrate", champ_br)
	line_chart = line_chart.render_data_uri()
	#print("Number of champions in db: ", Champions.select().count())
	print("Number of players recorded from 10k matches, ", Player.select().count())
	print("Number of games", GamesVisited.select().count())
	"""
	line_chart.x_labels = map(str, champion)
	line_chart.add("Laning against", champ_wr)
	line_chart.add("Pickrate against", champ_pr)
	line_chart = line_chart.render_data_uri()
	"""
	#return render_template("test.html", data=data, converter=convert_to_dict, get_kda=get_kda, rem_decimals=rem_decimals)
	return render_template("test.html", wr_chart=line_chart)
	
	#return "boo"
