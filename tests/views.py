from flask import Flask, render_template, redirect, url_for, escape, request, session, flash
#from match_history import MatchHistory
import regex
from summoner import Summoner
from api_calls import APICalls

app = Flask(__name__)
app.secret_key = "change this to something super secret"
api = APICalls()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/', methods=["GET", "POST"])
def get_data():
	if request.method == "POST":
		name = request.form["name"]
		validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
		if(name != "" and (len(name) >= 3 and len(name) <= 16) and validate.match(name) is not None):
			print("name = ", name)
			session["region"] = request.form["region"]
			session["name"] = name
			return redirect(url_for('get_summoner', name=name, region=escape(session["region"])))
		else:
			error = "Invalid Summoner name"
			flash("Please enter a valid summoner name")
			return render_template("index.html")

@app.route('/<region>/summoner/<name>')
def get_summoner(name, region):
	global api
	name = escape(session["name"])
	region = escape(session["region"])
	if(region != "NA"):
		api = APICalls(region)
	#print("API: " , api)
	name_l = len(name)
	summoner_data = Summoner(name, region, api)
	if(summoner_data.account_exists):
		match_history = summoner_data.get_match_history()
		p_icon = summoner_data.get_profile_icon()
		#print(match_history)
		if(match_history is None):
			return render_template("user.html", 
				name=name, 
				lvl=summoner_data.get_lvl(), 
				region=region, 
				profile_icon=p_icon)
		#print(match_history)
		league_data = summoner_data.get_league_rank()
		return render_template("user.html", 
			name=name, lvl=summoner_data.get_lvl(), 
			region=region, profile_icon=p_icon, 
			matches=match_history, league=league_data)
		"""
		match_history = MatchHistory(region, name, api)

		matches = match_history.get_matches(30)
		if(matches is None):
			return render_template("user.html")
		elif(matches == "Empty"):
			return render_template("user.html", name=name, lvl=match_history.lvl, region=region, profile_icon=match_history.get_summoner_icon())
		else:
			#print(matches.match_data())
			champ_icon = match_history.get_champ_icon()
			#print(champ_icon)
			return render_template("user.html", name=name, lvl=match_history.lvl, region=region, matches=matches, icon=champ_icon, profile_icon=match_history.get_summoner_icon()) 	
		"""
	return render_template("user.html")


if __name__ == "__main__":
	app.run(debug=True)#remove before publishsing
	#debug gives useuful info of what went wrong if server crashes, also autoupdates app without needing to rerun the file