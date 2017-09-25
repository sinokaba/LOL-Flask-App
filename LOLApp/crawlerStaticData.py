from APIConstants import *
from apiCalls import APICalls
class CrawlerStaticData:
	def __init__(self, db, reset=False):
		self.db = db
		self.riot_api = APICalls()
		#default region to NA to get static data since region not set yet
		self.riot_api.set_region("EUW")
		self.current_patch = self.riot_api.get_latest_cdn_ver()
		print("current patch: ", self.current_patch)
		champs_data = self.riot_api.get_static_data("champions")["data"]
		#print(champs_data_raw)
		#champs_data = requests.get('http://ddragon.leagueoflegends.com/cdn/7.15.1/data/en_US/champion.json').json()["data"]
		if(reset):
			self.db.drop_tables(["champbase", "spellbase", "runebase", "masterybase", "itembase"])
		if(self.current_patch != CURRENT_PATCH or reset):
			self.update_champ_avg_stats(champs_data)
			reset = True
			#CURRENT_PATCH = self.current_patch
		self.get_champ_avgs()
		self.items_info = self.get_items_data(reset)
		self.keystones_info = self.get_keystones_data(reset)
		self.spells_info = self.get_summ_spells_data(reset)
		self.runes_info = self.get_runes_data(reset)
		self.champs_info = self.get_champs_data(champs_data, reset)

	def get_items_data(self, update):
		temp = {"complete":{}, "trinket":{}, "start":{}, "consumables":{}}
		for item,val in self.riot_api.get_static_data("items")["data"].items():
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

			temp[champ["id"]] = {"name":champ["name"], "title":champ["title"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"tips":{"enemy":champ["enemytips"], "ally":champ["allytips"]},
								"tags":champ["tags"], "stats_ranking":stats_rank, "stats":champ_stats_base,
								"resource":champ["partype"]
								}
			print(champ["id"])
			if(update):
				self.db.create_champ_info(champ["id"], temp[champ["id"]])
			#when static is down
		return temp

	#get he avg base and scaling stat for the entire champion pool
	def get_champ_avgs(self):
		self.champs_avg_stats = {}
		champ_avgs_file = open("champ_stats_avgs.txt", "r")
		for stat in champ_avgs_file:
			data = stat.split(":")
			self.champs_avg_stats[data[0]] = float(data[1])
		champ_avgs_file.close()

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
		if(champ["name"] in late_game_monsters or champ["name"] == "Gnar"):
			curr_late_points *= 2
		elif(("Marksman" in champ["tags"] and "Fighter" not in champ["tags"]) or champ["name"] in late_game_scalers):
			curr_late_points *= 1.65
		elif("Mage" in champ["tags"][0] and champ["name"] != "Morgana"):
			curr_late_points *= 1.35
		elif("Assassin" in champ["tags"][0]):
			curr_late_points += 1.5
		if(champ["stats"]["attackrange"] <= 175):
			curr_late_points *= .85
		return curr_late_points

	def get_champ_starting_base(self, champ_name):
		if(champ_name in early_game_bullies):
			return 3
		elif(champ_name == "Zilean"):
			return 2
		elif(champ_name == "Nasus"):
			return -4
		elif(champ_name in early_game_eggs):
			return -3
		elif(champ_name in late_game_monsters or champ_name in late_game_scalers):
			return -1.5
		return 1

	def get_champ_late_base(self, champ_name):
		if(champ_name == "Tristana" or champ_name == "Vladimir"):
			return 2.5
		elif(champ_name in late_game_monsters):
			return 2
		elif(champ_name in late_game_scalers):
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
		masteries_data = self.riot_api.get_static_data("masteries")
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
		for rune_id,data in self.riot_api.get_static_data("runes")["data"].items():
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
		for spell,data in self.riot_api.get_static_data("summoner-spells")["data"].items():
			if("CLASSIC" in data["modes"]):
				temp[data["id"]] = {"name":data["name"], "id":data["id"], "image":data["image"]["full"], "des":data["description"]}
				if(update):
					self.db.create_spell_info(data["id"], temp[data["id"]])
		return temp