from LOLApp import app, api, cache
from flask import render_template, redirect, url_for, escape, request, session, flash, Response
import regex, json, ast, pygal
from .summoner import Summoner
from .api_calls import APICalls
from .models import *
from .lol_crawler import LolCrawler

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
    return render_template("index.html")

@app.route('/search', methods=["GET", "POST"])
def get_data():
	if request.method == "POST":
		name = request.form["name"]
		region = request.form["region"]
		if(name != ""):
			return redirect(url_for('get_summoner', name=name, region=region))
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		return render_template("index.html")


@app.route('/<region>/summoner/<name>')#@cache.cached(timeout=500)
def get_summoner(name, region):
	global api
	#cache = MemcachedCache(['127.0.0.1:11211'])
	validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	if((len(name) >= 3 and len(name) <= 16) and validate.match(name) is not None):
		if(region != "NA"):
			api = APICalls(region)
		#print("API: " , api)
		name_l = len(name)
		summoner_data = Summoner(name, region, api)
		query = Summoners.select().where(Summoners.name == summoner_data.name)
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
				Summoners.create(
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
			data = Summoners.get(Summoners.name == summoner_data.name)
			return render_template("user.html", 
				name=data.name, lvl=30, 
				region=data.region, profile_icon=None, 
				matches=ast.literal_eval(data.matches), league=ast.literal_eval(data.league))
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
	champ_data = Champions.select().where(Champions.rank == "diamondPlus", Champions.region == "NA")
	player_data = Summoners.select().where(Summoners.region == "NA").order_by(Summoners.rating.desc())
		#print("Champ id: ", champ.champ_id, " bans: ", champ.bans)
		#print("Insufficient data.")

	for champion in champ_data:
		if(champion.champId == 23):
			champ = champion
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
	info = ast.literal_eval(champ.info)
	roles = ast.literal_eval(champ.roles)
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
	top_10_kda = []
	top_10_wins = []
	for player in player_data:
		if(len(top_10_players) < 10):
			top_10_wins.append(player.wins)
			top_10_kda.append(player.kda)
			top_10_players.append(player.name)
			top_10_id.append(player.accountId)
			top_10_players_rating.append(player.rating)
	print(top_10_id)
	line_chart.x_labels = map(str, top_10_players)
	line_chart.add("Rating", top_10_players_rating)
	line_chart.add("kda", top_10_kda)
	line_chart.add("wins", top_10_wins)
	#line_chart.add("Wirate", champ_wr)
	#line_chart.add("Pickrate", champ_pr)
	#line_chart.add("Banrate", champ_br)
	line_chart = line_chart.render_data_uri()
	#print("Number of champions in db: ", Champions.select().count())
	print("Number of players recorded from 10k matches, ", Summoners.select().count())
	"""
	line_chart.x_labels = map(str, champion)
	line_chart.add("Laning against", champ_wr)
	line_chart.add("Pickrate against", champ_pr)
	line_chart = line_chart.render_data_uri()
	"""
	#return render_template("test.html", data=data, converter=convert_to_dict, get_kda=get_kda, rem_decimals=rem_decimals)
	return render_template("test.html", wr_chart=line_chart)
	
	#return "boo"
