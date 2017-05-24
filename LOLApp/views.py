from LOLApp import app, api, cache
from flask import render_template, redirect, url_for, escape, request, session, flash
import regex
from .summoner import Summoner

app.secret_key = "change this to something super secret"

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
	#cache = MemcachedCache(['127.0.0.1:11211'])
	global api
	validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	if((len(name) >= 3 and len(name) <= 16) and validate.match(name) is not None):
		if(region != "NA"):
			api = APICalls(region)
		#print("API: " , api)
		name_l = len(name)
		summoner_data = Summoner(name, region, api)
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
			#print(match_history)
			return render_template("user.html")
			"""
			return render_template("user.html", 
				name=name, lvl=summoner_data.get_lvl(), 
				region=region, profile_icon=p_icon, 
				matches=match_history, league=league_data)
			"""
		return render_template("user.html")
	else:
		error = "Invalid Summoner name"
		flash("Please enter a valid summoner name")
		return render_template("index.html")

@app.route('/<region>/summoner/')
def re_route(region):
	error = "Invalid Summoner name"
	flash("Please enter a valid summoner name")
	return render_template("index.html")

@app.route('/react')
def react_test():
	return render_template("react.html")