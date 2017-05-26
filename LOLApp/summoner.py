from .APIConstants import *
import urllib, time

class Summoner:
	def __init__(self, Name, Region, api_obj):
		self.riot_api = api_obj
		self.region = Region
		self.account = self.riot_api.get_summoner_by_name(Name.replace(" ", ""))
		print("account: ", self.account)
		self.acc_id = self.account["accountId"]
		self.name = self.account["name"]
		self.summ_id = self.account["id"]
		#self.dd_cdn_ver = "7.2.9"
		#print(self.name)
	
	def account_exists(self):
		return "status" in self.account

	def get_lvl(self):
		return self.account["summonerLevel"]

	def get_profile_icon(self):
		return self.get_icon_url("profileicon", self.account["profileIconId"])

	def get_league_rank(self):
		league_data = self.riot_api.get_league(self.summ_id)
		#print("league data: ", league_data)
		if(len(league_data) < 1):
			return None
		league = {}
		league["tier"] = league_data[0]["tier"]
		league["queue"] = league_data[0]["queue"]
		league["div_name"] = league_data[0]["name"]
		for player in league_data[0]["entries"]:
			if(player["playerOrTeamName"].lower() == self.name.lower()):
				league["player"] = player
				return league


	def get_ranked_match_history(self):
		match_history_raw = self.riot_api.get_matches_all(self.acc_id)
		match_history = []
		print("mhr: ", match_history_raw)
		if("status" not in match_history_raw):
			matches = match_history_raw["matches"]
			for match in matches[:1]:
				match_history.append(self.match_data(match))
			#print(summoner.acc_id)
			#print(self.matches_10[0]["gameId"])
			return match_history
		return "Inactive"

	"""
	def match_data(self, match):
		game = self.riot_api.get_match_data(match["gameId"])
		player_champ = match["champion"]
		game_data = {}
		if(match["queue"] in GAMEMODE):
			game_data["queue"] = GAMEMODE[match["queue"]][0]
		else:
			game_data["queue"] = GAMEMODE[-1]
		#if queue is not rank need to identify player by champ played
		#error when number of matches requested > 10 because of rate limit
		print("game: ", game)
		#print("game participants: ", game["participants"])
		for participant in game["participants"]:
			#print(participant["player"]["summonerName"], " sum name: ", self.name)1
			if(participant["championId"] == player_champ):
				game_data["kills"] =  participant["stats"]["kills"]
				game_data["deaths"] = participant["stats"]["deaths"]
				game_data["assists"] = participant["stats"]["assists"]
				game_data["team_id"] = participant["teamId"]
				game_data["spell1"] = self.get_icon_url("spell", participant["spell1Id"])
				game_data["spell2"] = self.get_icon_url("spell", participant["spell2Id"])
				game_data["champ"] = self.get_icon_url("champion", participant["championId"])
				game_data["trinket"] = self.get_icon_url("item", participant["stats"]["item6"])
				for mastery in participant["masteries"]:
					if(mastery["masteryId"] in KEYSTONE_MASTERIES):
						game_data["keystone"] = self.get_icon_url("mastery", mastery["masteryId"])
			#print(game_data)
		#print(match_history)
		game_data["result"] = game["teams"][(game_data["team_id"]//100) - 1]["win"]
		#game_duration_s = game["gameDuration"]
		res = game["teams"][(game_data["team_id"]//100) - 1]["win"]
		if(res == "Win"):
			game_data["result"] = "victory"
		else:
			game_data["result"] = "defeat"

		if(game["gameDuration"] <= 240):
			game_data["result"] = "remake"
		game_data["duration"] = game["gameDuration"]
		game_date = time.strftime('%m/%d/%Y', time.gmtime(game["gameCreation"]/1000))
		print("date: ", game_date)
		game_data["date"] = game_date
		return game_data
	"""
	def match_data(self, match):
		game = self.riot_api.get_match_data(match["gameId"])
		#if queue is not rank need to identify player by champ played
		#error when number of matches requested > 10 because of rate limit
		#print("game participants: ", game["participants"])
		if(game["queueId"] in GAMEMODE):
			game["queue"] = GAMEMODE[game["queueId"]][0]
		else:
			game["queue"] = GAMEMODE[-1]

		for participant in game["participants"]:
			participant["name"] = game["participantIdentities"][participant["participantId"]-1]["player"]["summonerName"]
			participant["spell1_img"] = self.get_icon_url("spell", participant["spell1Id"])
			participant["spell2_img"] = self.get_icon_url("spell", participant["spell2Id"])
			participant["champ_img"] = self.get_icon_url("champion", participant["championId"])

			for i in range(7):
				item_id = "item"+str(i)
				if(participant["stats"][item_id] != 0):
					participant[item_id+"_img"] = self.get_icon_url("item", participant["stats"][item_id])
				else:
					participant[item_id+"_img"] = "/static/no-item.png"

			for mastery in participant["masteries"]:
				if(mastery["masteryId"] in KEYSTONE_MASTERIES):
					participant["keystone_img"] = self.get_icon_url("mastery", mastery["masteryId"])
			if(participant["name"] == self.name):
				game["place"] = participant["participantId"] - 1
			#print(game_data)
		#print(match_history)
		#game_duration_s = game["gameDuration"]
		print("item url: ", game["participants"][game["place"]]["item4_img"])
		res = game["teams"][(game["participants"][game["place"]]["teamId"]//100) - 1]["win"]
		if(res == "Win"):
			game["result"] = "victory"
		else:
			game["result"] = "defeat"

		if(game["gameDuration"] <= 240):
			game["result"] = "remake"

		game["gameCreation"] = time.strftime('%m/%d/%Y', time.gmtime(game["gameCreation"]/1000))
		print(game)
		return game


	def get_icon_url(self, categ, icon_id):
		#print("icon = ", icon_id)
		time.sleep(.9)
		if(categ == "spell"):
			if(icon_id not in SPELLS):
				name = SPELLS[0]
			else:
				name = SPELLS[icon_id]
		elif(categ == "champion"):
			name = self.riot_api.get_champ_data(icon_id)["image"]["full"]
		else:
			name = str(icon_id) + ".png"

		return URL["static_data_imgs"].format(
				cdn_version="7.9.2",
				category=categ,
				name=name
				)
