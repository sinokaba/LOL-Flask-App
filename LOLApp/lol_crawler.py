import APIConstants, urllib, time, logging, ast
from random import randint
from championstats import ChampionStats
from playersStats import PlayerStats
from api_calls import APICalls
from models import *
"""need to import all champions data and parse just like with items, to get the name, tags and stufff"""
class LolCrawler:
	def __init__(self, region="NA"):
		self.api_obj = APICalls(region)
		self.region = region
		initialize_db()
		self.items_info = self.get_items_data()
		self.champs_info = self.get_champs_data()
		self.keystones_info = self.get_keystones_data()
		self.spells_info = self.get_summ_spells_data()
		self.runes_info = self.get_runes_data()
		self.error_log = open("crawl_error_log.txt", "w")
		#self.items_data = self.get_all_items_data()["data"]
		#logging.basicConfig(filename='crawl.log',level=logging.DEBUG)

	def get_champ_stats(self, desired_rank="diamondPlus", num_matches=1000, reset=True):
		start = time.time()
		self.coords = {"TOP":{"x":range(500,4600),"y":range(9500,14500)},"MIDDLE":{"x":range(5000,9000),"y":range(6000,9500)},
						"BOT":{"x":range(10000,14400),"y":range(600,4500)}, "JUNGLE":{"x":range(-120,14870),"y":range(-120,14980)}}
		if(reset):
			self.clear_db()
		#dictionary with key being champion names and value being object containing playrate, winrate, best builds, for each league
		self.players_visited = {}
		self.matches_visited_list = []
		self.mh_visited = []
		self.matches_visited = []
		self.remakes = []
		self.leagues = {"diamondPlus":{"rank_tiers":["DIAMOND", "CHALLENGER", "MASTER"],"champions":{}},
						"bronze":{"rank_tiers":["BRONZE"],"champions":{}},
						"silver":{"rank_tiers":["SILVER"],"champions":{}},
						"gold":{"rank_tiers":["GOLD"],"champions":{}},
						"plat":{"rank_tiers":["PLATINUM"],"champions":{}}
						}
		if(desired_rank == "diamondPlus"):
			data = self.api_obj.get_master_players()
			account_id = self.api_obj.get_summoner_by_summid(data["entries"][0]["playerOrTeamId"])["accountId"]
			rank = "MASTER"
		elif(desired_rank == "gold"):
			account_id = 47060566
			rank = desired_rank.upper()		
		self.crawl_history(account_id, rank, desired_rank, num_matches, "AllIDoisFeed")

		self.add_champs_db(desired_rank)
		self.add_gamed_visited_db()
		self.add_players_db()
		end = time.time()
		#need to figure out why item with an id 0 keeps popping up, neeed to get arrange items
		#also need to figure out why starting and early game items not being added
		self.error_log.close()
		print("Searching ", len(self.matches_visited_list), " matches took: ", end - start, " seconds.")
		print("Number of remakes: ", len(self.remakes))
		database.close()
		#return champ_info_list, self.matches_visited

	def clear_db(self):
		GamesVisited.delete().where(GamesVisited.matchId != None).execute()
		Champions.delete().where(Champions.champId != None).execute()  # remove the rows
		Summoners.delete().where(Summoners.accountId != None).execute()

	def add_players_db(self):
		for player,data in self.players_visited.items():
			kda_dict = data.stats["kda"]
			if(kda_dict["deaths"] == 0):
				kda = 99.0
			else:
				kda = kda_dict["kills"]+kda_dict["assists"]/kda_dict["deaths"]
			Summoners.create(
				accountId = data.info["accountId"],
				name = data.info["name"],
				region = data.info["region"],
				currentRank = data.info["currentRank"],
				champions = data.champs,
				kda = kda,
				rating = data.rating/(data.wins+data.loses),
				stats = data.stats,
				wins = data.wins,
				loses = data.loses,
				behavior = data.behavior
			)

	def add_champs_db(self, desired_rank):
		champs = self.leagues[desired_rank]["champions"]
		for champ in champs:
			#print("looking at champ: ", champ)
			champs[champ].most_common_roles(champs[champ].roles, 2)
			champs[champ].get_best_build()
			champs[champ].get_most_played_players()
			champs[champ].get_skill_order()
			champs[champ].filter_runes()
			#self.leagues[rank]["champions"][champ].most_common(self.leagues[rank]["champions"][champ].items, 4)
			#print("current champ: ", self.leagues[rank]["champions"][champ].champ_id, " matchups: ", self.leagues[rank]["champions"][champ].matchups)
			#print("players: ", self.leagues[rank]["champions"][champ].players)
			print('champ: ', champs[champ].champ_id)
			Champions.create(
				#temp["name"] = self.leagues[rank]["champions"][champ].name
				champId = champs[champ].champ_id,
				plays = champs[champ].plays,
				wins = champs[champ].wins,
				roles = champs[champ].roles,
				kda = champs[champ].kda,
				laning =  champs[champ].laning,
				bans = champs[champ].bans,
				players = champs[champ].players,
				info = champs[champ].info,
				region = self.region,
				rank = desired_rank,
			)

	def add_gamed_visited_db(self):
		visited_for_champ = open("matches_visited.txt", "w")
		visited_for_champ.write("List of games visited: \n")
		for game in self.matches_visited_list:
			visited_for_champ.write("game id: " + str(game) + " \n")
		visited_for_champ.close()
		try:
			with database.atomic():
				for i in range(0, len(self.matches_visited), 100):
					GamesVisited.insert_many(self.matches_visited[i:i+100]).execute()
		except IntegrityError as e:
			raise ValueError("already exists", e)

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
		
			if(len(champ.roles) > 0):
				roles = ast.literal_eval(champ.roles)
				#print(roles)
				for role,stats in roles.items():
					print(role)
					print("keystone", stats["keystone"])
					#print("skill order: ", stats["skill_order"])
					print("runes", stats["runes"])
					"""
					for num,skill_slot in stats["skill_order"].items():
						print("Level: ", num, " skills: ", skill_slot)
					"""
					for stage,items_list in stats["build"].items():
						print(stage)
						for item_id,item in items_list.items():
							if(stage == "late"):
								print("situation: ", item_id)
								for situation,item in item.items():
									print("name: ", item["info"]["name"], " rating: ", item["rating"])
							else:
							#print("item? ", item)
								print("name: ", item["info"]["name"], " uses: ", item["used"], " rating: ", item["rating"])
			else:
				print("Insufficient data.")
			"""
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
		"""
		for player in Summoners.select():
			print(player.name, " - ", player.currentRank, " region: ", player.region)
			print("rating ", player.rating)
			print("Champ pool: ", player.champions)
		print("Number of players: ", Summoners.select().count())
		"""

	def crawl_history(self, acc_id, curr_rank, desired_rank, num_matches, name=None, season = 8):
		print("name: ", name, " account id: ", acc_id)
		cur_count = len(self.matches_visited_list)
		self.mh_visited.append(acc_id)
		if(cur_count < num_matches):
			match_history = self.get_history(acc_id, season, 420)
			for match in match_history["matches"]:
				cur_count = len(self.matches_visited_list)
				print(cur_count, "/", num_matches)
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
								par = match_details["participants"]
								self.get_team_stats(par)
								for i in range(0, 5):
									blue_player = par[i]
									timeline = match_timeline["frames"]
									self.add_champ(blue_player["championId"], desired_rank)
									role = self.get_role(blue_player, game_id)
									for j in range(5, 10):
										#print(role, " vs ", self.get_role(match_details["participants"][j]))
										if(self.get_role(par[j], game_id) == role):
											red_player = par[j]
											break
									self.add_champ(red_player["championId"], desired_rank)
									self.add_champs_data(match_details, {"blue":blue_player,"red":red_player}, curr_rank, desired_rank, role, timeline)
									#print("build for: ", champ_name, " - ", self.leagues[rank]["champions"][champ_name].get_items())	
							self.matches_visited.append({"matchId":game_id})
							self.matches_visited_list.append(game_id)
				else:
					break
			if(cur_count < num_matches):
				for player in match_details["participantIdentities"]:
					acc_id = player["player"]["currentAccountId"]
					if(acc_id not in self.players_visited):
						rank = self.get_rank(player["player"]["summonerId"])
					else:
						rank = self.players_visited[acc_id].info["currentRank"]
					if(acc_id not in self.mh_visited and rank in self.leagues[desired_rank]["rank_tiers"]):
						self.crawl_history(acc_id, rank, desired_rank, num_matches, player["player"]["summonerName"], season)
	
	def get_rank(self, summ_id):
		rank = None
		try:
			rank = self.api_obj.get_league(summ_id)[0]["tier"]
		except:
			IndexError, KeyError
			self.error_log.write("fn: check_rank | input: " + str(summ_id) + "\n")
		return rank

	def add_player(self, player, acc_id, name, rank):
		if(acc_id not in self.players_visited):
			new_player = PlayerStats(acc_id, name, self.region, rank)
			self.players_visited[acc_id] = new_player

	def add_champ(self, champ, desired_rank):
		#print("champ: ", champ)
		if(champ not in self.leagues[desired_rank]["champions"]):
			new_champ = ChampionStats(champ, self.champs_info[champ])
			self.leagues[desired_rank]["champions"][champ] = new_champ

	#perhaps split this section, because "add_champs_data" does not fully describe what it does
	def add_champs_data(self, match_details, players, curr_rank, desired_rank, role=None, match_timeline=[]):
		#print("players len: ", len(players))
		print("des rank", desired_rank)
		laning_perf = self.analyze_matchup(match_timeline, players["blue"], players["red"], role, desired_rank)
		print("laning: ", laning_perf)
		for team,player in players.items():
			if(team == "red"):
				laning_perf = -laning_perf
			champ_id = player["championId"]
			par_id = player["participantId"]
			player_data = match_details["participantIdentities"][par_id-1]["player"]
			acc_id = player_data["currentAccountId"]
			#print(acc_id)
			win = 1 if player["stats"]["win"] else 0
			player_perf = self.get_player_performance(match_timeline, player, role, team)
			#print("performance: ", player_perf)
			rating = round(player_perf + laning_perf, 2)
			print("rating: ", rating)

			self.leagues[desired_rank]["champions"][champ_id].add_player(acc_id, win, self.get_kda(player), rating)
			self.add_player(player_data, acc_id, player_data["summonerName"], curr_rank)
			self.add_players_data(player, acc_id, win, rating)
			self.players_visited[acc_id].add_champ(champ_id, win, player_perf)

			champ_obj = self.leagues[desired_rank]["champions"][champ_id]
			champ_obj.plays += 1
			self.add_champ_stats(champ_obj, player, win, role, self.get_kda(player))
			self.add_build(role, match_timeline, player, desired_rank, laning_perf, rating)
			self.add_keystone(champ_obj, player, role, win, laning_perf)
			self.add_spells(champ_obj, player, role, win, laning_perf)
			self.add_runes(champ_obj, player, role, win, laning_perf)
			self.leagues[desired_rank]["champions"][champ_id].add_skill_order(role, match_timeline, par_id, win)

	def add_players_data(self, player, acc_id, win, rating):
		cur_player = self.players_visited[acc_id]
		cur_player.add_kda(self.get_kda(player))
		cur_player.add_rating(rating)
		cur_player.add_stat("objectiveScore", self.get_obj_sc(player))
		cur_player.add_stat("visionScore", self.get_vis_sc(player))
		cur_player.add_gold(player["stats"]["goldEarned"])
		cur_player.add_damage_dealt(player["stats"]["totalDamageDealtToChampions"])
		if(win == 1):
			self.players_visited[acc_id].wins += 1
		else:
			self.players_visited[acc_id].loses += 1

	#connect this with player perofrmance
	def get_obj_sc(self, player):
		points = 0
		try:
			stats = player["stats"]
			if(stats["firstTowerAssist"]):
				points += 1
			elif(stats["firstTowerKill"]):
				points += 1.5
			if(stats["firstInhibitorAssist"]):
				points += 1
			elif(stats["firstInhibitorKill"]):
				points += 1.5
			points += stats["inhibitorKills"]
			points += stats["damageDealtToObjectives"]**.15
		except:
			KeyError
		return points

	def get_vis_sc(self, player):
		#note riot's vision score is just (wards placed*2)+(wards killed)+(vision ward bought)
		points = 0
		try:
			points = player["stats"]["visionScore"]*.15
		except:
			KeyError
		return points

	def add_banned_champs(self, match, desired_rank):
		banned_champs = []
		for team in match["teams"]:
			for ban in team["bans"]:
				champ_id = ban["championId"]
				if(champ_id not in banned_champs):
					if(champ_id in self.champs_info):
						if(champ_id not in self.leagues[desired_rank]["champions"]):
							self.leagues[desired_rank]["champions"][champ_id] = ChampionStats(champ_id, self.champs_info[champ_id])			
						self.leagues[desired_rank]["champions"][champ_id].bans += 1
						banned_champs.append(champ_id)

	def get_role(self, player_data, match_id):
		#print("match_id ", match_id)
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

	def get_team_stats(self, participants):
		self.blue_total_dmg = self.blue_total_gold = self.blue_total_kills = 0
		self.red_total_dmg = self.red_total_gold = self.red_total_kills = 0
		for i in range(10):
			if(i < 5):
				self.blue_total_dmg += participants[i]["stats"]["totalDamageDealtToChampions"]
				self.blue_total_gold += participants[i]["stats"]["goldEarned"]
				self.blue_total_kills += participants[i]["stats"]["kills"]
			else:
				self.red_total_dmg += participants[i]["stats"]["totalDamageDealtToChampions"]
				self.red_total_gold += participants[i]["stats"]["goldEarned"]			
				self.red_total_kills += participants[i]["stats"]["kills"]

	def get_kda(self, player):
		return {"kills": player["stats"]["kills"],
				"deaths": player["stats"]["deaths"],
				"assists": player["stats"]["assists"]}

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
		score += self.get_team_contribution(player, kills_assists, role, teams[team][0], teams[team][1], teams[team][2])
		score += (self.get_obj_sc(player)*.3) + (self.get_vis_sc(player)*.2)
		#print("score: ", score)
		return round(score*.3,2)

	def get_team_contribution(self, player, ka, role, team_dmg, team_gold, team_kills):
		score = 0
		if(role == "BOT_SUPPORT"):
			exp_share = .1 
		elif(role == "BOT_CARRY" or "MIDDLE"):
			exp_share = .25
		else:
			exp_share = .2
		if(team_kills > 0):
			if(ka/team_kills >= .5):
				score += 1
			elif(ka/team_kills >= .8):
				score += 2
		score += 1 if player["stats"]["totalDamageDealtToChampions"]/team_dmg >= exp_share else 0
		score += 1 if player["stats"]["goldEarned"]/team_gold  >= exp_share else 0
		return score

	def add_keystone(self, champ, player_details, role, win, perf):
		try:
			masteries = player_details["masteries"]
			if(masteries[5]["masteryId"] in self.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", self.keystones_info[masteries[5]["masteryId"]])
			elif(masteries[len(masteries)-1]["masteryId"] in self.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", self.keystones_info[masteries[len(masteries)-1]["masteryId"]])			
		except:
			KeyError

	def add_spells(self, champ, player_details, role, win, perf):
		if(player_details["spell1Id"] in self.spells_info and player_details["spell2Id"] in self.spells_info):
			champ.add_attribute(role, win, perf, "spells", self.spells_info[player_details["spell1Id"]])
			champ.add_attribute(role, win, perf, "spells", self.spells_info[player_details["spell2Id"]])

	def add_runes(self, champ, player_details, role, win, perf):
		try:
			runes = player_details["runes"]
			"""
			temp = {"reds":0, "yellows":0, "blues":0, "blacks":0}
			length = len(runes)
			index = 0
			if(length >= 4):
				while(index < length):
					temp[]
					champ.add_attribute(role, win, perf, "runes", self.runes_info[runes[index]["runeId"], "red")
			"""
			rune_types = {0:"red", 1:"blue", 2:"yellow", 3:"black"}
			index = 0
			if(len(runes) == 4):
				for rune in runes:
					if(rune["runeId"] in self.runes_info):
						champ.add_attribute(role, win, perf, "runes", self.runes_info[rune["runeId"]], rune_types[index])
					index += 1
		except:
			KeyError

	def add_build(self, role, timeline, player_details, desired_rank, laning, performance):
		champ_id = player_details["championId"]
		par_id = player_details["participantId"]
		#print("laning: ", laning)
		champ = self.leagues[desired_rank]["champions"][champ_id]
		for frame in timeline[1:15]:
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] == par_id and event["type"] == "ITEM_PURCHASED"):
					#print("item: ", self.items_data[str(event["itemId"])])
					item = event["itemId"]
					#print("item id: ", item, "starting items: ", self.items["start"])
					if(event["timestamp"] < 20000 and item in self.items_info["start"]):
						champ.add_item(item, self.items_info["start"][item], role, "start", performance)
					else:
						if(laning >= 0):
							status = "early_ahead"
						else:
							status = "early_behind"
						#print("status: ", status, " item: ", self.items_raw_data[item]["name"])
						if(self.check_item(champ, item, role, status)):
							champ.add_item(item, self.items_info["complete"][item], role, status, performance)
		champ.add_late(player_details["stats"], role, performance, self.items_info)

	def check_item(self, champ, item_id, role, stage):
		build = champ.roles[role]["build"]
		if(stage == "late"):
			if(item_id not in build["start"] and item_id not in build["early_ahead"] and item_id not in build["early_behind"]):
				return item_id in self.items_info["complete"]
			return False
		elif(stage == "start"):
			return item_id in  self.items_info["start"]
		elif(stage == "early_ahead" or stage == "early_behind"):
			if(item_id not in build["start"]):
				return item_id in self.items_info["complete"]
			return False

	def add_champ_stats(self, champ, player, win, role, kda):
		champ.add_kda(kda)
		champ.wins += win
		champ.add_role(role, win, kda, player["stats"]["totalDamageDealtToChampions"], player["stats"]["totalDamageTaken"])

	def analyze_matchup(self, timeline, blue_player, red_player, role, desired_rank):
		print("des rank: ", desired_rank)
		blue_champ = blue_player["championId"]
		red_champ = red_player["championId"]
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		if(blue_player["participantId"] > red_player["participantId"] - 5):
			blue_points = 2
		else:
			blue_points = -2
		win = 1 if blue_player["stats"]["win"] else -1
		blue_points += win 
		blue_points += self.tally_cs_gold_lead(role, blue_player, red_player) 
		blue_points += self.tally_kp_and_op(timeline, blue_player["participantId"], red_player["participantId"], role)
		matchup_res = round(blue_points/3,2)
		print("matchup result: ", matchup_res)
		self.leagues[desired_rank]["champions"][blue_champ].add_matchup(role, red_champ, matchup_res, win)
		self.leagues[desired_rank]["champions"][red_champ].add_matchup(role, blue_champ, -matchup_res, win)
		return matchup_res

	def tally_cs_gold_lead(self, role, blue_player, red_player):
		points = 0
		if(role != "JUNGLE"):
			if("csDiffPerMinDeltas" in blue_player["timeline"]):
				for time in blue_player["timeline"]["csDiffPerMinDeltas"]:
					if("30" not in time):
						points += blue_player["timeline"]["csDiffPerMinDeltas"][time] * .2
		else:
			points += (blue_player["stats"]["neutralMinionsKilledEnemyJungle"]-red_player["stats"]["neutralMinionsKilledEnemyJungle"]*.35)
			points += (blue_player["stats"]["neutralMinionsKilledTeamJungle"]-red_player["stats"]["neutralMinionsKilledTeamJungle"]*.35)
		if("xpDiffPerMinDeltas" in blue_player["timeline"]):
			for time in blue_player["timeline"]["xpDiffPerMinDeltas"]:
				if("30" not in time):
					points += blue_player["timeline"]["xpDiffPerMinDeltas"][time] * .1
		return points

	def tally_kp_and_op(self, timeline, blue_id, red_id, role):
		#print("role: ", role)
		if(role == "BOT_CARRY" or role == "BOT_SUPPORT"):
			pos = self.coords["BOT"]
		else:
			pos = self.coords[role]
		points = 0
		for frame in timeline[1:14]:
			for event in frame["events"]:
				if(event["type"] == "CHAMPION_KILL" and (event["position"]["x"] in pos["x"] and event["position"]["y"] in pos["y"])):
					if(event["killerId"] == blue_id): 
						if(event["victimId"] == red_id and "assistingParticipantIds" not in event):
							points += 2
						else:
							points += 1
					elif(event["victimId"] == red_id and ("assistingParticipantIds" in event and blue_id in event["assistingParticipantIds"])):
						points += 1
				if(role == "JUNGLE"):
					if(event["type"] == "ELITE_MONSTER_KILL"):
						if(event["killerId"] == blue_id):
							points += 2
						else:
							points -= 1
		return points

	def get_items_data(self):
		#add item tags/descriptions as well, like whether it's damage item, armor, mr etc.
		items_raw_data = self.api_obj.get_static_data("items")["data"]
		temp = {"complete":{}, "trinket":{}, "start":{}}
		for item,val in items_raw_data.items():
			item = int(item)
			if("maps" in val and val["maps"]["11"] and "name" in val and val["gold"]["purchasable"]):
				if("tags" not in val):
					tags = [None]
				else:
					tags = val["tags"]
				if(val["gold"]["total"] <= 500):
					temp["start"][item] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags}
				elif("tags" in val and "Trinket" in val["tags"]):
					temp["trinket"][item] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags}
				elif("into" not in val and ("tags" not in val or "Consumable" not in val["tags"])):
					temp["complete"][item] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags}
		#print(temp)
		return temp

	def get_champs_data(self):
		champs_data = self.api_obj.get_static_data("champions")["data"]
		temp = {}
		for champ_key,champ in champs_data.items():
			temp[champ["id"]] = {"name":champ["name"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"enemy_tips":champ["enemytips"], "ally_tips":champ["allytips"],
								}
		return temp

	def get_keystones_data(self):
		masteries_data = self.api_obj.get_static_data("masteries")
		temp = {}
		keystones = []
		for tree,masteries in masteries_data["tree"].items():
			for keystone in masteries[5]["masteryTreeItems"]:
				#print(keystone)
				keystones.append(keystone["masteryId"])

		for mastery,info in masteries_data["data"].items():
			mastery_id = int(mastery)
			if(mastery_id in keystones):
				temp[mastery_id] = {"id":mastery_id, "name":info["name"], "tree":info["masteryTree"], "des":info["description"]}
		return temp

	def get_runes_data(self):
		runes_data = self.api_obj.get_static_data("runes")["data"]
		temp = {}
		for rune_id,data in runes_data.items():
			#print("key:", rune_id)
			if("Quintessence" in data["name"] or "Greater" in data["name"]):
				temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"]}
		return temp

	def get_summ_spells_data(self):
		spells_data = self.api_obj.get_static_data("summoner-spells")["data"]
		temp = {}
		for spell,data in spells_data.items():
			if("CLASSIC" in data["modes"]):
				temp[data["id"]] = {"name":data["name"], "id":data["id"], "image":data["image"]["full"], "des":data["description"]}
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
	#crawler.get_champ_stats("gold", 250)
	#crawler.get_champ_stats("diamondPlus", 100)
	crawler.print_data("gold")

