import APIConstants, urllib, time, json, requests
import _pickle as cPickle
from multiprocessing import Process
from threading import Thread
from queue import Queue
from random import randint
from championStats import ChampionStats
from playersStats import PlayerStats
from apiCalls import APICalls
#from models import *
#from dbModels import *
from DBHandler import *

#can maybe record most optimal pathing, using match timeline, and also best ward placements
#to do tomorrow use champion base stats to get avg base stats and assign champions either weak/avg/strong/very strong early games/late games, add this to tags perhaps
#also finish champin page and get started on player page(heat map, match history, best champions, etc)
#if time try to improve db and minimizze amount of space used per game recorded
class LolCrawler:
	def __init__(self, db, update_static=False, reset=False):
		self.api_obj = APICalls()
		#initialize_db()
		self.db = db
		print("Number of games: ", GamesVisited.select().count())
		self.init_static_data(update_static)
		self.error_log = open("crawl_error_log.txt", "w")
		#gives the coordinates in the minimap where the champ in its role is expected to be at
		self.coords = {"Top":{"x":range(500,4600),"y":range(9500,14500)},"Mid":{"x":range(5000,9000),"y":range(6000,9500)},
						"Bot":{"x":range(10000,14400),"y":range(600,4500)}, "Jungle":{"x":range(-120,14870),"y":range(-120,14980)}}

	#get he avg base and scaling stat for the entire champion pool
	def get_champ_avgs(self):
		self.champs_avg_stats = {}
		champ_avgs_file = open("champ_stats_avgs.txt", "r")
		for stat in champ_avgs_file:
			data = stat.split(":")
			self.champs_avg_stats[data[0]] = float(data[1])
		champ_avgs_file.close()

	def set_region(self, region):
		self.api_obj.set_region(region)
		self.region = region

	def init_static_data(self, reset=False):
		#default region to NA to get static data since region not set yet
		self.api_obj.set_region("NA")
		self.current_patch = self.api_obj.get_latest_cdn_ver()
		print("current patch: ", self.current_patch)
		champs_data = self.api_obj.get_static_data("champions")["data"]
		#print(champs_data_raw)
		#champs_data = requests.get('http://ddragon.leagueoflegends.com/cdn/7.15.1/data/en_US/champion.json').json()["data"]
		print(champs_data)
		if(reset):
			self.db.clear_static_data()
		"""
		if(self.current_patch != APIConstants.CURRENT_PATCH or reset):
			ChampBase.delete().where(ChampBase.champId != None).execute()
			ItemBase.delete().where(ItemBase.itemId != None).execute()
			self.update_champ_avg_stats(champs_data)
			reset = True
			#APIConstants.CURRENT_PATCH = self.current_patch
		"""
		self.get_champ_avgs()
		self.items_info = self.get_items_data(reset)
		self.keystones_info = self.get_keystones_data(reset)
		self.spells_info = self.get_summ_spells_data(reset)
		self.runes_info = self.get_runes_data(reset)
		self.champs_info = self.get_champs_data(champs_data, reset)
		for champ,data in self.champs_info.items():
			print(data["name"], data["stats_ranking"])

	def get_items_data(self, update):
		temp = {"complete":{}, "trinket":{}, "start":{}, "consumables":{}}
		for item,val in self.api_obj.get_static_data("items")["data"].items():
			item_int = int(item)
			if("maps" in val and val["maps"]["11"] and "name" in val):
				req = val["requiredChamp"] if "requiredChamp" in val else None
				tags = val["tags"] if "tags" in val else [None]
				complete = self.check_item_complete(val)
				if("Consumable" in tags and "consumed" in val):
					temp["consumables"][item_int] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags, "reqChamp":req}
				elif(val["gold"]["total"] <= 500 or "lane" in tags):
					print("starting item: ", val["name"])
					temp["start"][item_int] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags, "reqChamp":req}
				elif("tags" in val and "Trinket" in val["tags"]):
					temp["trinket"][item_int] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags, "reqChamp":req}
				elif(complete):
					temp["complete"][item_int] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags, "reqChamp":req, "from":val["from"]}
				elif("Jungle" in tags or "Sightstone" == val["name"]):
					for complete_item in val["into"]:
						print("complete base: ", complete_item)
						temp[int(complete_item)] = {"name":val["name"], "cost":val["gold"]["total"], "tags":tags, "reqChamp":req}
				if(None in tags):
					tags = None
				if(update):
					self.db.create_item_info(item_int, tags, val)
		return temp

	def check_item_complete(self, info):
		return "into" not in info and ("tags" not in info or "Consumable" not in info["tags"])

	def get_champs_data(self, all_champs_data, update=False):
		temp = {}
		for champ_key,champ in all_champs_data.items():
			stat_scores = self.get_champ_stat_placement(champ)
			stats_rank = {"early":stat_scores[0], "late":stat_scores[1]}
			champ_stats_base = champ["stats"]
			champ_stats_base["attackspeed"] = round(.625/(1+champ_stats_base["attackspeedoffset"]),2)
			del champ_stats_base["attackspeedoffset"]

			temp[champ["id"]] = {"name":champ["name"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"tips":{"enemy":champ["enemytips"], "ally":champ["allytips"]},
								"tags":champ["tags"], "stats_ranking":stats_rank, "stats":champ_stats_base,
								"resource":champ["partype"]
								}
			print(champ["id"])
			if(update):
				self.db.create_champ_info(champ["id"], temp[champ["id"]])
			#when static is down
			"""
			#print(champ_key, champ)
			raw_name = champ["name"]
			print(raw_name)
			if("'" in raw_name):
				print(raw_name)
				if("Kog" not in raw_name and "Rek" not in raw_name):
					split_name = raw_name.split("'")
					name = split_name[0].title() + split_name[1].lower()
					name_key = name
				else:
					name = raw_name.replace("'", "")
					name_key = name
			elif(raw_name == "Fiddlesticks"):
				name = "FiddleSticks"
				name_key = raw_name.title()
			elif("Jarvan" in raw_name):
				name = "JarvanIV"
				name_key = name
			elif("Wukong" in raw_name):
				name = "MonkeyKing"
				name_key = name
			else:
				name = raw_name.title().replace(' ', '')
				if("." in raw_name):
					print(raw_name)
					name = name.title().replace('.', '')

				name_key = name
			print(name)
			champ_id = int(champ["key"])
			champ_extra_info = requests.get('http://ddragon.leagueoflegends.com/cdn/7.15.1/data/en_US/champion/'+name+'.json').json()["data"][name_key]
			print({"enemy":champ_extra_info["enemytips"], "ally":champ_extra_info["allytips"]}, champ_extra_info["spells"], champ_extra_info["passive"])
			temp[champ_id] = {"name":name, "image":champ["image"]["full"], 
								"passive":champ_extra_info["passive"], "abilities":champ_extra_info["spells"], 
								"tips":{"enemy":champ_extra_info["enemytips"], "ally":champ_extra_info["allytips"]},
								"stats_ranking":stats_rank, "tags":champ_extra_info["tags"]
								}
			#print(champ["id"])
			
			if(update):
				self.db.create_champ_info(stats_rank, champ_id, temp[champ_id])
			"""
		return temp

	def get_champ_stat_placement(self, champ_data):
		early_above = self.get_champ_starting_base(champ_data["name"])
		late_above = self.get_champ_late_base(champ_data["name"])
		if("Marksman" in champ_data["tags"]):
			late_above += 1
		for stat,val in champ_data["stats"].items():
			if(stat in self.champs_avg_stats):
				if("perlevel" not in stat):
					if(stat == "attackrange"):
						if("Marksman" not in champ_data["tags"]):
							if(val > self.champs_avg_stats[stat]):
								early_above += 1
						else:
							if(val > self.champs_avg_stats["adc_"+stat]):
								early_above +=1
					elif("mp" in stat):
						if(champ_data["partype"] == "Mana"):
							if(val > self.champs_avg_stats[stat]):
								early_above += 1
						elif(champ_data["partype"] == "Gnarfury"):
							early_above += 1.5
							late_above += 1.5
						else:
							early_above += 1
							late_above += 1
					elif(stat == "attackspeedoffset"):
						if(val < self.champs_avg_stats[stat]):
							early_above += 1
					else:
						if(val > self.champs_avg_stats[stat]):
							early_above += 1
				else:
					if(val > self.champs_avg_stats[stat]):
						late_above += 1
		return early_above, self.get_champ_late_mult(champ_data, late_above)

	def get_champ_late_mult(self, champ, curr_late_points):
		if(champ["name"] in APIConstants.late_game_monsters or champ["name"] == "Gnar"):
			curr_late_points *= 2
		elif(("Marksman" in champ["tags"] and "Fighter" not in champ["tags"]) or champ["name"] in APIConstants.late_game_scalers):
			curr_late_points *= 1.65
		elif("Mage" in champ["tags"][0] and champ["name"] != "Morgana"):
			curr_late_points *= 1.35
		elif("Assassin" in champ["tags"][0]):
			curr_late_points += 1.5
		if(champ["stats"]["attackrange"] <= 175):
			curr_late_points *= .85
		return curr_late_points

	def get_champ_starting_base(self, champ_name):
		if(champ_name in APIConstants.early_game_bullies):
			return 3
		elif(champ_name == "Zilean"):
			return 2
		elif(champ_name == "Nasus"):
			return -4
		elif(champ_name in APIConstants.early_game_eggs):
			return -3
		elif(champ_name in APIConstants.late_game_monsters or champ_name in APIConstants.late_game_scalers):
			return -1.5
		return 1

	def get_champ_late_base(self, champ_name):
		if(champ_name == "Tristana" or champ_name == "Vladimir"):
			return 2.5
		elif(champ_name in APIConstants.late_game_monsters):
			return 2
		elif(champ_name in APIConstants.late_game_scalers):
			return 1.5
		return .5

	def update_champ_avg_stats(self, all_champs_data):
		total_champs_stats = {}
		num_champs_no_mana = 0
		num_adcs = 0
		for champ_key,champ_static_data in all_champs_data.items():
			if(champ_static_data["partype"] != "Mana"):
				num_champs_no_mana += 1
			for stat,val in champ_static_data["stats"].items():
				if("crit" not in stat):
					#print(stat)
					if(stat not in total_champs_stats):
						if(stat == "attackrange"):
							total_champs_stats["adc_"+stat] = 0
							total_champs_stats[stat] = 0
						else:
							total_champs_stats[stat] = 0
					if("mp" in stat):
						if(champ_static_data["partype"] == "Mana"):
							total_champs_stats[stat] += val
					elif(stat == "attackrange"):
						if("Marksman" in champ_static_data["tags"]):
							num_adcs += 1
							total_champs_stats["adc_"+stat] += val
						else:
							total_champs_stats[stat] += val		
					elif(stat == "armorperlevel"):
						if(champ_static_data["name"] != "Tresh"):
							total_champs_stats[stat] += val	
					else:
						total_champs_stats[stat] += val		
		self.write_champ_stat_avg(total_champs_stats, num_champs_no_mana, num_adcs, len(all_champs_data))

	def write_champ_stat_avg(self, data, num_no_mana, num_adcs, num_champs):
		champ_avgs_file = open("champ_stats_avgs.txt", "w")
		print("num no mana champs: ", num_no_mana)
		for stat,val in data.items():
			if("mp" not in stat):
				if(stat == "adc_attackrange"):
					champ_avgs_file.write(stat + ":" + str(val/num_adcs) + '\n')
				elif(stat == "attackrange"):
					champ_avgs_file.write(stat + ":" + str(val/(num_champs-num_adcs)) + '\n')
				elif(stat == "armorperlevel"):
					champ_avgs_file.write(stat + ":" + str(val/(num_champs-1)) + '\n')
				else:
					champ_avgs_file.write(stat + ":" + str(val/num_champs) + '\n')
			else:
				champ_avgs_file.write(stat + ":" + str(val/(num_champs-num_no_mana)) + '\n')
		champ_avgs_file.close()

	def get_keystones_data(self, update=False):
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
				if(update):
					self.db.create_mastery_info(mastery_id, info)
		return temp

	def get_runes_data(self, update):
		temp = {}
		for rune_id,data in self.api_obj.get_static_data("runes")["data"].items():
			if("Greater" in data["name"]):
				if("mark" in data["tags"]):
					temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"], "type":"reds"}
				elif("glyph" in data["tags"]):
					temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"], "type":"blues"}
				elif("seal" in data["tags"]):
					temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"], "type":"yellows"}
				elif("quintessence" in data["tags"]):
					temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"], "type":"blacks"}
				if(update):
					self.db.create_rune_info(data)
		return temp

	def get_summ_spells_data(self, update):
		temp = {}
		for spell,data in self.api_obj.get_static_data("summoner-spells")["data"].items():
			if("CLASSIC" in data["modes"]):
				temp[data["id"]] = {"name":data["name"], "id":data["id"], "image":data["image"]["full"], "des":data["description"]}
				if(update):
					self.db.create_spell_info(data["id"], temp[data["id"]])
		return temp
	
	def close_err_log(self):
		self.error_log.close()

	def add_data_to_db(self):
		self.db.add_games_visited_db(self.matches_visited_list, self.matches_visited)
		for league in self.leagues:
			champs = self.leagues[league]["champions"]
			if(len(champs) > 0):
				stats_base_mod = self.db.create_base_info(self.region, league)

				print(league)
				#print(self.leagues[league])
				if("game_dur" in self.leagues[league]):
					game_l = self.leagues[league]["game_dur"]
				else:
					game_l = 0
				self.db.add_monsters_db(self.leagues[league]["mons"], league, self.region, stats_base_mod)
				self.db.add_teams_db(self.leagues[league]["teams"], game_l, league, self.region, len(self.remakes), stats_base_mod)
				self.db.add_champ_stats(champs, APIConstants.CURRENT_PATCH, stats_base_mod)

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
			self.crawl_history(None, None, [[2558586644, 2558272413], ["GOLD", "DIAMOND"]])
		else:
			if(desired_rank == "diamondPlus"):
				league_players = self.api_obj.get_master_players()
			elif(desired_rank in APIConstants.STARTING_PLAYERS[self.region]):
				league_players = self.api_obj.get_league(APIConstants.STARTING_PLAYERS[self.region][desired_rank])[0]
			else:
				return "Invalid Parameters"
			self.crawl_history(league_players, num_matches)

		self.add_data_to_db()
		#self.add_gamed_visited_db()
		#self.add_players_db()
		end = time.time()
		"""
		stats_txt = open("champ_stats.txt", "w")
		for league,metrics in self.leagues.items():
			for champion,stats in metrics["champions"].items():
				stats_txt.write(str(stats.champ_id) + "\n")
				for role,info in stats.roles.items():
					print("t plays: ", stats.t_plays)
					try:
						stats_txt.write("dpg: " + str(info["damage_dealt_per_gold"]) + " dmpg " + str(info["damage_mitigated_per_gold"]) + " plays: " + str(info["patches_stats"]))
					except:
						KeyError
					#time.sleep(2) 
					stats_txt.write("\n")
		"""
		print("Searching ", len(self.matches_visited_list), " matches took: ", end - start, " seconds.")

	def close_db(self):
		self.db.close()
		self.error_log.close()

	def crawl_history(self, league, num_matches, matches_supplied=None, season=9, q=420):
		if(matches_supplied is None):
			self.rank_tiers_vis.append(league["tier"] + " " + league["name"])
			player_leagues_to_visit = []
			for player in league["entries"]:
				if(len(self.matches_visited_list) < num_matches):
					player_data = self.api_obj.get_summoner_by_summid(player["playerOrTeamId"])
					print("player: ", player["playerOrTeamName"])
					acc_id = player_data["accountId"]
					if(acc_id not in self.players_visited):
						self.add_player(acc_id, player_data["name"], player_data["id"], league["tier"])
					if(acc_id not in self.mh_visited and len(self.matches_visited_list) < num_matches):
						print(player_data["name"], " ", acc_id, " ", league["tier"])
						self.mh_visited.append(acc_id)
						match_history = self.get_history(acc_id, season, q)
						#matches_queue = Queue()
						for match in match_history:
							#matches_queue.put(match)
							game_id = match["gameId"]
							if(len(self.matches_visited_list) < num_matches):
								if(self.check_game(game_id, match["timestamp"]/1000)):
									print(len(self.matches_visited_list), "/", num_matches)
									print("game id :", game_id)
									match_details = self.get_match_details(game_id)
									if(match_details is not None):
										if(len(player_leagues_to_visit) < 2):
											player_leagues_to_visit.append(match_details["participantIdentities"])
										#1496197986 is june 1st
										game_creation_time = match_details["gameCreation"]/1000
										print("game created at: ", game_creation_time)
										if(match_details is not None):
											if(game_creation_time >= 1502204294):
												patch = "7.16.1"											
											elif(game_creation_time >= 1501082571):
												patch = "7.15.1"
											elif(game_creation_time >= 1499875845):
												patch = "7.14.1"
											elif(game_creation_time >= 1498608682):
												patch = "7.13.1"
											elif(game_creation_time >= 1497399082):
												patch = "7.12.1"										
											tier = self.get_tier_k(league["tier"])
											self.matches_visited.append({"matchId":game_id, "patch":patch, "baseInfo":self.db.create_base_info(self.region,tier)})
											self.matches_visited_list.append(game_id)
											print("315 tier: ", tier)
											if(match_details["gameDuration"] < 300):
												self.remakes.append(game_id)
											else:
												self.add_banned_champs(match_details, tier, patch)
												match_timeline = self.api_obj.get_match_timeline(game_id)
												if(match_timeline is not None):
													par = match_details["participants"]
													self.added_monster_stats = False
													self.get_team_stats(par)
													self.process_player_pairs(match_details, match_timeline, par, tier, patch)
													self.add_team_stats(match_details, tier)
													if("game_dur" not in self.leagues[tier]):
														self.leagues[tier]["game_dur"] = match_details["gameDuration"]/60
													else:
														self.leagues[tier]["game_dur"] += match_details["gameDuration"]/60
										else:
											break
							else:
								break
			#print("players to visit: ", player_leagues_to_visit)							
			for player in player_leagues_to_visit.pop():
				print("p: ", player)
				if(len(self.matches_visited_list) < num_matches):
					acc_id = player["player"]["currentAccountId"]
					if(acc_id not in self.players_visited):
						rank = self.api_obj.get_league(player["player"]["summonerId"])[0]
						print((rank["tier"] + " " + rank["name"]))
						if((rank["tier"] + " " + rank["name"]) not in self.rank_tiers_vis):
							self.crawl_history(rank, num_matches)
		else:
			index = 0
			for match in matches_supplied[0]:
				match_details = self.get_match_details(match)
				if(self.check_game(match, match_details["gameCreation"]/1000)):
					#print(len(self.matches_visited_list), "/", num_matches)
					print("game id :", match)
					if(match_details is not None):
						#1496197986 is june 1st
						game_creation_time = match_details["gameCreation"]/1000
						print("game created at: ", game_creation_time)
						if(match_details is not None):
							if(game_creation_time >= 1502204294):
								patch = "7.16.1"
							elif(game_creation_time >= 1501082571):
								patch = "7.15.1"
							elif(game_creation_time >= 1499875845):
								patch = "7.14.1"
							elif(game_creation_time >= 1498608682):
								patch = "7.13.1"									
							tier = self.get_tier_k(matches_supplied[1][index])
							self.matches_visited.append({"matchId":match, "patch":patch, "baseInfo":self.db.create_base_info(self.region,tier)})
							self.matches_visited_list.append(match)
							print("315 tier: ", tier)
							if(match_details["gameDuration"] < 300):
								self.remakes.append(match)
							else:
								self.add_banned_champs(match_details, tier, patch)
								match_timeline = self.api_obj.get_match_timeline(match)
								if(match_timeline is not None):
									par = match_details["participants"]
									self.added_monster_stats = False
									self.get_team_stats(par)
									self.process_player_pairs(match_details, match_timeline, par, tier, patch)
									self.add_team_stats(match_details, tier)
									if("game_dur" not in self.leagues[tier]):
										self.leagues[tier]["game_dur"] = match_details["gameDuration"]/60
									else:
										self.leagues[tier]["game_dur"] += match_details["gameDuration"]/60
							index += 1
						else:
							break			

	def check_game(self, game_id, creation):
		#print("creating time: ", creation)
		game_query = GamesVisited.select().join(StatsBase).where(GamesVisited.matchId == game_id, StatsBase.region == self.region)
		return game_id not in self.matches_visited_list and not game_query.exists() and creation > 1498608682

	def get_rank(self, summ_id):
		rank = self.api_obj.get_league(summ_id)
		if(len(rank) > 0):
			return rank[0]["tier"]
		return "UNRANKED"

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
		#note blue team consists of players with par ids 1-5, while red team is players from 5-10
		#record blue and red win rate by patch, by league tier
		picked_players = []
		game_id = match_details["gameId"]
		game_dur = match_details["gameDuration"]/60
		init_pos = match_timeline["frames"][2]["participantFrames"]
		par_idts = match_details["participantIdentities"]
		for i in range(0, 5):
			p1 = par[i]
			p1_acc_id = par_idts[i]["player"]["currentAccountId"]
			print("p1 id: ", p1_acc_id)
			if(p1_acc_id not in self.players_visited):
				self.add_player(p1_acc_id, par_idts[i]["player"]["summonerName"], par_idts[i]["player"]["summonerId"], curr_rank)
			p1_rank = self.players_visited[p1_acc_id].currentRank
			if(p1_rank is None):
				p1_rank = curr_rank
			p2 = None
			timeline = match_timeline["frames"]
			p1_tier_key = self.get_tier_k(p1_rank)
			self.add_champ(p1["championId"], p1_tier_key)
			p1_role = self.get_role(p1, game_id, game_dur, init_pos[str(p1["participantId"])]["position"])
			for j in range(5, 10):
				#print(role, " vs ", self.get_role(participants[j], game_id, avbl_roles))
				if(j not in picked_players):
					p2_role = self.get_role(par[j], game_id, game_dur, init_pos[str(par[j]["participantId"])]["position"]) 
					print("p1 champ ", self.champs_info[p1["championId"]]["name"], " role: ", p1_role, " vs p2 champ ", self.champs_info[par[j]["championId"]]["name"], " role: ", p2_role)
					if(p2_role == p1_role):
						p2_acc_id = par_idts[j]["player"]["currentAccountId"]
						if(p2_acc_id not in self.players_visited):
							self.add_player(p2_acc_id, par_idts[j]["player"]["summonerName"], par_idts[j]["player"]["summonerId"], curr_rank)
						p2_rank = self.players_visited[p2_acc_id].currentRank
						if(p2_rank is None):
							p2_rank = curr_rank
						p2 = par[j]
						print("p2 acc id: ", p2_acc_id)
						picked_players.append(j) 
						break
			if(p2 is not None):
				p2_tier_key = self.get_tier_k(p2_rank)
				self.add_champ(p2["championId"], p2_tier_key)
				self.add_champs_data(match_details, {100:[p1,p1_rank,p1_tier_key], 200:[p2,p2_rank,p2_tier_key]}, p1_role, timeline, patch)
				#print("build for: ", champ_name, " - ", self.leagues[rank]["champions"][champ_name].get_items())	
			else:
				print("no pair for: ", p1["championId"])

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

	def get_role(self, player_data, match_id, duration, pos):
		#jungle role hard to pin down, because riot seems to do role aassignments based on location. 
		#mid and support roaming a lot sometimes gets confused as jungler
		spell1 = player_data["spell1Id"]
		spell2 = player_data["spell2Id"]
		champ_tags = self.champs_info[player_data["championId"]]["tags"]
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
	def add_champs_data(self, match_details, players, role=None, match_timeline=[], patch="7.16.1"):
		laning_perf = self.analyze_matchup(match_timeline, players[100][0], players[200][0], players[100][2], players[200][2], role)
		game_dur = match_details["gameDuration"]/60
		for team,player in players.items():
			if(team == 200):
				laning_perf = 1 - laning_perf
			champ_id = player[0]["championId"]
			tier_k = player[2]
			par_details = player[0]
			champ_obj = self.leagues[tier_k]["champions"][champ_id]
			par_id = par_details["participantId"]
			player_d = match_details["participantIdentities"][par_id-1]["player"]
			acc_id = player_d["currentAccountId"]
			win = 1 if par_details["stats"]["win"] else 0
			if(team == 100):
				enemy_rank_weight = self.teams[200]["rank_weight"]
			else:
				enemy_rank_weight = self.teams[100]["rank_weight"]
			weighting = (enemy_rank_weight+self.get_multiplier(player[1]))/2
			player_perf = self.get_player_performance(match_timeline, par_details, acc_id, role, team, game_dur, win)
			rating = (player_perf[0]*.5) + (laning_perf*.5)
			oa_rating = rating*weighting

			self.add_players_data(par_details, acc_id, win, oa_rating, rating, game_dur)
			self.players_visited[acc_id].add_champ(champ_id, win, player_perf[0])
			self.add_champ_stats(champ_obj, par_details, win, role, self.get_kda(par_details), laning_perf, oa_rating, game_dur, patch)
			champ_obj.add_player(acc_id, 
				player_d["summonerName"], 
				win, 
				self.get_kda(par_details), 
				player_perf[0], 
				role, 
				self.players_visited[acc_id].currentRank,
				self.players_visited[acc_id].summ_id
				)
			champ_obj.add_game_scores(role, player_perf[1], player_perf[2])
			self.process_timeline(role, match_timeline, par_details, tier_k, laning_perf, oa_rating, match_details)
			self.add_keystone(champ_obj, par_details, role, win, laning_perf)
			self.add_spells(champ_obj, par_details, role, win, laning_perf)
			self.add_player_runes(champ_obj, par_details, role, win, laning_perf)
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
		points = .5 if stats["win"] else 0
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

	def get_team_stats(self, participants):
		self.teams = {100: {"kills":0, "gold":0, "damage":0, "rank_weight":0}, 
					200:{"kills":0, "gold":0, "damage":0, "rank_weight":0}}
		for i in range(10):
			if(i < 5):
				team = self.teams[100]
			else:
				team = self.teams[200]
			team["damage"] += participants[i]["stats"]["totalDamageDealtToChampions"]
			team["gold"]  += participants[i]["stats"]["goldEarned"]
			team["kills"]  += participants[i]["stats"]["kills"]
			team["rank_weight"] += self.get_rank_weighting(participants[i]["highestAchievedSeasonTier"])
		self.teams[100]["rank_weight"] = self.teams[100]["rank_weight"]/5
		self.teams[200]["rank_weight"] = self.teams[200]["rank_weight"]/5

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
			if(masteries[5]["masteryId"] in self.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", masteries[5]["masteryId"])
			elif(masteries[len(masteries)-1]["masteryId"] in self.keystones_info):
				champ.add_attribute(role, win, perf, "keystone", masteries[len(masteries)-1]["masteryId"])			
		except:
			KeyError

	def add_spells(self, champ, player_details, role, win, perf):
		if(player_details["spell1Id"] in self.spells_info and player_details["spell2Id"] in self.spells_info):
			spell_combo_key = player_details["spell1Id"] * player_details["spell2Id"]
			spells = [player_details["spell1Id"], player_details["spell2Id"]]
			champ.add_spells(role, win, perf, spell_combo_key, spells)
			#champ.add_attribute(role, win, perf, "spells", self.spells_info[player_details["spell2Id"]])

	def add_player_runes(self, champ, player_details, role, win, perf):
		runes_left = {"reds":{"left":9, "visited":False}, "blues":{"left":9, "visited":False}, 
					"yellows":{"left":9, "visited":False}, "blacks":{"left":3, "visited":False}}
		rune_group = {}
		if("runes" in player_details):
			for rune in player_details["runes"]:
				if(rune["runeId"] in self.runes_info):
					current_rune = self.runes_info[rune["runeId"]]
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
					if(item_id in self.items_info["consumables"]):
						champ.add_item(item_id, role, "consumables", rating, player_win)
					else:
						if(event["timestamp"] < 20000):
							if(item_id in self.items_info["start"]):
								champ.add_item(item_id, role, "start", rating, player_win)
						else:
							if(item_id in self.items_info["complete"]):			
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

	def process_timeline_2(self, timeline, player_details):
		players_to_items = {}
		champ_id = player_details["championId"]
		par_id = player_details["participantId"]
		player_win = 1 if player_details["stats"]["win"] else 0
		champ = self.leagues[rank_tier_key]["champions"][champ_id]
		monsters = self.leagues[rank_tier_key]["mons"]
		monsters_added_this_match = []
		for idx,frame in enumerate(timeline[1:]):
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] == par_id and event["type"] == "ITEM_PURCHASED"):
					if(event["type"] == "ITEM_PURCHASED"):
						if(event["participantId"] not in players_to_items):
							players_to_items[event["participantId"]] = {
							"consumables":[], 
							"start":[], 
							"complete":[], 
							"boots":[],
							"jung_items":[],
							"vis_items":[],
							"attk_speed_items":[],
							"early_ahead":[],
							"early_behind":[],
							"late":[]
							}
						item_id = event["itemId"]
						if(item_id in self.items_info["consumables"]):
							if("consumables" not in players_to_items[event["participantId"]]):
								players_to_items[event["participantId"]]["consumables"].append(item_id) 							
								champ.add_item(item_id, role, "consumables", rating, player_win)
						else:
							if(event["timestamp"] < 20000):
								if(item_id in self.items_info["start"]):
									champ.add_item(item_id, role, "start", rating, player_win)
							else:
								if(item_id in self.items_info["complete"]):			
									self.add_build(item_id, idx, laning, rating, champ, role, player_win)		
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


	def add_build(self, item_id, timeline_idx, laning_perf, rating, champ_obj, role, win):
		complete = self.items_info["complete"]
		if("Boots" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "boots", rating, win)
		elif(item_id in self.items_info and "Jungle" in self.items_info[item_id]["tags"]):
			champ_obj.add_item(item_id, role, "jung_items", rating, win)
		elif(item_id in self.items_info and "Vision" in self.items_info[item_id]["tags"]):
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
			if(item_id not in build["start"] and item_id not in build["early_ahead"] and item_id not in build["early_behind"]):
				return item_id in self.items_info["complete"]
			return False
		elif(stage == "start"):
			return item_id in  self.items_info["start"]
		elif(stage == "early_ahead" or stage == "early_behind"):
			if(item_id not in build["start"]):
				return item_id in self.items_info["complete"]
			return False

	def add_champ_stats(self, champ, player, win, role, kda, laning, rating, dur, patch):
		#print("player: ", player)
		champ.add_kda(kda)
		champ.add_rating(patch, rating, APIConstants.CURRENT_PATCH)
		champ.add_wins(patch, win, APIConstants.CURRENT_PATCH)
		champ.add_plays(patch, APIConstants.CURRENT_PATCH)
		stats = player["stats"]
		gpm = stats["goldEarned"]/dur
		cspm = stats["totalMinionsKilled"]/dur
		if(stats["goldSpent"] > 0):
			dpg = stats["totalDamageDealtToChampions"]/stats["goldSpent"]
			dmpg = stats["damageSelfMitigated"]/stats["goldSpent"]
		else:
			dpg = dmpg = 0
		#print("damage mitigated: ", stats["damageSelfMitigated"], " gold earned: ", stats["goldEarned"])
		champ.add_role(role, win, dur, kda, dpg, 
			dmpg, laning, rating, patch)
		champ.add_cspm(role, cspm)
		champ.add_gpm(role, gpm)
		champ.add_cc_dealt(role, stats["totalTimeCrowdControlDealt"])

	def get_player_performance(self, timeline, player, acc_id, role, team, duration, win):
		cur_team = self.teams[team]
		if(win):
			score = 2
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
			score += 1.6
		elif(kda >= 1.5):
			score += 1.3
		score += self.get_team_contribution(player, acc_id, ka, role, cur_team["damage"], cur_team["gold"], cur_team["kills"])
		obj_sc = self.get_obj_sc(player, duration)
		vis_sc = self.get_vis_sc(player, duration)
	
		player = self.players_visited[acc_id]
		player.add_obj_score(obj_sc)
		player.add_vis_score(vis_sc)
		player.add_kills_stats(kda_dict, kda)
		score += obj_sc + vis_sc
		#print("score: ", score)
		return (score/11),obj_sc,vis_sc

	def get_team_contribution(self, player, acc_id, ka, role, team_dmg, team_gold, team_kills):
		score = 0
		if(role == "Support"):
			expected_share = .12
		elif(role == "ADC" or role == "Mid"):
			expected_share = .25
		else:
			expected_share = .18
		kill_par = self.get_player_share(ka, team_kills)[1]
		print("kill participation: ", kill_par)
		if(kill_par >= .7):
			score += 2
		elif(kill_par >= .6):
			score += 1.5
		elif(kill_par >= .4):
			score += 1
		dmg_share = self.get_player_share(player["stats"]["totalDamageDealtToChampions"], team_dmg, expected_share)
		gold_share = self.get_player_share(player["stats"]["goldEarned"], team_gold, expected_share)
		score += dmg_share[0] + gold_share[0]

		self.players_visited[acc_id].kp += kill_par
		self.players_visited[acc_id].add_damage_share(dmg_share[1])
		self.players_visited[acc_id].add_gold_share(gold_share[1])
		return score

	def get_player_share(self, player_stat, team_stat, exp_cont=None):
		if(team_stat > 0):
			player_cont = player_stat/team_stat
			if(exp_cont is None):
				return player_stat,player_cont
			if(player_cont > exp_cont*1.2):
				return 2,player_cont
			elif(player_cont > exp_cont):
				return 1.5,player_cont
			elif(player_cont >= (exp_cont*.9)):
				return 1,player_cont
		return 0,0

	def analyze_matchup(self, timeline, p1, p2, t1, t2, role):
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
		p1_points += self.tally_cs_gold_lead(role, p1, p2) 
		p1_points += self.tally_kills_smites(timeline, p1["participantId"], p2["participantId"], role)
		matchup_res = p1_points/5
		#print("matchup result: ", matchup_res)
		self.leagues[t1]["champions"][p1_champ].add_matchup(role, p2_champ, matchup_res, p1["stats"]["win"])
		self.leagues[t2]["champions"][p2_champ].add_matchup(role, p1_champ, -matchup_res, p2["stats"]["win"])
		return matchup_res

	def tally_cs_gold_lead(self, role, p1, p2):
		points = 0
		if(role != "JUNGLE"):
			if("csDiffPerMinDeltas" in p1["timeline"]):
				for time in p1["timeline"]["csDiffPerMinDeltas"]:
					if("30" not in time and "20" not in time):
						if(p1["timeline"]["csDiffPerMinDeltas"][time] >= 2):
							points += 2
						elif(p1["timeline"]["csDiffPerMinDeltas"][time] > 1):
							points += 1
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

	def tally_kills_smites(self, timeline, p1_id, p2_id, role):
		#print("role: ", role)
		if(role == "ADC" or role == "Support"):
			pos = self.coords["Bot"]
		else:
			pos = self.coords[role]
		points = 0
		for frame in timeline[1:13]:
			for event in frame["events"]:
				points += self.get_early_kills(event, p1_id, pos) + self.get_monster_kills(event, p1_id, role)
		return points

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
		if(kill_points >= 5):
			return 2
		elif(kill_points >= 3):
			return 1
		elif(kill_points > 0):
			return .5
		else:
			return 0

	def get_monster_kills(self, timeframe, player_id, role):
		obj_points = 0
		if(timeframe["type"] == "ELITE_MONSTER_KILL"):
			if(timeframe["killerId"] == player_id):
				obj_points += 1 if role == "JUNGLE" else .5
			else:
				obj_points -= .5 if role == "JUNGLE" else 0
		if(obj_points >= 1):
			return 1.5
		elif(obj_points > 0):
			return 1	
		else:
			return 0

	def get_history(self, acc_id, season = 9, queues=[]):
		return self.api_obj.get_matches_all(acc_id, queues)["matches"]

	def get_match_details(self, game_id):
		return self.api_obj.get_match_data(game_id)

	def get_champ_tags(self, champ_id):
		return self.api_obj.get_champ_data(champ_id)["tags"]

	def add_overall_table_stats(self):
		all_champ_role_stats = ChampOverallStatsByRole.select().join(ChampStatsByRank).join(StatsBase).order_by(StatsBase.region)
		data = {}
		#champ_file = open("champ_overall_by_region.txt", "w")
		for champ_role_stats in all_champ_role_stats:
			region = champ_role_stats.stats_by_rank.get().baseInfo.region 
			if(region not in data):
				data[region] = {}
			champ = champ_role_stats.stats_by_rank.get().champId
			print(region, champ)
			if(champ not in data[region]):
				data[region][champ] = {}
			if("totalBansByPatch" not in data[region][champ]):
				data[region][champ]["totalBansByPatch"] = cPickle.loads(champ_role_stats.totalBansByPatch)
			if("totalPlaysByPatch" not in data[region][champ]):
				data[region][champ]["totalPlaysByPatch"] = cPickle.loads(champ_role_stats.totalPlaysByPatch)
			if("totalRating" not in data[region][champ]):
				data[region][champ]["totalRating"] = champ_role_stats.roleTotalRating
			else:
				data[region][champ]["totalRating"] += champ_role_stats.roleTotalRating
			if("totalWins" not in data[region][champ]):
				data[region][champ]["totalWins"] = champ_role_stats.roleTotalWins
			else:
				data[region][champ]["totalWins"] += champ_role_stats.roleTotalWins

		for champ_role_stats in all_champ_role_stats:
			champ = champ_role_stats.stats_by_rank.get().champId
			region = champ_role_stats.stats_by_rank.get().baseInfo.region 
			league = champ_role_stats.stats_by_rank.get().baseInfo.leagueTier
			overall_q = ChampOverallStats.select().where(
				ChampOverallStats.region == region,
				ChampOverallStats.champId == champ				
				)
			if(not overall_q.exists()):
				overall = ChampOverallStats.create(
							totalRating = data[region][champ]["totalRating"],
							totalBansByPatch = cPickle.dumps(data[region][champ]["totalBansByPatch"]),
							totalPlaysByPatch = cPickle.dumps(data[region][champ]["totalPlaysByPatch"]),
							totalWins = data[region][champ]["totalWins"],
							region = region,
							champId = champ
							)		
			else:
				overall = overall_q.get()
			role_overall_q = ChampOverallStatsByRole.select().where(ChampOverallStatsByRole.region == region, ChampOverallStatsByRole.champId == champ, ChampOverallStatsByRole.role == champ_role_stats.role)
			if(not role_overall_q.exists()):
				role_overall = ChampOverallStatsByRole.create(
								role = champ_role_stats.role,
								roleTotalPlays = champ_role_stats.roleTotalPlays,
								roleTotalWins = champ_role_stats.roleTotalWins,
								roleCCDealt = champ_role_stats.roleCCDealt,
								roleTotalRating = champ_role_stats.roleTotalRating,
								overall = overall,
								addons = champ_role_stats.addons,
								region = region,
								champId = champ
								)
			else:
				role_overall = role_overall_q.get()
			for rank_tier in champ_role_stats.stats_by_rank:
				print(rank_tier.champId, rank_tier.overallStats.role, region, league, rank_tier.baseInfo.leagueTier, champ_role_stats.role)
				champ_rank_stats_q = ChampStatsByRank.select().join(StatsBase).switch(ChampStatsByRank).join(ChampOverallStatsByRole).where(
					ChampStatsByRank.champId == rank_tier.champId, 
					StatsBase.region == region, 
					StatsBase.leagueTier == rank_tier.baseInfo.leagueTier, 
					ChampOverallStatsByRole.role == champ_role_stats.role)
				if(not champ_rank_stats_q.exists()):
					print("added")
					ChampStatsByRank.create(
						champId = rank_tier.champId,
						baseInfo = rank_tier.baseInfo,
						overallStats = role_overall,
						gameStats = rank_tier.gameStats,
						patchStats = rank_tier.patchStats,
						kills = rank_tier.kills,
						deaths = rank_tier.deaths,
						assists = rank_tier.assists,
						cspm = rank_tier.cspm,
						gpm = rank_tier.gpm,
						resultByTime = rank_tier.resultByTime
					)
				else:
					d = champ_rank_stats_q.get()
					print(d.champId, d.baseInfo.leagueTier, d.baseInfo.region)
				#time.sleep(2)	
		"""
		for region,champs in data.items():
			for champ,stats in champs.items():
				#print(champ, "\n")
				champ_file.write(region + "-" + str(champ) + "-" + str(stats["totalBansByPatch"]) + "-" + str(stats["totalPlaysByPatch"]) + "-" + str(stats["totalRating"]) + "\n")
		champ_file.close()
		"""
