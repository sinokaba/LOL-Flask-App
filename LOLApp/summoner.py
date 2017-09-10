from APIConstants import *
from .DBModels import *
from datetime import datetime
from queue import Queue
from threading import Thread
from multiprocessing.pool import ThreadPool
import urllib, time

class Summoner:
	def __init__(self, region, name, api_obj):
		self.riot_api = api_obj
		self.riot_api.set_region(region)
		self.region = region
		self.account = self.riot_api.get_summoner_by_name(name)
		if(self.account is not None):
			self.acc_id = self.account["accountId"]
			self.lvl = self.account["summonerLevel"]
			self.name = self.account["name"]
			self.summ_id = self.account["id"]
			self.profile_icon = self.account["profileIconId"]
			self.coords = {"Top":{"x":range(500,4600),"y":range(9500,14500)},"Mid":{"x":range(5000,9000),"y":range(6000,9500)},
							"Bot":{"x":range(10000,14400),"y":range(600,4500)}, "Jungle":{"x":range(-120,14870),"y":range(-120,14980)}}
			#self.dd_cdn_ver = "7.2.9"
			#print(self.name)

	def get_name(self):
		return self.name

	def account_exists(self):
		return self.account is not None

	def get_lvl(self):
		if(self.account is not None):
			return self.account["summonerLevel"]
		return None

	def get_profile_icon(self):
		return self.get_icon_url("profileicon", self.account["profileIconId"])

	def get_league_rank(self):
		league_data_raw = self.riot_api.get_player_league_data(self.summ_id)
		if(len(league_data_raw) < 1):
			self.league_tier = None
			return None
		for league in league_data_raw:
			print(league)
			if(league["queueType"] == "RANKED_SOLO_5x5"):
				league_data = league
		self.league_tier = league_data["tier"]
		self.league_rank = league_data["rank"]
		return league_data

	def get_ranked_match_history(self):
		start = time.time()
		self.player_tags = {
			"m_damage":"Sorcerer",
			"a_damage":"Warrior", 
			"cs":"Farmer",
			"deaths":"Daredevil",
			"kills":"Executioner",
			"k_sprees":"Mercenary",
			"assists":"Team Player",
			"gold":"Banker", 
			"cc_dealt":"Protector", 
			"time_living":"Godlike",
			"healing_done":"Medic", 
			"damage_taken":"Juggernaut", 
			"vision":"Visionary", 
			"strucs_destroyed":"Demolisher"
		}
		self.added_tracker = {"played":{}, "bans":{}}
		self.matches_visited = {}
		self.player_scores = {
			"rating": 0,
			"vision_score": 0,
			"objective_score": 0,
			"gold_share": 0,
			"dmg_share": 0,
			"wpm": 0,
			"kp": 0,
			"kda": {"kills":0, "deaths":0, "assists":0},
			"cspm": 0,
			"gpm": 0,
			"cs_dif": 0,
			"dpm": 0,
			"ccpm": 0,
			"xppm": 0,
			"laning": 0,
			"unweighted_rating":0
			}
		self.player_info = {
			"bans": [],
			"played": [],
			"chosen_roles": {},
			"plays_period": {},	
			"total_wins": 0,
			"num_remakes": 0,
			"game_length": 0,
			"blue_team": {"count":0, "wins":0},
			"tags": {}
		}
		self.highlight_game = None
		match_history_raw = self.riot_api.get_matches_all(self.acc_id)
		self.matches_key = []
		index = 0
		num_games_to_search = 20

		if(match_history_raw is not None and "status" not in match_history_raw):
			matches_list = match_history_raw["matches"]
			total_games = len(matches_list)
			if(total_games < num_games_to_search):
				num_games_to_search = total_games
			matches_queue = Queue()
			for match in matches_list[:num_games_to_search]:
				#async_result = pool.apply_async(self.process_match, (match,)) # tuple of args for foo
				# do some other stuff in the main process
				#match_history.append(async_result.get())  # get the return value from your function.
				#match_history.append(self.process_match(match))
				matches_queue.put(match)
			num_threads = 10
			for i in range(num_threads):
				worker = Thread(target=self.process_match, args=(matches_queue,))
				worker.setDaemon(True)
				worker.start()
			matches_queue.join()
			
			match_history = []
			#print(self.matches_visited)
			self.matches_key.sort(reverse=True)
			for key in self.matches_key:
				match_history.append(self.matches_visited[key])
			self.player_info["played"] = sorted(self.player_info["played"], key=lambda c:c["plays"], reverse=True)
			if(self.player_info["played"][0]["plays"] >= num_games_to_search*.85):
				self.player_info["champ_pool_weighting"] = .9
			else:
				self.player_info["champ_pool_weighting"] = 1 
			upper_percentile_rankings = ["CHALLENGER", "MASTER"]
			self.player_info["bans"] = sorted(self.player_info["bans"], key=lambda c:c["ban_num"], reverse=True)
			self.player_info["best_champs"] = sorted(self.player_info["played"], key=lambda c:c["rating"]/(c["plays"]-c["remakes"]), reverse=True)
			self.player_info["num_games"] = {"total":num_games_to_search, "counted": num_games_to_search-self.player_info["num_remakes"]}
			if(self.player_info["total_wins"]/self.player_info["num_games"]["counted"] >= .85):
				if(self.league_tier not in upper_percentile_rankings or (self.league_tier == "DIAMOND" and self.league_rank == "V")):
					self.player_info["champ_pool_weighting"] *= .8		
			most_frequent_tags = []
			while(len(most_frequent_tags) < 3):
				most_frequent_tag = max(self.player_info["tags"], key=self.player_info["tags"].get)
				most_frequent_tags.append(most_frequent_tag)
				del[self.player_info["tags"][most_frequent_tag]]
			self.player_info["tags"] = most_frequent_tags
			print(most_frequent_tags)	
			end = time.time()
			print("this took: ", end-start, " seconds")
			print(self.player_info["played"])
			return match_history, self.player_info, self.player_scores, self.highlight_game
		return None


	def process_match(self, q):
		while True:
			match = q.get()

			game_id = match["gameId"]
			game = self.riot_api.get_match_data(game_id)
			if(game):
				creation_epoch = game["gameCreation"]
				participants_queue = Queue()
				#if queue is not rank need to identify player by champ played
				#error when number of matches requested > 10 because of rate limit
				#print("game participants: ", game["participants"])
				game_minutes = game["gameDuration"]//60.0
				game_seconds = str(game["gameDuration"]%60) if game["gameDuration"]%60 > 10 else str(game["gameDuration"]%60) + "0"
				game["game_dur"] = str(int(game_minutes)) + ":" + game_seconds
				game_date = datetime.fromtimestamp(game["gameCreation"]/1000)
				self.get_play_dates(game_date)
				player_idx = 0
				player_team_id = 100
				player_role = None
				player_unw_rating = 0
				player_champ = None
				player_champ_q = None
				#game_minutes = game["gameDuration"]//60.0
				#print(game)
				game["player_tags"] = []
				players_data = {}
				team_stats = {
				100: {
				"t_damage":0,
				"t_kills":0,
				"t_gold":0,
				"t_assists":0,
				"t_deaths":0,
				"t_rating":0,
				"spot_metrics":{
					"m_damage":[],
					"a_damage":[], 
					"cs":[],
					"k_sprees":[],
					"assists":[],
					"gold":[], 
					"kills":[], 
					"cc_dealt":[], 
					"time_living":[],
					"healing_done":[], 
					"damage_taken":[], 
					"vision":[], 
					"strucs_destroyed":[]
					}
				}, 
				200: {
				"t_damage":0,
				"t_kills":0,
				"t_assists":0,
				"t_deaths":0,
				"t_gold":0,
				"t_rating":0,
				"spot_metrics":{
					"m_damage":[],
					"a_damage":[], 
					"cs":[],
					"k_sprees":[],
					"assists":[],
					"gold":[], 
					"kills":[], 
					"cc_dealt":[], 
					"time_living":[],
					"healing_done":[], 
					"damage_taken":[], 
					"vision":[], 
					"strucs_destroyed":[]
					}
				}
				}
				if(game["queueId"] in GAMEMODE):
					game["queue"] = GAMEMODE[game["queueId"]][0]
				else:
					game["queue"] = GAMEMODE[-1]
				
				if(game_minutes > 5):
					remake = False
					if(game["teams"][0]["win"] != "Fail"):
						game["teams"][0]["result"] = "VICTORY"
						game["teams"][1]["result"] = "DEFEAT"					
					else:
						game["teams"][1]["result"] = "VICTORY"
						game["teams"][0]["result"] = "DEFEAT"
				else:
					game["teams"][1]["result"] = "REMAKE"
					game["teams"][0]["result"] = "REMAKE"
					remake = True

				for participant in game["participants"]:
					champ = participant["championId"]
					par_id = participant["participantId"]
					player_data = game["participantIdentities"][par_id-1]["player"]
					participant["name"] = player_data["summonerName"]
					player_id = player_data["currentAccountId"]
					participants_queue.put(participant)

					if(par_id <= 5):
						team_id = 100
					else:
						team_id = 200
					vis_score = self.get_vis_sc(participant, game_minutes)
					participant["vision"] = vis_score
					team_stats[team_id]["t_damage"] += participant["stats"]["totalDamageDealtToChampions"]
					team_stats[team_id]["t_gold"] += participant["stats"]["goldEarned"]
					team_stats[team_id]["t_kills"] += participant["stats"]["kills"]
					team_stats[team_id]["t_assists"] += participant["stats"]["assists"]
					team_stats[team_id]["t_deaths"] += participant["stats"]["deaths"]
					cur_player_stat_tracker = {
						"kills": participant["stats"]["kills"],
						"gold": participant["stats"]["goldEarned"],
						"vision": vis_score,
						"a_damage": participant["stats"]["physicalDamageDealtToChampions"],
						"m_damage": participant["stats"]["magicDamageDealtToChampions"],
						"assists": participant["stats"]["assists"],
						"time_living": participant["stats"]["longestTimeSpentLiving"],
						"healing_done": participant["stats"]["totalHeal"],
						"damage_taken": participant["stats"]["totalDamageTaken"],
						"k_sprees": participant["stats"]["killingSprees"] + participant["stats"]["largestKillingSpree"],			
						"cc_dealt": participant["stats"]["totalTimeCrowdControlDealt"] + participant["stats"]["timeCCingOthers"],
						"cs": participant["stats"]["totalMinionsKilled"],
						"strucs_destroyed": participant["stats"]["damageDealtToTurrets"]**.15
					}
					for metric,player_list in team_stats[team_id]["spot_metrics"].items():
						if(len(player_list) < 2):
							player_list.append({"id":par_id, "stat_val":cur_player_stat_tracker[metric]})
						else:
							for player in player_list:
								if(player["stat_val"] < cur_player_stat_tracker[metric]):
									player["id"] = par_id
									player["stat_val"] = cur_player_stat_tracker[metric]
									break
					#perhaps instead of repeatedly making api calls to static data api, just store item ids,spell ids, keystone ids, and grab their images from db
					spell1_q = SpellBase.get(SpellBase.spellId == participant["spell1Id"])
					spell2_q = SpellBase.get(SpellBase.spellId == participant["spell2Id"])
					participant["spell1"] = {"image":spell1_q.image, "name": spell1_q.name, "des": spell1_q.des}
					participant["spell2"] = {"image":spell2_q.image, "name": spell2_q.name, "des": spell2_q.des}
					try:
						champ_info_q = ChampBase.get(ChampBase.champId == champ)
						if(champ_info_q.tag2 is not None):
							tags = champ_info_q.tag1 + "/" + champ_info_q.tag2
						else:
							tags = champ_info_q.tag1
						participant["champ"] = {"image": champ_info_q.image, "name": champ_info_q.name, "tags": tags}			
						champ_tags = [champ_info_q.tag1, champ_info_q.tag2]
						participant_role = self.get_role(participant, game_minutes, champ_tags)
						participant["items"] = []
						for i in range(7):
							item_key = "item"+str(i)
							item_q = ItemBase.select().where(ItemBase.itemId == participant["stats"][item_key])
							if(participant["stats"][item_key] != 0 and item_q.exists()):
								item_q = item_q.get()
								participant["items"].append({"image": item_q.image, "name": item_q.name, "des": item_q.des})
							else:
								participant["items"].append("/static/imgs/no-item")
						
						if(participant_role.lower() == "adc" or participant_role.lower() == "support"):
							players_data[par_id] = {"lane": "Bot", "role": participant_role, "kill_points": 0, "mon_smites_p": 0}
						else:
							players_data[par_id] = {"lane": participant_role, "role": participant_role, "kill_points": 0, "mon_smites_p": 0}						
						if(player_id == self.acc_id):
							player_champ = champ
							player_role = participant_role
							for mastery in participant["masteries"]:
								if(mastery["masteryId"] in KEYSTONE_MASTERIES):
									print("ks id: ", mastery["masteryId"])
									keystone_q = MasteryBase.get(MasteryBase.masteryId == mastery["masteryId"])
									participant["keystone"] = {"image": mastery["masteryId"], "name": keystone_q.name, "des": keystone_q.des}
							player_idx = par_id - 1
							if(par_id > 5):
								player_team_id = 200
							game["place"] = player_idx
							if(player_team_id == 100):
								team_game_stats = game["teams"][0]
							else:
								team_game_stats = game["teams"][1]
							for ban in team_game_stats["bans"]:
								if(ban["pickTurn"] == par_id):
									if(ban["championId"] != -1):
										banned_champ_q = ChampBase.get(ChampBase.champId == ban["championId"])
										if(ban["championId"] not in self.added_tracker["bans"]):
											self.player_info["bans"].append({"ban_num":1, "name": banned_champ_q.name, "image": banned_champ_q.image})
											self.added_tracker["bans"][ban["championId"]] = len(self.player_info["bans"])-1
										else:
											self.player_info["bans"][self.added_tracker["bans"][ban["championId"]]]["ban_num"] += 1 
							if(champ not in self.added_tracker["played"]):
								self.player_info["played"].append({
									"plays":1, 
									"rating":0,
									"uw_rating":0,
									"remakes":0,
									"image": champ_info_q.image,
									"name": champ_info_q.name,
									"splash": champ_info_q.image.split(".")[0]
									})
								champ_index = len(self.player_info["played"])-1
								print(champ_index)
								self.added_tracker["played"][champ] = champ_index
							else:
								self.player_info["played"][self.added_tracker["played"][champ]]["plays"] += 1					
							if(par_id <= 5):
								game["result"] = game["teams"][0]["result"]
							else:
								game["result"] = game["teams"][1]["result"]

							res = participant["stats"]["win"]
							if(res):
								self.player_info["total_wins"] += 1
							if(player_team_id == 100):
								self.player_info["blue_team"]["count"] += 1
								if(res):
									self.player_info["blue_team"]["wins"] += 1
							if(not remake):
								self.player_scores["kda"]["kills"] += participant["stats"]["kills"]
								self.player_scores["kda"]["deaths"] += participant["stats"]["deaths"]
								self.player_scores["kda"]["assists"] += participant["stats"]["assists"]
								self.player_scores["cspm"] += participant["stats"]["totalMinionsKilled"]/game_minutes
								self.player_scores["gpm"] += participant["stats"]["goldEarned"]/game_minutes
								self.player_scores["wpm"] += participant["stats"]["wardsPlaced"]/game_minutes
								self.player_scores["dpm"] += participant["stats"]["totalDamageDealtToChampions"]/game_minutes
								if("csDiffPerMinDeltas" in participant["timeline"]):
									self.player_scores["cs_dif"] += participant["timeline"]["csDiffPerMinDeltas"]["0-10"]
								xp_avg = 0
								if("xpPerMinDeltas" in participant["timeline"]):
									for interval,xp in participant["timeline"]["xpPerMinDeltas"].items():
										xp_avg += xp
									self.player_scores["xppm"] += xp_avg/len(participant["timeline"]["xpPerMinDeltas"])
								self.player_scores["ccpm"] += participant["stats"]["totalTimeCrowdControlDealt"]
								if(player_role not in self.player_info["chosen_roles"]):
									self.player_info["chosen_roles"][player_role] = 1
								else:
									self.player_info["chosen_roles"][player_role] += 1
					except ChampBase.DoesNotExist:
						q.task_done()
						return
					#print(game_data)
				#print(match_history)
				#game_duration_s = game["gameDuration"]
				#print("item url: ", game["participants"][game["place"]]["item4_img"])
				if(team_stats[100]["t_kills"] == 0):
					team_stats[100]["t_kills"] = 1
					team_stats[200]["t_deaths"] = 1
				if(team_stats[200]["t_kills"] == 0):
					team_stats[200]["t_kills"] = 1
					team_stats[100]["t_deaths"] = 1
				if(not remake):
					for metric,player_list in team_stats[player_team_id]["spot_metrics"].items():
						for player in player_list:
							if(player["id"] == player_idx + 1):
								tag = self.player_tags[metric]
								game["player_tags"].append(self.player_tags[metric])
								if(tag not in self.player_info):
									self.player_info["tags"][tag] = 0
								else:
									self.player_info["tags"][tag] += 1									
					match_timeline = self.riot_api.get_match_timeline(game_id)
					self.tally_kills_smites(match_timeline, players_data)
					"""
					num_threads = 5
					for i in range(num_threads):
						worker = Thread(target=self.process_match, args=(participants_queue,))
						worker.setDaemon(True)
						worker.start()
					participants_queue.join()
					"""
					for participant_d in game["participants"]:
						p_id = participant_d["participantId"]
						player_early_data = players_data[p_id]
						if(p_id <= 5):
							team_id = 100
						else:
							team_id = 200
						overall_performance = self.get_player_scores(participant_d, player_early_data["role"], team_stats[team_id], game_minutes, participant_d["vision"])
						laning = self.analyze_laning(participant_d, player_early_data["role"], champ, player_early_data["kill_points"], player_early_data["mon_smites_p"])
						unweighted_rating = (laning*.3) + (overall_performance[0]*.7)
						team_stats[team_id]["t_rating"] += unweighted_rating
						participant_d["rating"] = unweighted_rating			
						participant_d["objectives"] = overall_performance[1]
						participant_d["role"] = player_early_data["role"]
						if(p_id == player_idx+1):
							rank_weight = self.get_rank_weight()
							weighted_rating = unweighted_rating*rank_weight	
							game["obj_score"] = round(overall_performance[1],2)
							game["vis_score"] = round(participant_d["vision"],2)
							game["player_rating"] = weighted_rating
							game["player_rating_unweighted"] = unweighted_rating
							player_unw_rating = unweighted_rating
							self.player_scores["objective_score"] += overall_performance[1]
							self.player_scores["vision_score"] += participant_d["vision"]
							self.player_scores["rating"] += weighted_rating
							self.player_scores["laning"] += laning
							self.player_scores["unweighted_rating"] += unweighted_rating
							self.player_scores["kp"] += game["participants"][player_idx]["stats"]["kills"]/(team_stats[player_team_id]["t_kills"]*1.0)
							self.player_info["game_length"] += game_minutes
							self.player_scores["gold_share"] += game["participants"][player_idx]["stats"]["goldEarned"]/(team_stats[player_team_id]["t_gold"]*1.0)
							self.player_scores["dmg_share"] += game["participants"][player_idx]["stats"]["totalDamageDealtToChampions"]/(team_stats[player_team_id]["t_damage"]*1.0)	
							if(player_champ is not None):
								self.player_info["played"][self.added_tracker["played"][player_champ]]["rating"] += weighted_rating	
								self.player_info["played"][self.added_tracker["played"][player_champ]]["uw_rating"] += unweighted_rating													
				else:
					for participant_remake in game["participants"]:
						participant_remake["rating"] = "Undefined"
						participant_remake["vision"] = 0
						participant_remake["objectives"] = 0
					game["player_rating"] = "Undefined"
					game["player_rating_unweighted"] = "Undefined"
					game["obj_score"] = 0
					game["vis_score"] = 0
					self.player_info["num_remakes"] += 1
				game["gameCreation"] = time.strftime('%m/%d/%Y', time.gmtime(game["gameCreation"]/1000))
				game["blue_team_stats"] = team_stats[100]
				game["red_team_stats"] = team_stats[200]
				self.matches_key.append(creation_epoch)
				self.matches_visited[creation_epoch] = game
				print("tags: ", game["player_tags"])
				if(not remake):
					if(self.highlight_game is None):
						self.highlight_game = game
					else:
						if(self.highlight_game["player_rating_unweighted"] < player_unw_rating):
							self.highlight_game = game
				q.task_done()
				#print(game)
			else:
				with q.mutex:
				    q.queue.clear()

	def get_player_rating(self):
		player_par_id = players_data[game["participants"][player_idx]["participantId"]]
		self.player_info["game_length"] += game_minutes
		self.player_scores["gold_share"] += game["participants"][player_idx]["stats"]["goldEarned"]/(team_stats[player_team_id]["gold"]*1.0)
		self.player_scores["dmg_share"] += game["participants"][player_idx]["stats"]["totalDamageDealtToChampions"]/(team_stats[player_team_id]["damage"]*1.0)
		player_data = game["participants"][player_idx]
		overall_performance = self.get_player_scores(player_data, player_role, team_stats[player_team_id], game_minutes)
		laning = self.analyze_laning(player_data, player_role, champ, player_par_id["kill_points"], player_par_id["mon_smites_p"])
		unweighted_rating = (laning*.35) + (overall_performance[0]*.65)
		weighted_rating = unweighted_rating*self.get_rank_weight()
		self.player_scores["objective_score"] += overall_performance[1]
		self.player_scores["vision_score"] += overall_performance[2]
		self.player_scores["rating"] += weighted_rating
		self.player_scores["laning"] += laning
		self.player_scores["unweighted_rating"] += unweighted_rating
		game["obj_score"] = round(overall_performance[1],2)
		game["vis_score"] = round(overall_performance[2],2)
		game["player_rating"] = weighted_rating
		game["player_rating_unweighted"] = unweighted_rating
		if(player_champ is not None):
			self.player_info["played"][self.added_tracker["played"][player_champ]]["rating"] += weighted_rating			
		self.player_scores["kp"] += game["participants"][player_idx]["stats"]["kills"]/(team_stats[player_team_id]["kills"]*1.0)

	def get_rank_weight(self):
		if(self.league_tier is None):
			return 1
		if(self.league_tier == "CHALLENGER" or self.league_tier == "MASTER"):
			return 1.65
		elif(self.league_tier == "DIAMOND" and (self.league_rank == "I" or self.league_rank == "II")):
			return 1.35
		elif(self.league_tier == "DIAMOND"):
			return 1.2
		elif(self.league_tier == "PLATINUM"):
			return 1.1
		elif(self.league_tier == "GOLD"):
			return 1
		elif(self.league_tier == "SILVER"):
			return .8
		elif(self.league_tier == "BRONZE"):
			return .5
		else:
			return 1

	def get_play_dates(self, datetime_obj):
		weekday = datetime_obj.weekday()
		hour = datetime_obj.hour
		if(weekday == 0):
			weekday = "Monday"
		elif(weekday == 1):
			weekday = "Tuesday"
		elif(weekday == 2):
			weekday = "Wednesday"
		elif(weekday == 3):
			weekday = "Thursday"
		elif(weekday == 4):
			weekday = "Friday"
		elif(weekday == 5):
			weekday = "Saturday"
		elif(weekday == 6):
			weekday = "Sunday"
		if(hour <= 12):
			time_period = "0-12 AM"
		else:
			time_period = "0-12 PM"
		if(weekday not in self.player_info["plays_period"]):
			self.player_info["plays_period"][weekday] = {time_period:1}
		else:
			if(time_period not in self.player_info["plays_period"][weekday]):
				self.player_info["plays_period"][weekday][time_period] = 1
			else:
				self.player_info["plays_period"][weekday][time_period] += 1				

	def get_role(self, player_data, duration, champ_tags):
		#jungle role hard to pin down, because riot seems to do role aassignments based on location. 
		#mid and support roaming a lot sometimes gets confused as jungler
		spell1 = player_data["spell1Id"]
		spell2 = player_data["spell2Id"]
		mons_killed_per_min = ((player_data["stats"]["neutralMinionsKilledTeamJungle"] + 
								player_data["stats"]["neutralMinionsKilledEnemyJungle"])/duration)
		if((spell1 == 11 or spell2 == 11) or mons_killed_per_min >= 2.3):
			role = "Jungle"
		else:
			role = player_data["timeline"]["lane"]
			if(role.title() == "Jungle"):
				#check if the player has smite, and jungle monsters killed
				if(spell1 != 11 and spell2 != 11 and mons_killed_per_min < 2.3):
					if("Support" in champ_tags):
						role = "Support"
					elif("Marksman" in champ_tags):
						role = "ADC"
					elif(spell1 == 12 or spell2 == 12):
						role = "Top"
					else:
						role = "Mid"
			elif(role == "BOTTOM"):
				#check if the player has a large amount of jungle monster kills, jungle most likely
				if((spell1 == 11 or spell2 == 11) or mons_killed_per_min >= 2.3):
					role = "Jungle"
				else:
					role = self.decide_bot_roles(player_data["timeline"], champ_tags, spell1, spell2)
		if(role == "MIDDLE"):
			role = "Mid"
		return role.title() if role != "ADC" else role
		
	def decide_bot_roles(self, player_timeline, champ_tags, sp1, sp2):
		role = None
		def check_cspm(player, cur_role):
			try:
				if(player["creepsPerMinDeltas"]["0-10"] >= 3):
					return "ADC"
				else:
					return "Support"
			except:
				KeyError
				return cur_role

		if("CARRY" in player_timeline["role"]):
			role = "ADC"
		elif("SUPPORT" in player_timeline["role"]):
			role = "Support"
		else:
			#print("tags: ", tags)
			if(sp1 == 7 or sp2 == 7 or "Marksman" in champ_tags):
				role = check_cspm(player_timeline, "ADC")
			else:
				role = check_cspm(player_timeline, "Support")
		return role
		
	def analyze_laning(self, player, role, champ, kill_points, smite_points):
		#print("des rank: ", desired_rank)
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		#print("ks points: ", kill_points, " smite points: ", smite_points)
		if(kill_points >= 4):
			points = 2
		elif(kill_points >= 2):
			points = 1
		elif(kill_points > 0):
			points = .5
		else:
			points = 0
		if(smite_points > 1):
			points += 1.5
		elif(smite_points > 0):
			points += 1
		points += self.tally_cs_gold_lead(role, player) 
		#points += self.tally_kills_smites(match_timeline, player["participantId"], role)
		matchup_res = points/3
		#print("matchup result: ", matchup_res)
		return matchup_res

	def tally_cs_gold_lead(self, role, player):
		early_game = "0-10"
		points = 0
		if("csDiffPerMinDeltas" in player["timeline"]):
			if(role != "Jungle"):
				expected_lead = 1
			else:
				expected_lead = .4
			if(player["timeline"]["csDiffPerMinDeltas"][early_game] >= expected_lead*2):
				points += 2
			elif(player["timeline"]["csDiffPerMinDeltas"][early_game] > expected_lead):
				points += 1
		if("xpDiffPerMinDeltas" in player["timeline"]):
			if(player["timeline"]["xpDiffPerMinDeltas"][early_game] >= 100):
				points += 2
			elif(player["timeline"]["xpDiffPerMinDeltas"][early_game] >= 50):
				points += 1
		return points

	def tally_kills_smites(self, timeline, players):
		#print("role: ", role)
		#print(timeline)
		for frame in timeline["frames"][1:13]:
			for event in frame["events"]:
				self.get_early_kills(event, players)
				self.get_monster_kills(event, players)

	#team->role->id
	def get_early_kills(self, timeframe, player_par_ids):
		if(timeframe["type"] == "CHAMPION_KILL" and timeframe["killerId"] != 0):
			#print("killer id: ", timeframe["killerId"], " players_dict: ", player_par_ids)
			pos = self.coords[player_par_ids[timeframe["killerId"]]["lane"]]
			if(timeframe["position"]["x"] in pos["x"] and timeframe["position"]["y"] in pos["y"]): 
				player_par_ids[timeframe["killerId"]]["kill_points"] += 1
			elif("assistingParticipantIds" in timeframe and len(timeframe["assistingParticipantIds"]) < 3):
				for par_id in timeframe["assistingParticipantIds"]:
					player_par_ids[par_id]["kill_points"] += .5
			if("assistingParticipantIds" not in timeframe):
				player_par_ids[timeframe["victimId"]]["kill_points"] -= 1
			else:
				player_par_ids[timeframe["victimId"]]["kill_points"] -= .5
	"""
	def get_early_kills(self, timeframe, player_id, loc):
		kill_points = 0
		if(timeframe["type"] == "CHAMPION_KILL" and (timeframe["position"]["x"] in loc["x"] and timeframe["position"]["y"] in loc["y"])):
			if(timeframe["killerId"] == player_id): 
				kill_points += 1
			elif("assistingParticipantIds" in timeframe and player_id in timeframe["assistingParticipantIds"]):
				kill_points += .5
			if(timeframe["victimId"] == player_id):
				if("assistingParticipantIds" not in timeframe):
					kill_points -= 1
				else:
					kill_points -= .5
		if(kill_points >= 4):
			return 2
		elif(kill_points >= 2):
			return 1
		elif(kill_points > 0):
			return .5
		else:
			return 0
	"""

	def get_monster_kills(self, timeframe, player_par_ids):
		if(timeframe["type"] == "ELITE_MONSTER_KILL"):
			if(player_par_ids[timeframe["killerId"]]["lane"] == "Jungle"):
				player_par_ids[timeframe["killerId"]]["mon_smites_p"] += 1
			else:
				player_par_ids[timeframe["killerId"]]["mon_smites_p"] += 1.5

	def get_player_scores(self, player, role, team, duration, vis_score):
		if(player["stats"]["win"]):
			score = 1
		else:
			score = 0
		ka = player["stats"]["kills"]+player["stats"]["assists"]
		deaths = player["stats"]["deaths"]
		if(deaths == 0):
			deaths = 1
		kda = ka/deaths
		if(kda >= 4):
			score += 2
		elif(kda >= 2):
			score += 1.6
		elif(kda >= 1.5):
			score += 1.3
		elif(kda >= 1):
			score += 1.1
		score += (self.get_team_contribution(player, ka, role, team["t_damage"], team["t_gold"], team["t_kills"])*.6)
		obj_sc = self.get_obj_sc(player, duration)
		#print("obj: ", obj_sc, " vis: ", vis_sc)
		score += (obj_sc*2) + (vis_score*2)
		#print("score: ", score)
		return (score/10),obj_sc

	def get_obj_sc(self, player, game_dur):
		stats = player["stats"]
		points = 1 if stats["win"] else 0
		if("firstTowerAssist" in stats and stats["firstTowerAssist"]):
			points += .5
		elif("firstTowerKill" in stats and stats["firstTowerKill"]):
			points += 1
		if("firstInhibitorAssist" in stats and stats["firstInhibitorAssist"]):
			points += .5
		elif("firstInhibitorKill" in stats and stats["firstInhibitorKill"]):
			points += 1
		#print("objectives damage: ", stats["damageDealtToObjectives"])
		points += ((stats["damageDealtToObjectives"]/game_dur)**.15)*.5
		#print("objective points earned: ", points)
		return points

	def get_vis_sc(self, player, game_dur):
		#using riot's own visonscore which is calculated based on how much vision you provided/denied
		try:
			vis = player["stats"]["visionScore"]
			vis += (player["stats"]["visionWardsBoughtInGame"]*2)
			vis += player["stats"]["wardsPlaced"]*.5
			vis += player["stats"]["wardsKilled"]*.5
			return vis/game_dur
		except:
			KeyError
		return 0

	def get_team_contribution(self, player, ka, role, team_dmg, team_gold, team_kills):
		score = 0
		if(role == "Support"):
			expected_share = .12
		elif(role == "Adc" or role == "Mid"):
			expected_share = .25
		else:
			expected_share = .18
		kill_par = ka/team_kills
		#print("kill participation: ", kill_par)
		if(kill_par >= .7):
			score += 2
		elif(kill_par >= .5):
			score += 1.5
		elif(kill_par >= .3):
			score += 1
		dmg_share = self.get_player_share(player["stats"]["totalDamageDealtToChampions"], team_dmg, expected_share)
		gold_share = self.get_player_share(player["stats"]["goldEarned"], team_gold, expected_share)
		score += (dmg_share/gold_share)*2
		return score

	def get_player_share(self, player_stat, team_stat, exp_cont=None):
		if(team_stat > 5):
			player_cont = player_stat/team_stat
			if(exp_cont is None):
				return player_stat,player_cont
			if(player_cont > (exp_cont*2)):
				return 3
			if(player_cont > (exp_cont*1.4)):
				return 2
			elif(player_cont > (exp_cont)):
				return 1.5
			elif(player_cont >= (exp_cont*.9)):
				return 1
		return 1

	def get_icon_url(self, categ, icon_id):
		#print("icon = ", icon_id)
		#time.sleep(.9)
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
				cdn_version="7.15.1",
				category=categ,
				name=name
				)
