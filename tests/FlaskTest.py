from flask import Flask, render_template, redirect, url_for, request
from match_history import MatchHistory
import regex

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/hello')
def hello():
    return 'Hello, Flask'

@app.route('/test/<int:num>')
def test(num):
	return "You are %i" % num

@app.route('/user', methods=["POST"])
def get_data():
	validate = regex.compile('^[a-zA-Z_0-9\\p{L} _\\.]+$')
	name = request.form["name"]
	name_l = len(name)
	region = request.form["region"]
	if(name_l >= 3 and name_l <= 16 and validate.match(name) is not None):
		print(name)
		matches = MatchHistory(region, name)
		#print(matches.match_data())
		champ_icon = matches.get_champ_icon()
		print(champ_icon)
		return render_template("user.html", name=name, region=region, matches=matches.get_recent(), icon=champ_icon) 	
	return render_template("user.html")

if __name__ == "__main__":
	app.run(debug=True)#remove before publishsing
	#debug gives useuful info of what went wrong if server crashes, also autoupdates app without needing to rerun the file