def test(ind):
	print("process1")
	for i in range(ind, 10):
		print(i)
		time.sleep(2)	

def test2():
	print("process2")
	for i in range(20,30):
		print(i)		

if __name__ == "__main__":
	db = DBHandler()
	lol_crawler1 = LolCrawler(db)
	lol_crawler2 = LolCrawler(db)
	lol_crawler3 = LolCrawler(db)
	lol_crawler4 = LolCrawler(db)

	#lol_crawler.aggregate_rank_data("gold", 50, "NA")
	#lol_crawler.aggregate_rank_data("silver", 20, "EUW")
	#lol_crawler.aggregate_rank_data("platinum", 15, "EUW")

	#lol_crawler.aggregate_rank_data()

	#lol_crawler.add_overall_table_stats()
	#lol_crawler1.aggregate_rank_data("diamondPlus", 100, "NA")

	Thread(target=lol_crawler1.aggregate_rank_data, args=("silver", 150, "KR",)).start()
	Thread(target=lol_crawler3.aggregate_rank_data, args=("silver", 200, "NA",)).start()
	Thread(target=lol_crawler4.aggregate_rank_data, args=("silver", 210, "EUW",)).start()	
	Thread(target=lol_crawler4.aggregate_rank_data, args=("platinum", 210, "EUNE",)).start()	

	"""
	#lol_crawler.aggregate_rank_data()
	#lol_crawler.aggregate_rank_data("silver", 100, "EUW")

	#lol_crawler.aggregate_rank_data("platinum", 90, "NA")

	#lol_crawler.aggregate_rank_data("gold", 200, "KR")

	lol_crawler.aggregate_rank_data("diamondPlus", 500, "NA")
	lol_crawler.aggregate_rank_data("silver", 500, "NA")
	lol_crawler.aggregate_rank_data("gold", 500, "NA")

	lol_crawler.aggregate_rank_data("diamondPlus", 200, "EUW")
	lol_crawler.aggregate_rank_data("bronze", 200, "EUW")
	lol_crawler.aggregate_rank_data("gold", 200, "EUW")

	lol_crawler.aggregate_rank_data("gold", 300, "EUNE")
	lol_crawler.aggregate_rank_data("platinum", 300, "EUNE")
	lol_crawler.aggregate_rank_data("diamondPlus", 300, "EUNE")

	lol_crawler.aggregate_rank_data("platinum", 300, "KR")
	lol_crawler.aggregate_rank_data("platinum", 200, "KR")
	lol_crawler.aggregate_rank_data("gold", 200, "KR")
	lol_crawler.aggregate_rank_data("bronze", 200, "KR")

	#lol_crawler.update_visited_games()

	lol_crawler.aggregate_rank_data("diamondPlus", 100, "EUW")
	lol_crawler.aggregate_rank_data("platinum", 100, "EUW")
	lol_crawler.aggregate_rank_data("silver", 100, "EUW")

	lol_crawler.aggregate_rank_data("diamondPlus", 500, "NA")
	lol_crawler.aggregate_rank_data("bronze", 300, "NA")
	lol_crawler.aggregate_rank_data("gold", 350, "NA")

	#lol_crawler.add_player_rank()
	print(GamesVisited.select().count())
	"""
	db.close()