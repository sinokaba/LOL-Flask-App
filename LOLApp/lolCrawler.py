import APIConstants, urllib, time, json, requests
import _pickle as cPickle
from crawlerStaticData import CrawlerStaticData
from multiprocessing import Process
from threading import Thread
from queue import Queue
from random import randint
from championStats import ChampionStats
from playersStats import PlayerStats
from apiCalls import APICalls
from DBHandler import *

class LolCrawler:
	"""
	/Initialize the Apicalls object and lane coordinates
	"""
	def __init__(self, db, static_data, reset=False):
		self.api_obj = APICalls()
		self.static = static_data
		self.db = db
		#self.init_static_data(update_static)
		#gives the coordinates in the minimap where the champ in its role is expected to be at
		self.coords = {"Top":{"x":range(500,4600),"y":range(9500,14500)},"Mid":{"x":range(5000,9000),"y":range(6000,9500)},
						"Bot":{"x":range(10000,14400),"y":range(600,4500)}, "Jungle":{"x":range(-120,14870),"y":range(-120,14980)}}

	def set_region(self, region):
		self.api_obj.set_region(region)
		self.region = region

	def add_data_to_db(self):
		self.db.add_games_visited_db(self.matches_visited_list, self.matches_visited)
		league_file = open("league_file.txt", "w")
		for league in self.leagues:
			champs = self.leagues[league]["champions"]
			#league_file.write("Region: " + self.region + " League: " + league + "\n")
			if(len(champs) > 0):
				stats_base_mod = self.db.create_base_info(self.region, league)

				#print(league)
				#print(self.leagues[league])
				if("game_dur" in self.leagues[league]):
					game_l = self.leagues[league]["game_dur"]
				else:
					game_l = 0
				self.db.add_monsters_db(self.leagues[league]["mons"], league, self.region, stats_base_mod)
				self.db.add_teams_db(self.leagues[league]["teams"], game_l, league, self.region, len(self.remakes), stats_base_mod)
				self.db.add_champ_stats(champs, APIConstants.CURRENT_PATCH, stats_base_mod)
					
				for champ in champs:
					league_file.write(str(champs[champ].champ_id) + ": " + str(champs[champ].t_rating) + " \n")
		league_file.close()

	def aggregate_rank_data(self, desired_rank=None, num_matches=1000, region="NA"):
		print("region =", region)
		self.api_obj.set_region(region)
		self.region = region
		print("region =", self.region)
		start = time.time()
		self.players_visited = {}
		self.matches_visited_list = []
		self.mh_visited = []
		self.matches_visited = []
		self.remakes = []
		self.rank_tiers_vis = []
		self.leagues = {"diamondPlus":
							{"rank_tiers":["DIAMOND", "CHALLENGER", "MASTER"],
							"champions":{}, 
							"mons":{},
							"teams":{100:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}, 
					  				200:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}},
							},
						"silverMinus":
							{"rank_tiers":["SILVER", "BRONZE"],
							"champions":{}, 
							"mons":{},
							"teams":{100:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}, 
					  				200:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}}
							},
						"gold":
							{"rank_tiers":["GOLD"],
							"champions":{}, 
							"mons":{},
							"teams":{100:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}, 
					  				200:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}}
							},
						"platinum":
							{"rank_tiers":["PLATINUM"],
							"champions":{}, 
							"mons":{},
							"teams":{100:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}, 
					  				200:{"wins":0, "first_drag":0, "first_tower":0, "first_baron":0, "first_blood": 0, "first_herald":0}}
							},
						}
		if(desired_rank is None):
			self.search_players_in_tier(None, None, [[2558586644, 2558272413], ["GOLD", "DIAMOND"]])
		else:
			if(desired_rank == "diamondPlus"):
				league_players = self.api_obj.get_master_players()
			elif(desired_rank in APIConstants.STARTING_PLAYERS[self.region]):
				league_players = self.api_obj.get_league(APIConstants.STARTING_PLAYERS[self.region][desired_rank])[0]
			else:
				return "Invalid Parameters"
			self.search_players_in_tier(league_players, num_matches)

		self.add_data_to_db()
		#self.add_gamed_visited_db()
		#self.add_players_db()
		end = time.time()
		print("Searching ", len(self.matches_visited_list), " matches took: ", end - start, " seconds.")

	def search_players_in_tier(self, league, num_matches, matches_supplied=None, season=9, q=420):
		self.player_leagues_to_visit = []
		if(matches_supplied is None):
			self.rank_tiers_vis.append(league["tier"] + " " + league["name"])
			for player in league["entries"]:
				if(len(self.matches_visited_list) < num_matches):
					print("region: ", self.region, " player name: ", player["playerOrTeamName"], " id: ", player["playerOrTeamId"])
					player_data = self.api_obj.get_summoner_by_summid(player["playerOrTeamId"])
					if(player_data is not None):
						acc_id = player_data["accountId"]
						print("account id: ", acc_id)
						if(acc_id not in self.players_visited):
							self.add_player(acc_id, player_data["name"], player_data["id"], league["tier"])
						if(acc_id not in self.mh_visited and len(self.matches_visited_list) < num_matches):
							print(player_data["name"], " ", acc_id, " ", league["tier"])
							self.mh_visited.append(acc_id)
							match_history = self.get_history(acc_id, season, q)
							if(match_history is not None):
								self.crawl_history(match_history["matches"], num_matches, league)
			if(len(self.matches_visited_list) < num_matches):
				for player in self.player_leagues_to_visit.pop():
					print("p: ", player)
					if(len(self.matches_visited_list) < num_matches):
						acc_id = player["player"]["currentAccountId"]
						print("account id: ", acc_id)
						if(acc_id not in self.players_visited):
							rank = self.api_obj.get_league(player["player"]["summonerId"])[0]
							print((rank["tier"] + " " + rank["name"]))
							if((rank["tier"] + " " + rank["name"]) not in self.rank_tiers_vis):
								self.search_players_in_tier(rank, num_matches)
		else:
			self.crawl_history(matches_supplied, num_matches, league)


	def crawl_history(self, match_history, num_matches, league_tier):
		for match in match_history:
			#matches_queue.put(match)
			game_id = match["gameId"]
			if(len(self.matches_visited_list) < num_matches):
				if(self.check_game(game_id, match["timestamp"]/1000)):
					print(len(self.matches_visited_list), "/", num_matches)
					print("game id :", game_id)
					match_details = self.get_match_details(game_id)
					if(match_details is not None):
						if(len(self.player_leagues_to_visit) < 5):
							self.player_leagues_to_visit.append(match_details["participantIdentities"])
						#1496197986 is june 1st
						game_creation_time = match_details["gameCreation"]/1000
						print("game created at: ", game_creation_time)
						if(match_details is not None):
							patch = self.get_match_patch(game_creation_time)									
							tier = self.get_tier_k(league_tier["tier"])
							self.matches_visited.append({"matchId":game_id, "patch":patch, "baseInfo":self.db.create_base_info(self.region,tier)})
							self.matches_visited_list.append(game_id)
							print("315 tier: ", tier)
							game_dur = match_details["gameDuration"]
							if(game_dur < 300):
								self.remakes.append(game_id)
							else:
								self.add_banned_champs(match_details, tier, patch)
								match_timeline = self.api_obj.get_match_timeline(game_id)
								if(match_timeline is not None):
									timeline = match_timeline["frames"]
									participants = match_details["participants"]
									self.current_participants_data = {}
									self.agg_team_stats = {100: {"kills":0, "gold":0, "damage":0, "rank_weight":0}, 
															200:{"kills":0, "gold":0, "damage":0, "rank_weight":0}}									
									self.get_prelim_match_data(participants, timeline, game_dur)
									self.get_early_takedowns(timeline)
									#get each players' role and put them into this dict, this dict will track early game kills/smites and others
									self.added_monster_stats = False
									#self.get_team_stats(participants)
									self.process_player_pairs(match_details, timeline, participants, tier, patch)
									self.add_team_stats(match_details, tier)
									if("game_dur" not in self.leagues[tier]):
										self.leagues[tier]["game_dur"] = game_dur/60
									else:
										self.leagues[tier]["game_dur"] += game_dur/60
									self.process_match_timeline(timeline, tier)									
						else:
							break		

	def get_match_patch(self, match_creation):
		if(match_creation >= 1502204294):
			return "7.16.1"											
		elif(match_creation >= 1501082571):
			return "7.15.1"
		elif(match_creation >= 1499875845):
			return "7.14.1"
		elif(match_creation >= 1498608682):
			return "7.13.1"									

	def check_game(self, game_id, creation):
		#print("creating time: ", creation)
		game_query = GamesVisited.select().join(StatsBase).where(GamesVisited.matchId == game_id, StatsBase.region == self.region)
		return game_id not in self.matches_visited_list and not game_query.exists() and creation > 1498608682

	def get_rank(self, summ_id):
		rank = self.api_obj.get_league(summ_id)
		if(len(rank) > 0):
			return rank[0]["tier"]
		return "UNRANKED"

	def get_prelim_match_data(self, participants, match_timeline, game_dur):
		self.player_role_pairs = {"Support":[], "ADC": [], "Top":[], "Mid":[], "Jungle":[]}
		init_pos = match_timeline[2]["participantFrames"]
		index = 0;
		for player in participants:
			role = self.get_role(player, game_dur, init_pos[str(player["participantId"])]["position"])
			self.current_participants_data[player["participantId"]] = {"role": role, 
																		"takedown_points":0, 
																		"win": player["stats"]["win"],
																		"champ": player["championId"],
																		"rating": 0
																		}
			if(role in self.player_role_pairs and len(self.player_role_pairs[role]) < 2):
				self.player_role_pairs[role].append(player)
			if(index < 5):
				team = self.agg_team_stats[100]
			else:
				team = self.agg_team_stats[200]
			team["damage"] += player["stats"]["totalDamageDealtToChampions"]
			team["gold"] += player["stats"]["goldEarned"]
			team["kills"] += player["stats"]["kills"]
			team["rank_weight"] += self.get_rank_weighting(player["highestAchievedSeasonTier"])
			index += 1
		print(" team stats: ", self.agg_team_stats)
		self.agg_team_stats[100]["rank_weight"] = self.agg_team_stats[100]["rank_weight"]/5
		self.agg_team_stats[200]["rank_weight"] = self.agg_team_stats[200]["rank_weight"]/5		

	def add_banned_champs(self, match, desired_rank, patch):
		banned_champs = []
		curr_section = self.leagues[desired_rank]
		for team in match["teams"]:
			for ban in team["bans"]:
				champ_id = ban["championId"]
				if(champ_id not in banned_champs):
					if(champ_id not in curr_section["champions"]):
						curr_section["champions"][champ_id] = ChampionStats(champ_id)	
					curr_section["champions"][champ_id].add_bans(patch, APIConstants.CURRENT_PATCH)
					banned_champs.append(champ_id)

	def add_player(self, acc_id, name, summ_id, curr_player_rank):
		print("rank: ", curr_player_rank)
		if(type(summ_id) is int):
			rank = self.get_rank(summ_id)
			if(rank is "UNRANKED"):
				rank = curr_player_rank
		else:
			rank = summ_id
		new_player = PlayerStats(acc_id, summ_id, name, self.region, rank)
		print(new_player)
		self.players_visited[acc_id] = new_player

	def get_tier_k(self, player_rank):
		print("rank: ", player_rank)
		if(player_rank == "DIAMOND" or player_rank == "diamondPlus" or player_rank == "MASTER" or player_rank == "CHALLENGER"):
			return "diamondPlus"
		elif(player_rank == "BRONZE" or player_rank == "silverMinus" or player_rank == "SILVER"):
			return "silverMinus"
		else:
			return player_rank.lower()


	def process_player_pairs(self, match_details, match_timeline, par, curr_rank, patch):
		for role,pair in self.player_role_pairs.items():
			if(len(pair) == 2):
				self.add_champ(pair[0]["championId"], curr_rank)
				self.add_champ(pair[1]["championId"], curr_rank)
				self.add_champs_data(match_details, {100:pair[0], 200:pair[1]}, curr_rank, role, match_timeline, patch)

	def add_team_stats(self, game_data, league_tier):
		for team in game_data["teams"]:
			cur_team = self.leagues[league_tier]["teams"][team["teamId"]]
			if(team["firstDragon"]):
				cur_team["first_drag"] += 1
			if(team["win"] != "Fail"):
				cur_team["wins"] += 1
			if(team["firstRiftHerald"]):
				cur_team["first_herald"] += 1
			if(team["firstBaron"]):
				cur_team["first_baron"] += 1
			if(team["firstBlood"]):
				cur_team["first_blood"] += 1
			if(team["firstTower"]):
				cur_team["first_tower"] += 1

	def get_role(self, player_data, duration, pos):
		#jungle role hard to pin down, because riot seems to do role aassignments based on location. 
		#mid and support roaming a lot sometimes gets confused as jungler
		spell1 = player_data["spell1Id"]
		spell2 = player_data["spell2Id"]
		champ_tags = self.static.champs_info[player_data["championId"]]["tags"]
		mons_killed_per_min = ((player_data["stats"]["neutralMinionsKilledTeamJungle"] + 
								player_data["stats"]["neutralMinionsKilledEnemyJungle"])/duration)
		if((spell1 == 11 or spell2 == 11) or mons_killed_per_min >= 2.3):
			role = "JUNGLE"
		else:
			role = player_data["timeline"]["lane"]
			if(role == "JUNGLE"):
				#check if the player has smite, and jungle monsters killed
				if(spell1 != 11 and spell2 != 11 and mons_killed_per_min < 2.3):
					if(pos["x"] in self.coords["Bot"]["x"] and pos["y"] in self.coords["Bot"]["y"]):
						if("Support" in champ_tags):
							role = "Support"
						elif("Marksman" in champ_tags):
							role = "ADC"
					elif(pos["x"] in self.coords["Top"]["x"] and pos["y"] in self.coords["Top"]["y"]):
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
		print(self.static.champs_info[player_data["championId"]]["name"], role)
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

	def add_champ(self, champ, desired_rank):
		#print("champ: ", champ)
		#print("tier rank: ", desired_rank)
		if(champ not in self.leagues[desired_rank]["champions"]):
			new_champ = ChampionStats(champ)
			self.leagues[desired_rank]["champions"][champ] = new_champ

	#perhaps split this section, because "add_champs_data" does not fully describe what it does
	def add_champs_data(self, match_details, players, rank, role=None, match_timeline=[], patch="7.16.1"):
		laning_perf = self.analyze_matchup(match_timeline, players[100], players[200], rank, role)
		game_dur = match_details["gameDuration"]/60
		for team,player in players.items():
			print("role: ", role)
			if(team == 200):
				laning_perf = 1 - laning_perf
			champ_id = player["championId"]
			champ_obj = self.leagues[rank]["champions"][champ_id]
			par_id = player["participantId"]
			player_d = match_details["participantIdentities"][par_id-1]["player"]
			acc_id = player_d["currentAccountId"]
			win = 1 if player["stats"]["win"] else 0
			if(team == 100):
				enemy_rank_weight = self.agg_team_stats[200]["rank_weight"]
			else:
				enemy_rank_weight = self.agg_team_stats[100]["rank_weight"]
			weighting = (enemy_rank_weight+self.get_multiplier(rank))/2
			player_perf = self.get_player_performance(player, acc_id, role, team, game_dur, win)
			rating = (player_perf[0]*.5) + (laning_perf*.5)
			oa_rating = rating*weighting
			print("rating: ", rating, " rating with weight: ", oa_rating)
			self.current_participants_data[par_id]["rating"] = oa_rating
			self.add_champ_stats(champ_obj, player, win, role, self.get_kda(player), laning_perf, oa_rating, game_dur, patch)
			champ_obj.add_game_scores(role, player_perf[1], player_perf[2])
			"""
			old
			self.process_timeline(role, match_timeline, player, rank, laning_perf, oa_rating, match_details)
			"""
			self.add_keystone(champ_obj, player, role, win, laning_perf)
			self.add_spells(champ_obj, player, role, win, laning_perf)
			self.add_runes(champ_obj, player, role, win, laning_perf)
			champ_obj.add_skill_order(role, match_timeline, par_id, win, oa_rating)

	def get_multiplier(self, rank):
		if(rank == "CHALLENGER"):
			return 1.7
		elif(rank == "MASTER"):
			return 1.6
		elif(rank == "DIAMOND"):
			return 1.4
		elif(rank == "PLATINUM"):
			return 1.25
		elif(rank == "GOLD" or "UNRANKED"):
			return 1
		else:
			return .9

	def add_players_data(self, player, acc_id, win, oa_rating, t_rating, duration):
		cur_player = self.players_visited[acc_id]
		cur_player.num_games += 1
		cur_player.add_ratings(oa_rating, t_rating)
		cur_player.wpm += player["stats"]["wardsPlaced"]/duration
		cur_player.dpm += player["stats"]["totalDamageDealtToChampions"]/duration
		cur_player.add_wins_loses(win)

	#connect this with player perofrmance
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
		print("objectives damage: ", stats["damageDealtToObjectives"])
		points += ((stats["damageDealtToObjectives"]/game_dur)**.15)*.6
		print("objective points earned: ", points)
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

	def get_rank_weighting(self, rank_tier):
		if(rank_tier == "MASTER" or rank_tier == "CHALLENGER"):
			return 2
		elif(rank_tier == "DIAMOND"):
			return 1.5
		elif(rank_tier == "PLATINUM"):
			return 1.25
		elif(rank_tier == "GOLD"):
			return 1.1
		elif(rank_tier == "SILVER" or "UNRANKED"):
			return .9
		else:
			return .75

	def get_kda(self, player):
		return {"kills": player["stats"]["kills"],
				"deaths": player["stats"]["deaths"],
				"assists": player["stats"]["assists"]}

	def add_keystone(self, champ, player_details, role, win, perf):
		try:
			masteries = player_details["masteries"]
			if(masteries[5]["masteryId"] in self.static.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", masteries[5]["masteryId"])
			elif(masteries[len(masteries)-1]["masteryId"] in self.static.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", masteries[len(masteries)-1]["masteryId"])			
		except:
			KeyError

	def add_spells(self, champ, player_details, role, win, perf):
		if(player_details["spell1Id"] in self.static.spells_info and player_details["spell2Id"] in self.static.spells_info):
			spell_combo_key = player_details["spell1Id"] * player_details["spell2Id"]
			spells = [player_details["spell1Id"], player_details["spell2Id"]]
			champ.add_spells(role, win, perf, spell_combo_key, spells)
			#champ.add_attribute(role, win, perf, "spells", self.static.spells_info[player_details["spell2Id"]])

	def add_runes(self, champ, player_details, role, win, perf):
		runes_left = {"reds":{"left":9, "visited":False}, "blues":{"left":9, "visited":False}, 
					"yellows":{"left":9, "visited":False}, "blacks":{"left":3, "visited":False}}
		rune_group = {}
		if("runes" in player_details):
			for rune in player_details["runes"]:
				if(rune["runeId"] in self.static.runes_info):
					current_rune = self.static.runes_info[rune["runeId"]]
					if(not runes_left[current_rune["type"]]["visited"]):
						rune_group = {}
					runes_left[current_rune["type"]]["left"] -= rune["rank"]
					runes_left[current_rune["type"]]["visited"] = True
					key = rune["runeId"]*rune["rank"]
					rune_group[key] = rune["runeId"]
					if(runes_left[current_rune["type"]]["left"] == 0):
						group_key = 0
						for key,rune_id in rune_group.items():
							group_key += key
						print("runes:? ", rune_group)
						#time.sleep(4)
						champ.add_runes(role, win, perf, rune_group, current_rune["type"], group_key)
						rune_group = {}

	def process_timeline(self, role, timeline, player_details, rank_tier_key, laning, rating, match_details):
		champ_id = player_details["championId"]
		par_id = player_details["participantId"]
		player_win = 1 if player_details["stats"]["win"] else 0
		champ = self.leagues[rank_tier_key]["champions"][champ_id]
		monsters = self.leagues[rank_tier_key]["mons"]
		monsters_added_this_match = []
		for idx,frame in enumerate(timeline[1:]):
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] == par_id and event["type"] == "ITEM_PURCHASED"):
					item_id = event["itemId"]
					if(item_id in self.static.items_info["consumables"]):
						champ.add_item(item_id, role, "consumables", rating, player_win)
					else:
						if(event["timestamp"] < 20000):
							if(item_id in self.static.items_info["start"]):
								champ.add_item(item_id, role, "start", rating, player_win)
						else:
							if(item_id in self.static.items_info["complete"]):			
								self.add_build(item_id, idx, laning, rating, champ, role, player_win)		
				elif(event["type"] == "ELITE_MONSTER_KILL"):
					if(event["killerId"] <= 5):
						team = 100
					else:
						team = 200
					if(team not in monsters):
						monsters[team] = {}
					if(not self.added_monster_stats):
						win = 1 if match_details["participants"][event["killerId"]-1]["stats"]["win"] else 0
						if(event["monsterType"] == "DRAGON" and event["monsterSubType"] == "ELDER_DRAGON"):
							mon = event["monsterSubType"]
						else:
							mon = event["monsterType"]
						if(mon not in monsters_added_this_match):
							self.add_monster(event, monsters[team], win, mon, team)
							monsters_added_this_match.append(mon)
						else:
							self.add_monsters_killed(event, monsters[team], mon, team)
						self.added_monster_stats = True

	def process_match_timeline(self, timeline, rank):
		players_to_items = {}
		monsters = self.leagues[rank]["mons"]
		monsters_added_this_match = []
		print(self.current_participants_data)
		#print(self.player_role_pairs)
		for idx,frame in enumerate(timeline[1:]):
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] > 0):
					par_id = event["participantId"]
					player = self.current_participants_data[par_id]
					player_rating = player["rating"]
					player_win = player["win"]
					role = player["role"]
					#self.add_champ(player["champ"], rank)]
					if(player["champ"] in self.leagues[rank]["champions"]):
						champ = self.leagues[rank]["champions"][player["champ"]]
						if(event["type"] == "ITEM_PURCHASED" and role in champ.roles):
							item_id = event["itemId"]
							if(item_id in self.static.items_info["consumables"]):
								#player["items"]["consumables"].append(item_id) 									
								champ.add_item(item_id, role, "consumables", player_rating, player_win)
							else:
								if(event["timestamp"] < 20000):
									if(item_id in self.static.items_info["start"]):
										#player["items"]["start"].append(item_id)
										champ.add_item(item_id, role, "start", player_rating, player_win)
								else:
									if(item_id in self.static.items_info["complete"]):			
										self.add_complete_items(item_id, idx, player_rating, player_win, role, champ)		
					elif(event["type"] == "ELITE_MONSTER_KILL"):
						if(event["killerId"] <= 5):
							team = 100
						else:
							team = 200
						if(team not in monsters):
							monsters[team] = {}
						win = 1 if match_details["participants"][event["killerId"]-1]["stats"]["win"] else 0
						if(event["monsterType"] == "DRAGON" and event["monsterSubType"] == "ELDER_DRAGON"):
							mon = event["monsterSubType"]
						else:
							mon = event["monsterType"]
						if(mon not in monsters_added_this_match):
							self.add_monster(event, monsters[team], win, mon, team)
							monsters_added_this_match.append(mon)
						else:
							self.add_monsters_killed(event, monsters[team], mon, team)
						self.added_monster_stats = True

	def get_early_takedowns(self, timeline):
		for frame in timeline[1:13]:
			for event in frame["events"]:
				if((event["type"] == "CHAMPION_KILL" or event["type"] == "ELITE_MONSTER_KILL") and event["killerId"] > 0):
					killer_player = self.current_participants_data[event["killerId"]]
					role = killer_player["role"]
					if(role == "ADC" or role == "Support"):
						pos = self.coords["Bot"]
					else:
						pos = self.coords[role]
					print("role: ", role)
					if(event["type"] == "CHAMPION_KILL"):
						if("assistingParticipantIds" in event):
							for assister in event["assistingParticipantIds"]:
								self.current_participants_data[assister]["takedown_points"] += .5
						if(event["position"]["x"] in pos["x"] and event["position"]["y"] in pos["y"]):
							killer_player["takedown_points"] += 1.5
						else:
							killer_player["takedown_points"] += 1
					else:
						if(killer_player["role"] == "Jungle"):
							killer_player["takedown_points"] += 1
						else:
							killer_player["takedown_points"] += 1.5

	def add_complete_items(self, item_id, timeline_idx, rating, win, role, champ_obj):
		complete = self.static.items_info["complete"]
		if("Boots" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "boots", rating, win)
			#player["items"]["boots"].append(item_id)
		elif(item_id in self.static.items_info and "Jungle" in self.static.items_info[item_id]["tags"]):
			#player["items"]["jung_items"].append(item_id)
			champ_obj.add_item(item_id, role, "jung_items", rating, win)
		elif(item_id in self.static.items_info and "Vision" in self.static.items_info[item_id]["tags"]):
			#player["items"]["vis_items"].append(item_id)
			champ_obj.add_item(item_id, role, "vis_items", rating, win)
		elif("CriticalStrike" in complete[item_id]["tags"] and "AttackSpeed" in complete[item_id]["tags"]):
			#player["items"]["attk_speed_items"].append(item_id)
			champ_obj.add_item(item_id, role, "attk_speed_items", rating, win)
		else:
			if(timeline_idx <= 13):
				if(item_id not in champ_obj.roles[role]["build"]["start"]):
					champ_obj.add_item(item_id, role, "early", rating, win)
			else:
				if(self.check_item(champ_obj, item_id, role, "late")):
					champ_obj.add_item(item_id, role, "late", rating, win)

	def add_build(self, item_id, timeline_idx, laning_perf, rating, champ_obj, role, win): #old
		complete = self.static.items_info["complete"]
		if("Boots" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "boots", rating, win)
		elif(item_id in self.static.items_info and "Jungle" in self.static.items_info[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "jung_items", rating, win)
		elif(item_id in self.static.items_info and "Vision" in self.static.items_info[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "vis_items", rating, win)
		elif("CriticalStrike" in complete[item_id]["tags"] and "AttackSpeed" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "attk_speed_items", rating, win)
		else:
			if (timeline_idx <= 13):
				if(laning_perf >= 0):
					status = "early_ahead"
				else:
					status = "early_behind"
				if(item_id not in champ_obj.roles[role]["build"]["start"]):
					champ_obj.add_item(item_id, role, status, rating, win)
			else:
				if(self.check_item(champ_obj, item_id, role, "late")):
					champ_obj.add_item(item_id, role, "late", rating, win)

	def add_monster(self, event, mon_dict, win, monster, team):
		if(monster not in mon_dict):
			if(monster == "DRAGON"):
				mon_dict[monster] = {"time":event["timestamp"]/60000, "killed":1, "games":1, "wins":win, "types":{event["monsterSubType"]:1}}
			else:
				mon_dict[monster] = {"time":event["timestamp"]/60000, "killed":1, "games":1, "wins":win}
		else:
			mon_dict[monster]["wins"] += win
			mon_dict[monster]["time"] += event["timestamp"]/60000
			mon_dict[monster]["killed"] += 1
			mon_dict[monster]["games"] += 1
 
	def add_monsters_killed(self, event, monsters, cur_monster):
		if(cur_monster == "DRAGON"):
			if(event["monsterSubType"] in monsters[cur_monster]["types"]):
				monsters[cur_monster]["types"][event["monsterSubType"]] += 1
			else:
				monsters[cur_monster]["types"][event["monsterSubType"]] = 1
		monsters[cur_monster]["killed"] += 1

	def check_item(self, champ, item_id, role, stage):
		build = champ.roles[role]["build"]
		if(stage == "late"):
			if(item_id not in build["start"] and item_id not in build["early"]):
				return item_id in self.static.items_info["complete"]
			return False
		elif(stage == "start"):
			return item_id in  self.static.items_info["start"]
		elif(stage == "early"):
			if(item_id not in build["start"]):
				return item_id in self.static.items_info["complete"]
			return False

	def add_champ_stats(self, champ, player, win, role, kda, laning, rating, dur, patch):
		#overall stats regardless of role
		champ.add_rating(patch, rating, APIConstants.CURRENT_PATCH)
		champ.add_wins(patch, win, APIConstants.CURRENT_PATCH)
		champ.add_plays(patch, APIConstants.CURRENT_PATCH)
		#role specific stats
		stats = player["stats"]
		gpm = stats["goldEarned"]/dur
		cspm = stats["totalMinionsKilled"]/dur
		if(stats["goldSpent"] > 0):
			dpg = stats["totalDamageDealtToChampions"]/stats["goldSpent"]
			dmpg = stats["damageSelfMitigated"]/stats["goldSpent"]
		else:
			dpg = dmpg = 0
		champ.add_role(role, win, dur, laning, rating, patch)
		champ.add_stat_to_role(role, "kda", kda)
		champ.add_stat_to_role(role, "cspm", cspm)
		champ.add_stat_to_role(role, "gpm", gpm)
		champ.add_stat_to_role(role, "dpg", dpg)
		champ.add_stat_to_role(role, "dmpg", dmpg)
		champ.add_stat_to_role(role, "cc", stats["totalTimeCrowdControlDealt"])
		champ.add_stat_to_role(role, "magic", stats["magicDamageDealtToChampions"])
		champ.add_stat_to_role(role, "physical", stats["physicalDamageDealtToChampions"])
		champ.add_stat_to_role(role, "true", stats["trueDamageDealtToChampions"])

	def get_player_performance(self, player, acc_id, role, team, duration, win):
		cur_team = self.agg_team_stats[team]
		if(win):
			score = 1
		else:
			score = 0
		kda_dict = self.get_kda(player)
		ka = kda_dict["kills"]+kda_dict["assists"]
		deaths = kda_dict["deaths"]
		if(deaths == 0):
			deaths = 1
		kda = ka/deaths  
		if(kda >= 5):
			score += 2
		elif(kda >= 3):
			score += 1.5
		elif(kda >= 1.5):
			score += 1
		score += self.get_team_contribution(player, acc_id, ka, role, cur_team["damage"], cur_team["gold"], cur_team["kills"])		
		obj_sc = self.get_obj_sc(player, duration) 
		vis_sc = self.get_vis_sc(player, duration)	
		score += obj_sc + vis_sc	
		#print("score: ", score)
		return (score/10),obj_sc,vis_sc

	def get_team_contribution(self, player, acc_id, ka, role, team_dmg, team_gold, team_kills):
		score = 0
		if(role == "Support"):
			expected_share = .13
		elif(role == "ADC" or role == "Mid"):
			expected_share = .25
		else:
			expected_share = .16
		kill_par = self.get_player_share(ka, team_kills)[1]
		print("kill participation: ", kill_par)
		if(kill_par >= .75):
			score += 2
		elif(kill_par >= .6):
			score += 1.5
		elif(kill_par >= .35):
			score += 1
		dmg_share = self.get_player_share(player["stats"]["totalDamageDealtToChampions"], team_dmg, expected_share)
		gold_share = self.get_player_share(player["stats"]["goldEarned"], team_gold, expected_share)
		print("damage share: ", dmg_share, " gold share: ", gold_share)
		score += dmg_share[0] + gold_share[0]
		#time.sleep(3)
		return score

	def get_player_share(self, player_stat, team_stat, exp_cont=None):
		print("player: ", player_stat, " team: ", team_stat)
		if(team_stat > 0):
			player_cont = player_stat/team_stat
			if(exp_cont is None):
				return player_stat,player_cont
			if(player_cont >= exp_cont*1.2):
				return 2,player_cont
			elif(player_cont >= exp_cont):
				return 1.5,player_cont
			elif(player_cont >= (exp_cont*.9)):
				return 1,player_cont
			else:
				return .5, player_cont
		return 0,0

	def analyze_matchup(self, timeline, p1, p2, rank, role):
		#print("des rank: ", desired_rank)
		p1_champ = p1["championId"]
		p2_champ = p2["championId"]
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		win = 1.5 if p1["stats"]["win"] else 0
		p1_points = win
		if(p1["participantId"] > p2["participantId"] - 5):
			p1_points += 1
		try:
			if(p1["stats"]["firstTowerAssist"] or p1["stats"]["firstTowerKill"]):
				p1_points += 1
		except:
			KeyError
		t_points = self.current_participants_data[p1["participantId"]]["takedown_points"]
		if(t_points >= 5):
			t_points =  2
		elif(t_points >= 3):
			t_points = 1
		elif(t_points > 0):
			t_points = .5
		else:
			t_points = 0
		print("take down points: ", t_points)
		print("cs/gold lead points: ", self.tally_cs_gold_lead(role, p1, p2))
		p1_points += self.tally_cs_gold_lead(role, p1, p2) 
		p1_points += t_points
		#p1_points += self.tally_kills_smites(timeline, p1["participantId"], p2["participantId"], role)
		print("p1 points: ", p1_points)
		matchup_res = p1_points/4
		#print("matchup result: ", matchup_res)
		self.leagues[rank]["champions"][p1_champ].add_matchup(role, p2_champ, matchup_res, p1["stats"]["win"])
		self.leagues[rank]["champions"][p2_champ].add_matchup(role, p1_champ, -matchup_res, p2["stats"]["win"])
		#time.sleep(4)
		return matchup_res

	def tally_cs_gold_lead(self, role, p1, p2):
		points = 0
		if(role != "JUNGLE"):
			if("csDiffPerMinDeltas" in p1["timeline"]):
				for time in p1["timeline"]["csDiffPerMinDeltas"]:
					if("30" not in time and "20" not in time):
						if(p1["timeline"]["csDiffPerMinDeltas"][time] >= 2):
							points += 2
						elif(p1["timeline"]["csDiffPerMinDeltas"][time] >= 1):
							points += 1
						elif(p1["timeline"]["csDiffPerMinDeltas"][time] >= .5):
							points += .5
		else:
			enemy_camps_dif = p1["stats"]["neutralMinionsKilledEnemyJungle"]-p2["stats"]["neutralMinionsKilledEnemyJungle"]
			team_camps_dif = p1["stats"]["neutralMinionsKilledTeamJungle"]-p2["stats"]["neutralMinionsKilledTeamJungle"]
			if(enemy_camps_dif >= 7 and team_camps_dif >= 7):
				points += .5
			if(enemy_camps_dif >= 10):
				points += 1
			if(team_camps_dif >= 10):
				points += 1
		if("xpDiffPerMinDeltas" in p1["timeline"]):
			for time in p1["timeline"]["xpDiffPerMinDeltas"]:
				if("30" not in time and "20" not in time):
					if(p1["timeline"]["xpDiffPerMinDeltas"][time] >= 100):
						points += 2
					elif(p1["timeline"]["xpDiffPerMinDeltas"][time] >= 50):
						points += 1
		return points

	def get_history(self, acc_id, season = 9, queues=[]):
		return self.api_obj.get_matches_all(acc_id, queues)

	def get_match_details(self, game_id):
		return self.api_obj.get_match_data(game_id)

	def get_champ_tags(self, champ_id):
		return self.api_obj.get_champ_data(champ_id)["tags"]

	def close_db(self):
		self.db.close()

if __name__ == "__main__":
	db = DBHandler()
	print("Number of games: ", GamesVisited.select().count())
	static = CrawlerStaticData(db)
	regions = ["NA", "EUW", "EUNE", "KR", "BR"]
	#lol_crawler = LolCrawler(db, static)			
	start = time.time()
	for i in range(5):
		lol_crawler = LolCrawler(db, static)			
		t = Thread(target=lol_crawler.aggregate_rank_data, args=("silver", 800, regions[i],))
		t.start()
	"""
	lol_crawler.aggregate_rank_data("diamondPlus", 3, "KR")
	"""
	#lol_crawler.aggregate_rank_data("gold", 50, "NA")
	#lol_crawler.aggregate_rank_data("silver", 20, "EUW")
	#lol_crawler.aggregate_rank_data("platinum", 15, "EUW")

	#lol_crawler.aggregate_rank_data()

	#lol_crawler.add_overall_table_stats()
	#lol_crawler1.aggregate_rank_data("diamondPlus", 100, "NA")
	end = time.time()
	print("This took: ", end - start, " seconds.")
	db.close()