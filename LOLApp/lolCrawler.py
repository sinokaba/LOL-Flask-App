import APIConstants, urllib, time, logging, ast
import _pickle as cPickle
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
	def __init__(self, update_static=False, reset=False):
		self.api_obj = APICalls()
		#initialize_db()
		self.db = DBHandler(reset)
		self.init_static_data(update_static)
		print("Number of games: ", GamesVisited.select().count())
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
		self.api_obj.set_region("EUW")
		self.current_patch = self.api_obj.get_latest_cdn_ver()
		print("current patch: ", self.current_patch)
		champs_data = self.api_obj.get_static_data("champions")["data"]
		if(self.current_patch != APIConstants.CURRENT_PATCH or reset):
			ChampBase.delete().where(ChampBase.champId != None).execute()
			ItemBase.delete().where(ItemBase.itemId != None).execute()
			self.update_champ_avg_stats(champs_data)
			#APIConstants.CURRENT_PATCH = self.current_patch
		self.get_champ_avgs()
		self.items_info = self.get_items_data(reset)
		self.keystones_info = self.get_keystones_data()
		self.spells_info = self.get_summ_spells_data()
		self.runes_info = self.get_runes_data()
		self.champs_info = self.get_champs_data(champs_data, reset)
		for champ,data in self.champs_info.items():
			print(data["name"], data["stats_ranking"])

	def get_items_data(self, update):
		temp = {"complete":{}, "trinket":{}, "start":{}, "consumables":{}}
		for item,val in self.api_obj.get_static_data("items")["data"].items():
			item_int = int(item)
			if("maps" in val and val["maps"]["11"] and "name" in val and val["gold"]["purchasable"]):
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
			temp[champ["id"]] = {"name":champ["name"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"enemy_tips":champ["enemytips"], "ally_tips":champ["allytips"],
								"tags":champ["tags"], "stats_ranking":stats_rank
								}
			if(update):
				self.db.create_champ_info(stats_rank, champ)
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
						if(champ_data["partype"] == "mana"):
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
		return temp

	def get_summ_spells_data(self):
		temp = {}
		for spell,data in self.api_obj.get_static_data("summoner-spells")["data"].items():
			if("CLASSIC" in data["modes"]):
				temp[data["id"]] = {"name":data["name"], "id":data["id"], "image":data["image"]["full"], "des":data["description"]}
		return temp
	
	def close_err_log(self):
		self.error_log.close()

	"""
	def clear_db(self):
		GamesVisited.delete().where(GamesVisited.matchId != None).execute()
		ChampRankStats.delete().where(ChampRankStats.leagueTier != None).execute()  # remove the rows
		ChampPlayer.delete().where(ChampPlayer.accountId != None).execute()
		ChampRoleData.delete().where(ChampRoleData.champId != None).execute()
		ChampAddons.delete().where(ChampAddons.spells != None).execute()
		TeamStats.delete().where(TeamStats.teamInfo != None).execute()
		TeamBase.delete().where(TeamBase.teamId != None).execute()
		MonsterStats.delete().where(MonsterStats.monsterType != None).execute()
	"""

	def add_data_to_db(self):
		for league in self.leagues:
			champs = self.leagues[league]["champions"]
			if(len(champs) > 0):
				stats_base_mod = self.db.create_base_info(self.region, league)
				#print(self.leagues[league])
				if("game_dur" in self.leagues[league]):
					game_l = self.leagues[league]["game_dur"]
				else:
					game_l = 0
				self.db.add_monsters_db(self.leagues[league]["mons"], league, self.region, stats_base_mod)
				self.db.add_teams_db(self.leagues[league]["teams"], game_l, league, self.region, len(self.remakes), stats_base_mod)
				self.db.add_champ_stats(champs, APIConstants.CURRENT_PATCH, stats_base_mod)
				self.db.add_games_visited_db(self.matches_visited_list, self.matches_visited)
				"""
				for champ in champs:
					cur_champ = champs[champ]
					for role, stats in cur_champ.roles.items():
						cur_patch = APIConstants.CURRENT_PATCH
						cur_champ.get_best_players(role)
						champ_q = ChampRoleData.select().where(ChampRoleData.champId == cur_champ.champ_id, ChampRoleData.region == self.region, ChampRoleData.role == role)
						in_game_stats = {"dpg": stats["damage_dealt_per_gold"],
										"dmpg": stats["damage_mitigated_per_gold"],
										"visScore": stats["vision"],
										"objScore": stats["objectives"]
										}
						print("id: ", cur_champ.champ_id, " role: ", role)
						#print("total plays: ", cur_champ.plays, " this role patch stats: ", stats["patches_stats"])
						if(not champ_q.exists()):
							#print("players: ", stats["players"])
							if(league != "silverMinus"):
								addons = ChampAddons.create(
									spells = cPickle.dumps(stats["spells"]),
									skillOrder = cPickle.dumps(stats["skill_order"]),
									keystone = cPickle.dumps(stats["keystone"]),
									items = cPickle.dumps(stats["build"]),
									runes = cPickle.dumps(stats["runes"]),
									matchups = cPickle.dumps(stats["matchups"])
								)
							else:
								addons = None							
							if(cur_patch in stats["patches_stats"]):
								t_plays = stats["patches_stats"][cur_patch]["plays"]
								t_wins = stats["patches_stats"][cur_patch]["wins"]
								t_rating = stats["patches_stats"][cur_patch]["rating"]
							else:
								t_plays = t_wins = t_rating = 0
							champ_basic_d = ChampRoleData.create(
								region = self.region,
								champId = cur_champ.champ_id,
								role = role,
								roleCCDealt = stats["cc_dealt"],
								roleTotalPlays = t_plays,
								roleTotalWins = t_wins,
								totalPlaysByPatch = cPickle.dumps(cur_champ.patch_plays),
								totalBansByPatch = cPickle.dumps(cur_champ.patch_bans),
								roleTotalRating = t_rating,
								addons = addons
							)
							ChampRankStats.create(
								gameStats = cPickle.dumps(in_game_stats),
								patchStats = cPickle.dumps(stats["patches_stats"]),
								kills = stats["kda"]["kills"],
								deaths = stats["kda"]["deaths"],
								assists = stats["kda"]["assists"],
								cspm = stats["cspm"],
								gpm = stats["gpm"],
								resultByTime = cPickle.dumps(stats["game_result"]),
								leagueTier = league,
								champ = champ_basic_d
							)
							self.add_players_to_db(champ_basic_d, stats["players"], cur_champ.champ_id, role)
						else:
							old_champ_basic_d = champ_q.get()
							self.update_core_champ_data(old_champ_basic_d, stats, cur_champ.patch_bans, cur_champ.patch_plays, cur_patch, league)
							league_champ_q = ChampRankStats.select().join(ChampRoleData).where(
								ChampRankStats.leagueTier == league, ChampRoleData.champId == cur_champ.champ_id, 
								ChampRoleData.region == self.region, ChampRoleData.role == role)
							if(league_champ_q.exists()):
								self.update_champ_stats(league_champ_q.get(), stats, in_game_stats)
							else:
								if(old_champ_basic_d.addons == None):
									addons = ChampAddons.create(
										spells = cPickle.dumps(stats["spells"]),
										skillOrder = cPickle.dumps(stats["skill_order"]),
										keystone = cPickle.dumps(stats["keystone"]),
										items = cPickle.dumps(stats["build"]),
										runes = cPickle.dumps(stats["runes"]),
										matchups = cPickle.dumps(stats["matchups"])
									)
									old_champ_basic_d.addons = addons
									old_champ_basic_d.save()
								ChampRankStats.create(
									gameStats = cPickle.dumps(in_game_stats),
									patchStats = cPickle.dumps(stats["patches_stats"]),
									kills = stats["kda"]["kills"],
									deaths = stats["kda"]["deaths"],
									assists = stats["kda"]["assists"],
									cspm = stats["cspm"],
									gpm = stats["gpm"],
									resultByTime = cPickle.dumps(stats["game_result"]),
									leagueTier = league,
									champ = old_champ_basic_d
								)						
						#update players
							self.add_players_to_db(old_champ_basic_d, stats["players"], cur_champ.champ_id, role)
						"""
	"""
	def update_champ_stats(self, old_champ_stats, new_stats, new_game_scores):								
		old_champ_stats.patchStats = self.update_patches_stats(cPickle.loads(old_champ_stats.patchStats), new_stats["patches_stats"])
		old_champ_stats.resultByTime = self.update_game_results(cPickle.loads(old_champ_stats.resultByTime), new_stats["game_result"])

		old_game_stats = cPickle.loads(old_champ_stats.gameStats)
		for game_stat,val in old_game_stats.items():
			#print("current stat name: ", game_stat, " current value: ", val)
			val += new_game_scores[game_stat]
		old_champ_stats.gameStats = cPickle.dumps(old_game_stats)

		old_champ_stats.kills += new_stats["kda"]["kills"]
		old_champ_stats.deaths += new_stats["kda"]["deaths"]
		old_champ_stats.assists += new_stats["kda"]["assists"]
		old_champ_stats.cspm += new_stats["cspm"]
		old_champ_stats.gpm += new_stats["gpm"]
		old_champ_stats.save()
		print("saved data after: ", cPickle.loads(old_champ_stats.patchStats))

	def update_game_results(self, old_game_res, new_game_res):
		for duration,game_res in new_game_res.items():
			#print(game_res)
			if(duration not in old_game_res):
				old_game_res[duration] = game_res
			else:
				old_game_res[duration]["wins"] += game_res["wins"]
				old_game_res[duration]["games"] += game_res["games"]
		return cPickle.dumps(old_game_res)

	def update_patches_stats(self, old_patches_stats, new_patches_stats):
		print("old: ", old_patches_stats)
		print("new: ", new_patches_stats)		
		for patch,match_data in new_patches_stats.items():
			if(patch not in old_patches_stats):
				old_patches_stats[patch] = match_data
			else:
				old_patches_stats[patch]["wins"] += match_data["wins"]
				old_patches_stats[patch]["rating"] += match_data["rating"]
				old_patches_stats[patch]["plays"] += match_data["plays"]
		return cPickle.dumps(old_patches_stats)

	def update_core_champ_data(self, old_data, new_data, new_patch_bans, new_patch_plays, cur_patch, rank):
		old_addons = old_data.addons
		#print("print addon item:", old_addons)
		if(rank != "silverMinus"):
			if(old_addons is not None):
				old_addons.skillOrder = cPickle.dumps(self.update_skill_order(cPickle.loads(old_addons.skillOrder), new_data["skill_order"]))	
				old_addons.spells = cPickle.dumps(self.update_attribute(cPickle.loads(old_addons.spells), new_data["spells"], "spells"))
				old_addons.runes = cPickle.dumps(self.update_runes(cPickle.loads(old_addons.runes), new_data["runes"]))
				old_addons.keystone = cPickle.dumps(self.update_attribute(cPickle.loads(old_addons.keystone), new_data["keystone"], "keystone"))
				old_addons.matchups = cPickle.dumps(self.update_matchups(cPickle.loads(old_addons.matchups), new_data["matchups"]))
				old_addons.items = cPickle.dumps(self.update_champ_items(cPickle.loads(old_addons.items), new_data["build"]))
				old_addons.save()		
			else:
				old_data.addons = ChampAddons.create(
					spells = cPickle.dumps(new_data["spells"]),
					skillOrder = cPickle.dumps(new_data["skill_order"]),
					keystone = cPickle.dumps(new_data["keystone"]),
					items = cPickle.dumps(new_data["build"]),
					runes = cPickle.dumps(new_data["runes"]),
					matchups = cPickle.dumps(new_data["matchups"])
				)			
			#also need to update items			
		#print("league: ", league_champ_q.get().champ.role)
		if(cur_patch in new_data["patches_stats"]):
			old_data.roleTotalPlays += new_data["patches_stats"][cur_patch]["plays"]
			old_data.roleTotalWins += new_data["patches_stats"][cur_patch]["wins"]
			old_data.roleTotalRating += new_data["patches_stats"][cur_patch]["rating"]								

		old_num_bans = cPickle.loads(old_data.totalBansByPatch)
		for patch,num_bans in new_patch_bans.items():
			if(patch not in old_num_bans):
				old_num_bans[patch] = num_bans
			else:
				old_num_bans[patch] += num_bans

		old_num_plays = cPickle.loads(old_data.totalPlaysByPatch)
		for patch,num_plays in old_num_plays.items():
			if(patch not in old_num_plays):
				old_num_plays[patch] = num_plays
			else:
				old_num_plays[patch] += num_plays
		old_data.totalPlaysByPatch = cPickle.dumps(old_num_plays)
		old_data.totalBansByPatch = cPickle.dumps(old_num_bans)
		old_data.roleCCDealt += new_data["cc_dealt"]
		old_data.save()

	def add_players_to_db(self, champ_ob, players, champ, role):
		#print("new players: ", players)
		all_player_q = ChampPlayer.select().join(ChampRoleData).where(
							ChampRoleData.champId == champ,
							ChampRoleData.region == self.region,
							ChampRoleData.role == role
						)
		#all_player_q = ChampRoleData.get(ChampRoleData.champId == champ, ChampRoleData.region == self.region, ChampRoleData.role == role).player_details
		self.error_log.write("Champ id: " + str(champ) + " role: " + role + "\n")
		self.error_log.write("current number of players: " +  str(all_player_q.count()) + "\n")
		self.error_log.write("Current player ids: " + "\n")
		for player in all_player_q:
			self.error_log.write(str(player.accountId) + "\n")
		self.error_log.write("new players: " + str(players) + "\n")
		for player in players:
			self.error_log.write("Checking: " + str(player["accountId"]) + "\n")
			player_q = ChampPlayer.select().join(ChampRoleData).where(
						ChampPlayer.accountId == player["accountId"],
						ChampRoleData.champId == champ,
						ChampRoleData.region == self.region,
						ChampRoleData.role == role
						)
			print("account id: ", player["accountId"], " number of wins: ", player["wins"], " number of games: ", player["plays"])
			if(all_player_q.count() < 5):
				test_q = ChampPlayer.select().where(ChampPlayer.accountId == player["accountId"])
				print("test ex: ", test_q.exists())
				if(not player_q.exists()):
					print("player not  exists: ", player_q.exists())
					self.error_log.write("Adding: " + str(player["accountId"]) + "\n")
					ChampPlayer.create(
						accountId = player["accountId"],
						kills = player["kills"],
						deaths = player["deaths"],
						assists = player["assists"],
						performance = player["performance"],
						wins = player["wins"],
						plays = player["plays"],
						champs = champ_ob				
					)
				else:
					self.error_log.write("Updating stats: " + str(player["accountId"]) + "\n")
					print("updating player stats , ", player["accountId"])
					old_data = player_q.get()
					old_data.kills += player["kills"]
					old_data.deaths += player["deaths"]
					old_data.assists += player["assists"]
					old_data.performance += player["performance"]
					old_data.wins += player["wins"]
					old_data.plays += player["plays"]	
					old_data.save()
			else:
				print("checking new  players")
				self.error_log.write("Comparing current vs new" + "\n")
				curr_all_players = ChampPlayer.select().join(ChampRoleData).where(
						ChampPlayer.accountId == player["accountId"],
						ChampRoleData.champId == champ,
						ChampRoleData.region == self.region,
						ChampRoleData.role == role
						)
				for old_player in curr_all_players:
					old_data = ChampPlayer.select().join(ChampRoleData).where(
						ChampPlayer.accountId == player["accountId"], 
						ChampRoleData.champId == champ, 
						ChampRoleData.region == self.region, 
						ChampRoleData.role == role
						)
					#if the new player has a better rating per game than an old player then replace
					self.error_log.write("new player " + str(old_player.accountId) + "-" + str(old_player.performance/old_player.plays) + " vs old " + str(player["accountId"]) +  "-" + str(player["performance"]/player["plays"]) + "\n")
					if(old_data.exists()):
						self.error_log.write("Updating stats after checking old: " + str(player["accountId"]) + "\n")
						old_d = old_data.get()
						old_d.kills += player["kills"]
						old_d.deaths += player["deaths"]
						old_d.assists += player["assists"]
						old_d.performance += player["performance"]
						old_d.wins += player["wins"]
						old_d.plays += player["plays"]	
						old_d.save()			
					elif(player["performance"]/player["plays"] > (old_player.performance/old_player.plays)):
						print("changing player")
						self.error_log.write("Replacing player " + str(old_player.accountId) + "-" + str(old_player.performance/old_player.plays) + " with new player " + str(player["accountId"]) +  "-" + str(player["performance"]/player["plays"]) + "\n")
						old_player.update(
							accountId = player["accountId"],
							kills = player["kills"],
							deaths = player["deaths"],
							assists = player["assists"],
							performance = player["performance"],
							wins = player["wins"],
							plays = player["plays"]
							).execute()
						break;

		self.error_log.write("number of players after: " +  str(all_player_q.count()) + "\n")
		self.error_log.write("Player ids now: " + "\n")
		for player in ChampPlayer.select().join(ChampRoleData).where(ChampRoleData.champId == champ,ChampRoleData.region == self.region,ChampRoleData.role == role):
			self.error_log.write(str(player.accountId) + "\n")
		self.error_log.write("\n")


	def add_monsters_db(self, teams, league):
		for team,monster_stats in teams.items():
			team_q = TeamBase.select().where(TeamBase.region == self.region, TeamBase.teamId == team, TeamBase.leagueTier == league)
			if(not team_q.exists()):
				TeamBase.create(
					region = self.region,
					teamId = team,
					leagueTier = league
					)
			team_ref = team_q.get()
			print("stats: ", monster_stats)
			for mon,stats in monster_stats.items():
				print("mon: ", mon, " stats: ", stats)
				#print(mon, " w: ",  stats["wins"], " k: ", stats["kills"])
				mon_query = MonsterStats.select().join(TeamBase).where(
					MonsterStats.monsterType == mon, 
					TeamBase.region == self.region,
					TeamBase.teamId == team,
					TeamBase.leagueTier == league
					)
				if(not mon_query.exists()):
					if("types" in stats):
						subtype_data = stats["types"]
					else:
						subtype_data = None 
					MonsterStats.create(
						monsterType = mon,
						team = team_ref,
						kills = stats["killed"],
						wins = stats["wins"],
						time = stats["time"], #if this was the first monster killed, add the time
						games = stats["games"],
						subtypeData = cPickle.dumps(subtype_data)
					)
				else:
					old_d = mon_query.get()
					old_d.kills += stats["killed"]
					old_d.wins += stats["wins"]
					old_d.time += stats["time"] #if this was the first monster killed, add the time
					old_d.games += stats["games"]
					old_sub_data = cPickle.loads(old_d.subtypeData)
					if(old_sub_data is not None):
						for drag_type,num_killed in stats["types"].items():
							if(drag_type not in old_sub_data):
								old_sub_data[drag_type] = num_killed
							else:
								old_sub_data[drag_type] += num_killed
					old_d.save()

	def update_champ_items(self, old_items, new_items):
		for category,champ_items in new_items.items():
			for item,stats in champ_items.items():
				if(item not in old_items[category]):
					old_items[category][item] = stats
				else:
					old_items[category][item]["rating"] += stats["rating"]
					old_items[category][item]["wins"] += stats["wins"]
					old_items[category][item]["used"] += stats["used"]	
		return old_items				


	def update_skill_order(self, old, new):
		if(old != None):
			#print("old skill order : ", old)
			if(len(new) > len(old)):
				old,new = new,old
			for lvl,skills in old.items():
				if(lvl in new):
					for skill,data in new[lvl].items():
						if(skill in old[lvl]):
							old[lvl][skill]["used"] += data["used"]
							old[lvl][skill]["perf"] += data["perf"]
							old[lvl][skill]["wins"] += data["wins"]
						else:
							old[lvl][skill] = data	
		else:
			old = new					
		return old

	def update_runes(self, old, new):
		if(old is not None):
			for rune_type,old_runes in old.items():
				if(rune_type in new):
					for rune,data in new[rune_type].items():
						if(rune in old_runes):
							old_runes[rune]["used"] += data["used"]
							old_runes[rune]["perf"] += data["perf"]
							old_runes[rune]["wins"] += data["wins"]
						else:
							old_runes[rune] = data
		else:
			old = new
		return old

	def update_matchups(self, old, new):
		for matchup_type,matchups in new.items():
			for matchup,stats in matchups.items():
				if(matchup not in old[matchup_type]):
					old[matchup_type] = stats
				else:
					old[matchup_type]["wins_against"] += stats["wins_against"]
					old[matchup_type]["perf_against"] += stats["perf_against"]
					old[matchup_type]["used_against"] += stats["used_against"]
		return old

	def update_attribute(self, old, new, attribute):
		#print("old: ", old, " new: ", new, " type: ", attribute)
		if(old != None):
			for item,stats in new.items():
				if(item in old):
					old[item]["used"] += stats["used"]
					old[item]["perf"] += stats["perf"]
					old[item]["wins"] += stats["wins"]					
				else:
					old[item] = stats
		else:
			old = new
		#print("old updated: ", old)
		return old

	def add_teams_db(self, teams_dict, game_dur, league):
		if(teams_dict[100]["wins"] + teams_dict[200]["wins"] > 0):
			for team,val in teams_dict.items():
				team_q = TeamBase.select().where(TeamBase.region == self.region, TeamBase.teamId == team, TeamBase.leagueTier == league)
				if(not team_q.exists()):
					TeamBase.create(
						region = self.region,
						teamId = team,
						leagueTier = league
					)
				team_ref = team_q.get()
				if(len(team_ref.team_stats) <= 0):
					TeamStats.create(
						teamInfo = team_ref,
						game_length = game_dur,
						numRemakes = len(self.remakes),
						teamGameStats = cPickle.dumps(val),
					)
				else:
					cur_team = team_ref.team_stats.get()
					print(cur_team)
					cur_team.numRemakes += len(self.remakes)
					cur_team.game_length += game_dur
					old_stats = cPickle.loads(cur_team.teamGameStats)
					for stat,value in val.items():
						old_stats[stat] += value
					cur_team.save()

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

	def update_visited_games(self):
		regions_list = []
		#regions_list.append(GamesVisited.select().where(GamesVisited.region == "NA"))
		#regions_list.append(GamesVisited.select().where(GamesVisited.region == "EUW"))
		regions_list.append(GamesVisited.select().where(GamesVisited.region == "EUNE"))
		regions_list.append(GamesVisited.select().where(GamesVisited.region == "KR"))
		for region_games in regions_list:
			region = region_games[0].region
			self.set_region(region)
			for game in region_games:
				print("before: ", game.Patch)
				creation = self.get_match_details(game.matchId)["gameCreation"]/1000
				print(creation)
				if(creation >= 1499875845):
					patch = "7.14.1"
				elif(creation >= 1498608682):
					patch = "7.13.1"
				elif(creation >= 1497399082):
					patch = "7.12.1"
				print("patch: ", patch)
				if(GamesVisited.get(GamesVisited.region == region, GamesVisited.matchId == game.matchId).Patch != patch):
					game_q = GamesVisited.update(Patch=patch).where(GamesVisited.region == region, GamesVisited.matchId == game.matchId)
					game_q.execute() # Will do the SQL update query.
					print("after: ", GamesVisited.get(GamesVisited.region == region, GamesVisited.matchId == game.matchId).Patch)
			#region_games.save()
			print(GamesVisited.select().where(GamesVisited.region == "NA", GamesVisited.Patch == self.current_patch).count())
		for game in GamesVisited.select().where(GamesVisited.region == "NA"):
			if(game.Patch != self.current_patch):
				print(game.Patch)
		print(GamesVisited.select().where(GamesVisited.region == "NA", GamesVisited.Patch == "7.13.1").count())
		"""

	def aggregate_rank_data(self, desired_rank, num_matches=1000, region="NA"):
		self.api_obj.set_region(region)
		self.region = region
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
		if(desired_rank == "diamondPlus"):
			league_players = self.api_obj.get_master_players()
		else:
			if(desired_rank in APIConstants.STARTING_PLAYERS[self.region]):
				league_players = self.api_obj.get_league(APIConstants.STARTING_PLAYERS[self.region][desired_rank])[0]
			else:
				return "Invalid Parameters"
		self.crawl_history(league_players, num_matches)

		self.add_data_to_db()
		#self.add_gamed_visited_db()
		#self.add_players_db()
		end = time.time()
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
						for match in match_history:
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
											if(game_creation_time >= 1499875845):
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

	def check_game(self, game_id, creation):
		print("creating time: ", creation)
		game_query = GamesVisited.select().join(StatsBase).where(GamesVisited.matchId == game_id, StatsBase.region == self.region)
		return game_id not in self.matches_visited_list and not game_query.exists() and creation > 1497399082

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
					if(champ_id in self.champs_info):
						if(champ_id not in curr_section["champions"]):
							curr_section["champions"][champ_id] = ChampionStats(champ_id)	
						curr_section["champions"][champ_id].add_bans(patch)
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
				self.add_champs_data(match_details, {"team1":[p1,p1_rank],"team2":[p2,p2_rank]}, {"team1":p1_tier_key, "team2":p2_tier_key}, p1_role, timeline, patch)
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
							role = "Bot Support"
						elif("Marksman" in champ_tags):
							role = "Bot Carry"
					elif(pos["x"] in self.coords["Top"]["x"] and pos["y"] in self.coords["Top"]["y"]):
						role = "Top"
					else:
						role = "MIDDLE"
			elif(role == "BOTTOM"):
				#check if the player has a large amount of jungle monster kills, jungle most likely
				if((spell1 == 11 or spell2 == 11) or mons_killed_per_min >= 2.3):
					role = "Jungle"
				else:
					role = self.decide_bot_roles(player_data["timeline"], champ_tags, spell1, spell2)
		return role[:3].title() if role == "MIDDLE" else role.title()

	def decide_bot_roles(self, player_timeline, champ_tags, sp1, sp2):
		role = None

		def check_cspm(player, cur_role):
			try:
				if(player["creepsPerMinDeltas"]["0-10"] >= 3):
					return "Bot Carry"
				else:
					return "Bot Support"
			except:
				KeyError
				return cur_role

		if("CARRY" in player_timeline["role"]):
			role = "Bot Carry"
		elif("SUPPORT" in player_timeline["role"]):
			role = "Bot Support"
		else:
			#print("tags: ", tags)
			if(sp1 == 7 or sp2 == 7 or "Marksman" in champ_tags):
				role = check_cspm(player_timeline, "Bot Carry")
			else:
				role = check_cspm(player_timeline, "Bot Support")
		return role

	def add_champ(self, champ, desired_rank):
		#print("champ: ", champ)
		#print("tier rank: ", desired_rank)
		if(champ not in self.leagues[desired_rank]["champions"]):
			new_champ = ChampionStats(champ)
			self.leagues[desired_rank]["champions"][champ] = new_champ

	#perhaps split this section, because "add_champs_data" does not fully describe what it does
	def add_champs_data(self, match_details, players, rank_tier_key, role=None, match_timeline=[], patch="7.14.1"):
		laning_perf = self.analyze_matchup(match_timeline, players["team1"][0], players["team2"][0], role, rank_tier_key)
		game_dur = match_details["gameDuration"]/60
		for team,player in players.items():
			if(team == "team2"):
				laning_perf = 1 - laning_perf
			champ_id = player[0]["championId"]
			champ_obj = self.leagues[rank_tier_key[team]]["champions"][champ_id]
			player_d = match_details["participantIdentities"][player[0]["participantId"]-1]["player"]
			acc_id = player_d["currentAccountId"]
			win = 1 if player[0]["stats"]["win"] else 0
			player_perf = self.get_player_performance(match_timeline, player[0], acc_id, role, team, game_dur, win)
			rating = (player_perf[0]*.7) + (laning_perf*.3)
			oa_rating = rating*self.get_multiplier(player[1])

			self.add_players_data(player[0], acc_id, win, oa_rating, rating, game_dur)
			self.players_visited[acc_id].add_champ(champ_id, win, player_perf[0])
			champ_obj.add_plays(patch)
			self.add_champ_stats(champ_obj, player[0], win, role, self.get_kda(player[0]), laning_perf, oa_rating, game_dur, patch)
			champ_obj.add_player(acc_id, player_d["summonerName"], win, self.get_kda(player[0]), oa_rating, role)
			champ_obj.add_game_scores(role, player_perf[1], player_perf[2])
			self.process_timeline(role, match_timeline, player[0], rank_tier_key[team], laning_perf, oa_rating, match_details)
			self.add_keystone(champ_obj, player[0], role, win, laning_perf)
			self.add_spells(champ_obj, player[0], role, win, laning_perf)
			self.add_player_runes(champ_obj, player[0], role, win, laning_perf)
			champ_obj.add_skill_order(role, match_timeline, player[0]["participantId"], win, oa_rating)

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
			return 1.1
		else:
			return 1

	def add_players_data(self, player, acc_id, win, oa_rating, t_rating, duration):
		cur_player = self.players_visited[acc_id]
		cur_player.num_games += 1
		cur_player.add_ratings(oa_rating, t_rating)
		cur_player.wpm += player["stats"]["wardsPlaced"]/duration
		cur_player.dpm += player["stats"]["totalDamageDealtToChampions"]/duration
		cur_player.add_wins_loses(win)

	#connect this with player perofrmance
	def get_obj_sc(self, player, game_dur):
		points = 0
		stats = player["stats"]
		if("firstTowerAssist" in stats and stats["firstTowerAssist"]):
			points += .5
		elif("firstTowerKill" in stats and stats["firstTowerKill"]):
			points += 1
		if("firstInhibitorAssist" in stats and stats["firstInhibitorAssist"]):
			points += .5
		elif("firstInhibitorKill" in stats and stats["firstInhibitorKill"]):
			points += 1
		print("objectives damage: ", stats["damageDealtToObjectives"])
		points += (stats["damageDealtToObjectives"]/game_dur)**.2
		print("objective points earned: ", points)
		return points

	def get_vis_sc(self, player, game_dur):
		#using riot's own visonscore which is calculated based on how much vision you provided/denied
		try:
			return player["stats"]["visionScore"]/game_dur
		except:
			KeyError
		return 0

	def get_team_stats(self, participants):
		self.team1_dmg = self.team1_gold = self.team1_kills = 0
		self.team2_dmg = self.team2_gold = self.team2_kills = 0
		for i in range(10):
			if(i < 5):
				self.team1_dmg += participants[i]["stats"]["totalDamageDealtToChampions"]
				self.team1_gold += participants[i]["stats"]["goldEarned"]
				self.team1_kills += participants[i]["stats"]["kills"]
			else:
				self.team2_dmg += participants[i]["stats"]["totalDamageDealtToChampions"]
				self.team2_gold += participants[i]["stats"]["goldEarned"]			
				self.team2_kills += participants[i]["stats"]["kills"]

	def get_kda(self, player):
		return {"kills": player["stats"]["kills"],
				"deaths": player["stats"]["deaths"],
				"assists": player["stats"]["assists"]}

	def get_player_performance(self, timeline, player, acc_id, role, team, duration, win):
		teams = {"team1": [self.team1_dmg, self.team1_gold, self.team1_kills], 
				"team2":[self.team2_dmg, self.team2_gold, self.team2_kills]}
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
		obj_sc = self.get_obj_sc(player, duration)
		vis_sc = self.get_vis_sc(player, duration)
		score += self.get_team_contribution(player, acc_id, ka, role, teams[team][0], teams[team][1], teams[team][2])
	
		player = self.players_visited[acc_id]
		player.add_obj_score(obj_sc)
		player.add_vis_score(vis_sc)
		player.add_kills_stats(kda_dict, kda)
		score += obj_sc + vis_sc
		#print("score: ", score)
		return (score/11),obj_sc,vis_sc

	def get_team_contribution(self, player, acc_id, ka, role, team_dmg, team_gold, team_kills):
		score = 0
		if(role == "Bot Support"):
			expected_share = .15
		elif(role == "Bot Carry"):
			expected_share = .25
		else:
			expected_share = .2
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
			if(player_cont > exp_cont):
				return 2,player_cont
			elif(player_cont >= (exp_cont*.9)):
				return 1,player_cont
		return 0,0

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
					rune_group[key] = current_rune
					if(runes_left[current_rune["type"]]["left"] == 0):
						group_key = 0
						for key in rune_group:
							group_key += key
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
						champ.add_item(item_id, self.items_info["consumables"][item_id], role, "consumables", rating, player_win)
					else:
						if(event["timestamp"] < 20000):
							if(item_id in self.items_info["start"]):
								champ.add_item(item_id, self.items_info["start"][item_id], role, "start", rating, player_win)
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

	def add_build(self, item_id, timeline_idx, laning_perf, rating, champ_obj, role, win):
		complete = self.items_info["complete"]
		if("Boots" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, complete[item_id], role, "boots", rating, win)
		elif(item_id in self.items_info and "Jungle" in self.items_info[item_id]["tags"]):
			champ_obj.add_item(item_id, complete[item_id], role, "jung_items", rating, win)
		elif(item_id in self.items_info and "Vision" in self.items_info[item_id]["tags"]):
			champ_obj.add_item(item_id, complete[item_id], role, "vis_items", rating, win)
		elif("CriticalStrike" in complete[item_id]["tags"] and "AttackSpeed" in complete[item_id]["tags"]):
			champ_obj.add_item(item_id, complete[item_id], role, "attk_speed_items", rating, win)
		else:
			if (timeline_idx <= 13):
				if(laning_perf >= 0):
					status = "early_ahead"
				else:
					status = "early_behind"
				if(item_id not in champ_obj.roles[role]["build"]["start"]):
					champ_obj.add_item(item_id, complete[item_id], role, status, rating, win)
			else:
				if(self.check_item(champ_obj, item_id, role, "late")):
					champ_obj.add_item(item_id, complete[item_id], role, "late", rating, win)

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
		champ.oa_rating += rating
		champ.wins += win
		stats = player["stats"]
		gpm = stats["goldEarned"]/dur
		cspm = stats["totalMinionsKilled"]/dur
		dpg = stats["totalDamageDealtToChampions"]/stats["goldEarned"]
		dmpg = stats["damageSelfMitigated"]/stats["goldEarned"]
		#print("damage mitigated: ", stats["damageSelfMitigated"], " gold earned: ", stats["goldEarned"])
		champ.add_role(role, win, dur, kda, dpg, 
			dmpg, laning, rating, patch)
		champ.add_cspm(role, cspm)
		champ.add_gpm(role, gpm)
		champ.add_cc_dealt(role, stats["totalTimeCrowdControlDealt"])

	def analyze_matchup(self, timeline, p1, p2, role, rank_tier_key):
		#print("des rank: ", desired_rank)
		p1_champ = p1["championId"]
		p2_champ = p2["championId"]
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		win = 1.5 if p1["stats"]["win"] else 0
		p1_points = win
		if(p1["participantId"] > p2["participantId"] - 5):
			p1_points += 1
		if(p1["stats"]["firstTowerAssist"]):
			p1_points += 1
		elif(p1["stats"]["firstTowerKill"]):
			p1_points += .5
		p1_points += self.tally_cs_gold_lead(role, p1, p2) 
		p1_points += self.tally_kills_smites(timeline, p1["participantId"], p2["participantId"], role)
		matchup_res = p1_points/6
		#print("matchup result: ", matchup_res)
		self.leagues[rank_tier_key["team1"]]["champions"][p1_champ].add_matchup(role, p2_champ, matchup_res, p1["stats"]["win"])
		self.leagues[rank_tier_key["team2"]]["champions"][p2_champ].add_matchup(role, p1_champ, -matchup_res, p2["stats"]["win"])
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
		if(role == "Bot Carry" or role == "Bot Support"):
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
		return self.api_obj.get_matches_all(acc_id, season, queues)["matches"]

	def get_match_details(self, game_id):
		return self.api_obj.get_match_data(game_id)

	def get_champ_tags(self, champ_id):
		return self.api_obj.get_champ_data(champ_id)["tags"]

if __name__ == "__main__":
	lol_crawler = LolCrawler(True)
	#lol_crawler.aggregate_rank_data("silver", 50, "EUW")
	#lol_crawler.aggregate_rank_data("silver", 40, "NA")
	#lol_crawler.aggregate_rank_data("diamondPlus", 50, "NA")
	lol_crawler.aggregate_rank_data("platinum", 300, "KR")
	lol_crawler.aggregate_rank_data("diamondPlus", 500, "KR")
	lol_crawler.aggregate_rank_data("platinum", 200, "KR")
	lol_crawler.aggregate_rank_data("gold", 200, "KR")
	lol_crawler.aggregate_rank_data("bronze", 200, "KR")

	lol_crawler.aggregate_rank_data("silver", 250, "NA")
	lol_crawler.aggregate_rank_data("gold", 250, "NA")
	lol_crawler.aggregate_rank_data("diamondPlus", 300, "NA")
	#lol_crawler.update_visited_games()
	
	lol_crawler.aggregate_rank_data("silver", 200, "EUNE")
	lol_crawler.aggregate_rank_data("platinum", 200, "EUNE")
	lol_crawler.aggregate_rank_data("diamondPlus", 300, "EUNE")

	lol_crawler.aggregate_rank_data("diamondPlus", 100, "EUW")
	lol_crawler.aggregate_rank_data("platinum", 100, "EUW")
	lol_crawler.aggregate_rank_data("silver", 100, "EUW")

	lol_crawler.aggregate_rank_data("diamondPlus", 500, "NA")
	lol_crawler.aggregate_rank_data("bronze", 300, "NA")
	lol_crawler.aggregate_rank_data("gold", 350, "NA")

	lol_crawler.close_db()