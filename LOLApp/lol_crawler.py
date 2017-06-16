import APIConstants, urllib, time, logging, ast
from random import randint
"""
from .championstats import ChampionStats
from .api_calls import APICalls
from .models import *
"""
from championstats import ChampionStats
from api_calls import APICalls
from models import *
#from log import logger
"""need to import all champions data and parse just like with items, to get the name, tags and stufff"""
class LolCrawler:
	def __init__(self, region="NA"):
		self.api_obj = APICalls(region)
		self.region = region
		initialize_db()
		self.items_info = self.get_all_items()
		self.champs_info = self.get_all_champs()
		#self.items_data = self.get_all_items_data()["data"]
		#logging.basicConfig(filename='crawl.log',level=logging.DEBUG)

	def get_champ_stats(self, rank="diamondPlus", num_matches=1000):
		self.error_log = open("crawl_error_log.txt", "w")
		start = time.time()
		try:
			game_q = GamesVisited.delete().where(GamesVisited.match_id != None)
			game_q.execute()
			champ_q = Champions.delete().where(Champions.champ_id != None)
			champ_q.execute()  # remove the rows
		except:
			AttributeError
		#dictionary with key being champion names and value being object containing playrate, winrate, best builds, for each league
		self.player_visited = []
		self.matches_visited_list = []
		self.matches_visited = []
		self.remakes = []
		self.leagues = {"diamondPlus":{"rank_tiers":["DIAMOND", "CHALLENGER", "MASTER"],"champions":{}},
						"bronze":{"rank_tiers":["BRONZE"],"champions":{}},
						"silver":{"rank_tiers":["SILVER"],"champions":{}},
						"gold":{"rank_tiers":["GOLD"],"champions":{}},
						"plat":{"rank_tiers":["PLATINUM"],"champions":{}}
						}
		if(rank == "diamondPlus"):
			data = self.api_obj.get_master_players()
			account_id = self.api_obj.get_summoner_by_summid(data["entries"][0]["playerOrTeamId"])["accountId"]
		elif(rank == "gold"):
			account_id = 47060566
		
		self.crawl_history(account_id, rank, num_matches)

		"""
		data_file = open("champ_data.txt", "w")
		#print(self.leagues[rank]["champions"])
		for champ in self.leagues[rank]["champions"]:
			data_file.write("Data for " + champ + " over " + str(self.leagues[rank]["champions"][champ].plays) + " games. \n")
			data_file.write("Number of Plays: " + str(self.leagues[rank]["champions"][champ].plays) + "- Play rate: " + str(self.leagues[rank]["champions"][champ].plays/self.total_games) + "\n")
			data_file.write("Number of Wins: " + str(self.leagues[rank]["champions"][champ].wins) + "- Win rate: " + str(self.leagues[rank]["champions"][champ].wins/self.leagues[rank]["champions"][champ].plays) + " \n")
			data_file.write("\n")
		data_file.close()
		"""
		visited_for_champ = open("matches_visited.txt", "w")
		visited_for_champ.write("List of games visited: \n")

		for game in self.matches_visited_list:
			visited_for_champ.write("game id: " + str(game) + " \n")
		visited_for_champ.close()

		#print(self.leagues[rank]["champions"])
		#champ_info_list = []
		for champ in self.leagues[rank]["champions"]:
			#print("looking at champ: ", champ)
			self.leagues[rank]["champions"][champ].most_common_roles(self.leagues[rank]["champions"][champ].roles, 2)
			self.leagues[rank]["champions"][champ].get_best_build()
			self.leagues[rank]["champions"][champ].get_most_played_players()
			self.leagues[rank]["champions"][champ].get_skill_order()
			#self.leagues[rank]["champions"][champ].most_common(self.leagues[rank]["champions"][champ].items, 4)
			#print("current champ: ", self.leagues[rank]["champions"][champ].champ_id, " matchups: ", self.leagues[rank]["champions"][champ].matchups)
			#print("players: ", self.leagues[rank]["champions"][champ].players)
			print('champ: ', self.leagues[rank]["champions"][champ].champ_id)
			Champions.create(
				#temp["name"] = self.leagues[rank]["champions"][champ].name
				champId = self.leagues[rank]["champions"][champ].champ_id,
				plays = self.leagues[rank]["champions"][champ].plays,
				wins = self.leagues[rank]["champions"][champ].wins,
				roles = self.leagues[rank]["champions"][champ].roles,
				kda = self.leagues[rank]["champions"][champ].kda,
				laning =  self.leagues[rank]["champions"][champ].laning,
				bans = self.leagues[rank]["champions"][champ].bans,
				players = self.leagues[rank]["champions"][champ].players,
				info = self.leagues[rank]["champions"][champ].info,
				region = self.region,
				rank = rank,
			)
		try:
			with database.atomic():
				for i in range(0, len(self.matches_visited), 100):
					GamesVisited.insert_many(self.matches_visited[i:i+100]).execute()
		except IntegrityError as e:
			raise ValueError("already exists", e)
		self.error_log.close()
		end = time.time()
		#need to figure out why item with an id 0 keeps popping up, neeed to get arrange items
		#also need to figure out why starting and early game items not being added
	
		print("Searching ", len(self.matches_visited_list), " matches took: ", end - start, " seconds.")
		print("Number of remakes: ", len(self.remakes))
		database.close()
		#return champ_info_list, self.matches_visited

	def print_data(self, rank):
		temp = []
		for champ in Champions.select().where(Champions.rank == rank):
			if(champ.champId not in temp):
				temp.append(champ.champId)
			else:
				print("repeated")
			info = ast.literal_eval(champ.info)
			print("Region: ", champ.region, " rank: ", champ.rank)
			print("Champ name: ", info["name"], " bans: ", champ.bans, " plays: ", champ.plays)
			#print(champ.roles)
			"""
			if(len(champ.roles) > 0):
				roles = ast.literal_eval(champ.roles)
				#print(roles)
				for role,stats in roles.items():
					print(role)
					print("spells", stats["spells"])
					print("skill order: ", stats["skill_order"])
					
					for num,skill_slot in stats["skill_order"].items():
						print("Level: ", num, " skills: ", skill_slot)
					
					for stage,items_list in stats["build"].items():
						print(stage)
						for item_id,item in items_list.items():
							#print("item? ", item)
							print("name: ", item["info"]["name"], " uses: ", item["used"], " wins: ", item["wins"])
			else:
				print("Insufficient data.")
			
			#count = 0
			if(len(champ.players) > 0):
				players = ast.literal_eval(champ.players)
				for player,stats in players.items():
					print("player: ", player, " stats: ", stats)
			"""
			#print("Number of players who played this champ 2 or less times: ", count)
			#print("Playrate: ", champ.plays/1000, " Winrate: ", champ.wins/champ.plays, "\n")
			#print("Players: ", champ.players)
			
		print("Number of champions in db: ", Champions.select().where(Champions.rank == rank).count())

	def crawl_history(self, acc_id, desired_rank, num_matches, name=None, season = 8):
		print("name: ", name, " account id: ", acc_id)
		cur_count = len(self.matches_visited_list)
		if(cur_count < num_matches):
			self.player_visited.append(acc_id)
			match_history = self.get_history(acc_id, season, 420)
			for match in match_history["matches"]:
				cur_count = len(self.matches_visited_list)
				print(cur_count, "/", num_matches)
				#print("current champ list", self.leagues[rank]["champions"])
				#print(self.matches_visited)
				if(cur_count < num_matches):
					game_id = match["gameId"]
					if(game_id not in self.matches_visited_list):
						print("game id :", match["gameId"])
						match_details = self.get_match_details(match)
						#1496197986 represents latest paatch date
						if(match_details["gameCreation"] > 1496197986):
							if(match_details["gameDuration"] < 300):
								self.remakes.append(game_id)
							else:
								self.add_banned_champs(match_details, desired_rank)
								match_timeline = self.api_obj.get_match_timeline(game_id)
								self.blue_total_dmg = self.blue_total_gold = self.blue_total_kills = 0
								self.red_total_dmg = self.red_total_gold = self.red_total_kills = 0
								for i in range(10):
									if(i < 5):
										self.blue_total_dmg += match_details["participants"][i]["stats"]["totalDamageDealtToChampions"]
										self.blue_total_gold += match_details["participants"][i]["stats"]["goldEarned"]
										self.blue_total_kills += match_details["participants"][i]["stats"]["kills"]
									else:
										self.red_total_dmg += match_details["participants"][i]["stats"]["totalDamageDealtToChampions"]
										self.red_total_gold += match_details["participants"][i]["stats"]["goldEarned"]			
										self.red_total_kills += match_details["participants"][i]["stats"]["kills"]
								#try:
								#find matching pairs and compare so only need to loop 5 times instead of 10
								for i in range(0, 5):
									blue_player = match_details["participants"][i]
									timeline = match_timeline["frames"]
									#print("cham data: ", self.api_obj.get_champ_data(participant["championId"]))
									#champ = self.api_obj.get_champ_data(participant["championId"])["name"]
									self.add_champ(blue_player["championId"], desired_rank)
									role = self.get_role(blue_player, game_id)
									for j in range(5, 10):
										#print(role, " vs ", self.get_role(match_details["participants"][j]))
										if(self.get_role(match_details["participants"][j], game_id) == role):
											red_player = match_details["participants"][j]
											break
									self.add_champ(red_player["championId"], desired_rank)
									self.add_champs_data(match_details, {"blue":blue_player,"red":red_player}, desired_rank, role, timeline)
									#print("build for: ", champ_name, " - ", self.leagues[rank]["champions"][champ_name].get_items())	
							self.matches_visited.append({"match_id":game_id})
							self.matches_visited_list.append(game_id)
				else:
					break
			if(cur_count < num_matches):
				for player in match_details["participantIdentities"]:
					acc_id = player["player"]["currentAccountId"]
					rank = self.check_rank(player["player"]["summonerId"])
					if(acc_id not in self.player_visited and rank in self.leagues[desired_rank]["rank_tiers"]):
						self.crawl_history(acc_id, desired_rank, num_matches, player["player"]["summonerName"], season)

	def add_champ(self, champ, rank):
		#print("champ: ", champ)
		if(champ not in self.leagues[rank]["champions"]):
			new_champ = ChampionStats(champ, self.champs_info[champ])
			self.leagues[rank]["champions"][champ] = new_champ

	def add_champs_data(self, match_details, players, rank, role=None, match_timeline=[]):
		#print("players len: ", len(players))
		laning = self.analyze_matchup(match_timeline, players["blue"], players["red"], role, rank)
		for team,player in players.items():
			if(team == "red"):
				laning = -laning
			champ_id = player["championId"]
			par_id = player["participantId"]
			acc_id = match_details["participantIdentities"][par_id-1]["player"]["currentAccountId"]
			print(acc_id)
			win = 1 if player["stats"]["win"] else 0
			self.leagues[rank]["champions"][champ_id].add_player(
				acc_id, 
				win, 
				self.get_kda(player),
				self.get_player_performance(match_timeline, player, role, team) + (laning*.3)
				)
			self.leagues[rank]["champions"][champ_id].plays += 1
			self.add_champ_stats(champ_id, player, win, role, self.get_kda(player), rank)
			self.add_build(role, match_timeline, player, win, laning, rank)
			self.leagues[rank]["champions"][champ_id].add_skill_order(role, match_timeline, par_id, win)
			self.leagues[rank]["champions"][champ_id].add_spells(role, [player["spell1Id"], player["spell2Id"]], win)

	def add_banned_champs(self, match, rank):
		banned_champs = []
		for team in match["teams"]:
			for ban in team["bans"]:
				champ_id = ban["championId"]
				if(champ_id not in banned_champs):
					if(champ_id in self.champs_info):
						if(champ_id not in self.leagues[rank]["champions"]):
							self.leagues[rank]["champions"][champ_id] = ChampionStats(champ_id, self.champs_info[champ_id])			
						self.leagues[rank]["champions"][champ_id].bans += 1
						banned_champs.append(champ_id)

	def get_role(self, player_data, match_id):
		print("match_id ", match_id)
		role = None
		if(player_data["spell2Id"] == 11 or player_data["spell1Id"] == 11):
			for item,val in player_data["stats"].items():
				#print(val)
				if("item" in item and str(val) in APIConstants.JUNGLE_CORE):
					role = "JUNGLE"
					break
		if(role is None):
			role = player_data["timeline"]["lane"]

		if(player_data["timeline"]["lane"] == "BOTTOM"):
			if("CARRY" in player_data["timeline"]["role"]):
				role = "BOT_CARRY"
			elif("SUPPORT" in player_data["timeline"]["role"]):
				role = "BOT_SUPPORT"
			else:
				tags = self.get_champ_tags(player_data["championId"])
				#print("tags: ", tags)
				if(player_data["spell2Id"] == 7 or player_data["spell1Id"] == 7 or "Marksman" in tags):
					role = "BOT_CARRY"
					try:
						if(player_data["timeline"]["creepsPerMinDeltas"]["0-10"] < 3):
							role = "BOT_SUPPORT"
					except:
						KeyError
				else:
					role = "BOT_SUPPORT"
					try:
						if(player_data["timeline"]["creepsPerMinDeltas"]["0-10"] >= 3):
							role = "BOT_CARRY"
					except:
						KeyError
		return role

	def get_kda(self, player):
		return {"kills": player["stats"]["kills"],
				"deaths": player["stats"]["deaths"],
				"assists": player["stats"]["assists"]}

	def check_rank(self, summ_id):
		rank = None
		try:
			rank = self.api_obj.get_league(summ_id)[0]["tier"]
		except:
			IndexError, KeyError
			self.error_log.write("fn: check_rank | input: " + str(summ_id) + "\n")
		return rank

	def get_player_performance(self, timeline, player, role, team):
		teams = {"blue": [self.blue_total_dmg, self.blue_total_gold, self.blue_total_kills], 
				"red":[self.blue_total_dmg, self.blue_total_gold, self.red_total_kills]}
		score = 0
		deaths = player["stats"]["deaths"]
		if(deaths == 0):
			deaths = 1
		kills_assists = player["stats"]["kills"] + player["stats"]["assists"]
		kda = kills_assists/deaths  
		if(kda >= 7):
			score += 3
		elif(kda >= 4):
			score += 2
		elif(kda >= 1.5):
			score += 1
		else:
			score -= 1
		if(teams[team][2] > 0 and kills_assists/teams[team][2] >= .5):
			score += 1
		elif(teams[team][2] > 0 and kills_assists/teams[team][2] >= .8):
			score += 2
		if(role == "BOT_SUPPORT"):
			score += 1 if player["stats"]["totalDamageDealtToChampions"]/teams[team][0] >= .1 else 0
			score += 1 if player["stats"]["goldEarned"]/teams[team][1] >= .1 else 0
		elif(role == "BOT_CARRY" or "MIDDLE"):
			score += 1 if player["stats"]["totalDamageDealtToChampions"]/teams[team][0] >= .25 else 0
			score += 1 if player["stats"]["goldEarned"]/teams[team][1]  >= .25 else 0
		else:
			score += 1 if player["stats"]["totalDamageDealtToChampions"]/teams[team][0] >= .2 else 0
			score += 1 if player["stats"]["goldEarned"]/teams[team][1]  >= .2 else 0
		score += (player["stats"]["objectivePlayerScore"]*.3) + (player["stats"]["visionScore"]*.2)
		print("score: ", score)
		return round(score,2)

	def add_build(self, role, timeline, player_details, win, laning, rank):
		champ_id = player_details["championId"]
		par_id = player_details["participantId"]
		#print("laning: ", laning)
		champ = self.leagues[rank]["champions"][champ_id]
		for frame in timeline[1:15]:
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] == par_id and event["type"] == "ITEM_PURCHASED"):
					#print("item: ", self.items_data[str(event["itemId"])])
					item = str(event["itemId"])
					#print("item id: ", item, "starting items: ", self.items["start"])
					if(event["timestamp"] < 20000 and item in self.items_info["start"]):
						champ.add_item(item, self.items_info["start"][item], win, role, "start")
					else:
						if(laning >= 0):
							status = "early_ahead"
						else:
							status = "early_behind"
						#print("status: ", status, " item: ", self.items_raw_data[item]["name"])
						if(self.check_item(champ, item, role, status)):
							champ.add_item(item, self.items_info["complete"][item], win, role, status)
		champ.add_core(player_details["stats"], role, win, self.items_info)

	def check_item(self, champ, item_id, role, stage):
		build = champ.roles[role]["build"]
		if(stage == "core"):
			if(item_id not in build["start"] and item_id not in build["early_ahead"] and item_id not in build["early_behind"]):
				return item_id in self.items_info["complete"]
			return False
		elif(stage == "start"):
			return item_id in  self.items_info["start"]
		elif(stage == "early_ahead" or stage == "early_behind"):
			if(item_id not in build["start"]):
				return item_id in self.items_info["complete"]
			return False

	def add_champ_stats(self, champ_id, player, win, role, kda, rank):
		self.leagues[rank]["champions"][champ_id].add_kda(kda)
		self.leagues[rank]["champions"][champ_id].wins += win
		self.leagues[rank]["champions"][champ_id].add_role(role, win, kda, player["stats"]["totalDamageDealtToChampions"], player["stats"]["totalDamageTaken"])

	def analyze_matchup(self, timeline, blue_player, red_player, role, rank):
		blue_champ = blue_player["championId"]
		red_champ = red_player["championId"]
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		if(blue_player["participantId"] > red_player["participantId"] - 5):
			blue_lane_points = 2
		else:
			blue_lane_points = -2
		if(role != "JUNGLE"):
			if("csDiffPerMinDeltas" in blue_player["timeline"]):
				for time in blue_player["timeline"]["csDiffPerMinDeltas"]:
					if("30" not in time):
						blue_lane_points += blue_player["timeline"]["csDiffPerMinDeltas"][time] * .2
		else:
			blue_lane_points += (blue_player["stats"]["neutralMinionsKilledEnemyJungle"]-red_player["stats"]["neutralMinionsKilledEnemyJungle"]*.35)
			blue_lane_points += (blue_player["stats"]["neutralMinionsKilledTeamJungle"]-red_player["stats"]["neutralMinionsKilledTeamJungle"]*.35)
		if("xpDiffPerMinDeltas" in blue_player["timeline"]):
			for time in blue_player["timeline"]["xpDiffPerMinDeltas"]:
				if("30" not in time):
					blue_lane_points += blue_player["timeline"]["xpDiffPerMinDeltas"][time] * .1
		for frame in timeline[1:10]:
			if(frame["timestamp"] <= 900000):
				for event in frame["events"]:
					if(event["type"] == "CHAMPION_KILL"):
						if(event["killerId"] == blue_player["participantId"] and event["victimId"] == red_player):
							blue_lane_points += 2
		#print(blue_champ, " vs ", red_champ)
		#print("blue lane points: ", blue_lane_points)
		if(blue_lane_points >= 4):
			blue_lane_win = 1
		elif(blue_lane_points >= 10):
			blue_lane_win = 2
		else:
			blue_lane_win = 0
		self.leagues[rank]["champions"][blue_champ].add_matchup(role, red_champ, blue_lane_win)
		self.leagues[rank]["champions"][red_champ].add_matchup(role, blue_champ, -blue_lane_win)
		return blue_lane_win

	def get_all_items(self):
		items_raw_data = self.api_obj.get_all_items_data()["data"]
		temp = {"complete":{}, "trinket":{}, "start":{}}
		for item,val in items_raw_data.items():
			print("Value: ", val)
			if("maps" in val and val["maps"]["11"] and "name" in val and val["gold"]["purchasable"]):
				if(val["gold"]["total"] <= 500):
					temp["start"][item] = {"name":val["name"], "cost":val["gold"]["total"]}
				elif("tags" in val and "Trinket" in val["tags"]):
					temp["trinket"][item] = {"name":val["name"], "cost":val["gold"]["total"]}
				elif("into" not in val and ("tags" not in val or "Consumable" not in val["tags"])):
					temp["complete"][item] = {"name":val["name"], "cost":val["gold"]["total"]}
		print(temp)
		return temp

	def get_all_champs(self):
		champs_data = self.api_obj.get_all_champs_data()["data"]
		temp = {}
		for champ_key,champ in champs_data.items():
			temp[champ["id"]] = {"name":champ["name"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"enemy_tips":champ["enemytips"], "ally_tips":champ["allytips"],
								}
		return temp

	def get_history(self, acc_id, season = 8, queues=[]):
		return self.api_obj.get_matches_all(acc_id, season, queues)

	def get_match_details(self, match):
		#print("game id: ", match)
		return self.api_obj.get_match_data(match["gameId"])

	def get_champ_tags(self, champ_id):
		return self.api_obj.get_champ_data(champ_id)["tags"]

if __name__ == "__main__":
	crawler = LolCrawler()
	crawler.get_champ_stats("gold", 2200)
	crawler.get_champ_stats("diamondPlus", 2200)
