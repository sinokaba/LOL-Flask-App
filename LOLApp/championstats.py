class ChampionStats:
	def __init__(self, champ_id, info):
		#self.name = champ_name
		self.champ_id = champ_id
		self.info = info
		self.roles = {}
		self.plays = 0
		self.wins = 0
		self.ov_rating = 0
		self.kda = 0
		self.bans = 0
		self.players = {}

	def add_role(self, role, win, kda, dmg, dmg_taken, laning, rating):
		#if(role == "")
		if(role not in self.roles):
			self.roles[role] = {"plays":1, "build":{"start":{}, "boots":{},
								"early_ahead":{}, "early_behind":{}, "core":{}, "late":{}}, "kda":kda, 
								"wins":win, "matchups":{}, "damage":dmg, "damage_taken":dmg_taken,
								"runes":{"red":{},"yellow":{},"blue":{},"black":{}}, "keystone":{}, "spells":{},
								"laning":laning, "ov_role_rating":rating
								}
		else:
			self.roles[role]["plays"] += 1
			self.roles[role]["kda"]["kills"] += kda["kills"]
			self.roles[role]["kda"]["deaths"] += kda["deaths"]
			self.roles[role]["kda"]["assists"] += kda["assists"]			
			self.roles[role]["wins"] += win
			self.roles[role]["damage"] += dmg
			self.roles[role]["damage_taken"] += dmg_taken
			self.roles[role]["laning"] += laning
			self.roles[role]["ov_role_rating"] += rating
		#print("CALLED")

	def add_attribute(self, role, win, perf, attr, data, extra=None):
		if(attr == "runes"):
			temp = self.roles[role][attr][extra]
		else:
			temp = self.roles[role][attr]
		item_id = data["id"] 
		if(item_id not in temp):
			temp[item_id] = {"used":1, "wins":win, "perf":perf, "info":data}
		else:
			temp[item_id]["used"] += 1
			temp[item_id]["wins"] += win
			temp[item_id]["perf"] += perf

	def add_skill_order(self, role, data, par_id, win):
		if("skill_order" not in self.roles[role]):
			self.roles[role]["skill_order"] = {}
		order = 1
		for frame in data:
			for event in frame["events"]:
				if(event["type"] == "SKILL_LEVEL_UP" and event["participantId"] == par_id):
					if(order not in self.roles[role]["skill_order"]):
						self.roles[role]["skill_order"][order] = {}
					if(event["skillSlot"] not in self.roles[role]["skill_order"][order]):
						self.roles[role]["skill_order"][order][event["skillSlot"]] = {"used":1, "wins":win}
					else:
						self.roles[role]["skill_order"][order][event["skillSlot"]]["used"] += 1
						self.roles[role]["skill_order"][order][event["skillSlot"]]["wins"] += win
					order += 1
		#print(self.roles[role]["skill_order"])

	def add_matchup(self, role, enemy_champ, perf, win):
		if(role in self.roles):
			if(enemy_champ not in self.roles[role]["matchups"]):
				self.roles[role]["matchups"][enemy_champ] = {"used_against":1, "perf_against":perf, "wins_against":win}
			else:
				self.roles[role]["matchups"][enemy_champ]["used_against"] += 1
				self.roles[role]["matchups"][enemy_champ]["perf_against"] += perf
				self.roles[role]["matchups"][enemy_champ]["wins_against"] += win
			
	def add_kda(self, kda):
		if(self.kda is 0):
			self.kda = kda
		else:
			self.kda["kills"] += kda["kills"]
			self.kda["deaths"] += kda["deaths"]
			self.kda["assists"] += kda["assists"]

	def get_skill_order(self):
		for role in self.roles:
			for lvl,skill in self.roles[role]["skill_order"].items():
				while(len(skill) > 2):
					del skill[(min(skill, key=lambda ss:skill[ss]["used"]))]
				if(len(skill) > 1):
					del skill[(min(skill, key=lambda ss:(skill[ss]["wins"]/skill[ss]["used"])))]

	def add_player(self, acused_id, win, kda, p_score):
		#print("kda: ", kda, " acused id: ", acused_id, " perf: ", p_score)
		#print("Acused id: ", acused_id, " kda: ", kda)
		if(acused_id not in self.players):
			self.players[acused_id] = {"plays":1, "wins":win, "kda":kda, "perf":p_score}
		else:
			#print("Plays before: ", self.players[acused_id]["plays"])
			self.players[acused_id]["wins"] += win
			self.players[acused_id]["kda"]["kills"] += kda["kills"]
			self.players[acused_id]["kda"]["deaths"] += kda["deaths"]
			self.players[acused_id]["kda"]["assists"] += kda["assists"]
			self.players[acused_id]["perf"] += p_score
			self.players[acused_id]["plays"] += 1
		#print("Plays after: ", self.players[acused_id]["plays"])

	def get_best_players(self):
		temp = {}
		for player,stats in self.players.items():
			if(stats["plays"] > self.plays*.08):
				temp[player] = {"plays":stats["plays"], "wins":stats["wins"], "kda":stats["kda"], "perf":stats["perf"]}
		while(len(temp) > 10):
			del temp[(min(temp, key=lambda player:(temp[player]["perf"]/temp[player]["plays"])))]

	def get_most_played(self):
		most_played = -1
		acc_id = None
		for player,stats in self.players.items():
			if(stats["plays"] > most_played):
				most_played = stats["plays"]
				acc_id = player
		if(acc_id is not None):
			print("Most played by a player: ", most_played, " vs kda: ", self.players[acc_id]["kda"])

	def get_most_played_players(self):
		if(len(self.players) > 5):
			temp = {}
			while(len(temp) < 5):
				base = -1
				cur = -1
				for player,stats in self.players.items():
					if(stats["plays"] > base):
						base = stats["plays"]
						cur = player
				temp[cur] = {"plays":self.players[cur]["plays"], "wins":self.players[cur]["wins"], 
							"kda":self.players[cur]["kda"], "perf":self.players[cur]["perf"]
							}
				del self.players[cur]
			self.players = temp

	def most_common_roles(self, roles, num):
		if(len(roles) > 0):
			most_picked = max(roles, key=lambda role:roles[role]["plays"])
			#print("most picked: ", most_picked)
			if(roles[most_picked]["plays"]/self.plays >= .9):
				num = 1
			while(len(roles) > num):
				least = float("inf")
				rarest = None
				for role,val in roles.items():
					if(val["plays"] < least):
						least = val["plays"]
						rarest = role
				del roles[rarest]

	def get_best_build(self):
		#print("items: ", self.items)
		for role in self.roles:
			build = self.roles[role]["build"]
			for stage,items in build.items():
				#print("stage: ", stage)
				if(stage == "start" or "early" in stage):
					self.remove_rare_items(items, self.roles[role]["plays"], 4)
				else:
					self.remove_rare_items(items, self.roles[role]["plays"], 6)
			self.get_boots(role, build)
			self.get_core(build)
			self.filter_items(build, "late", self.roles[role]["plays"]*.085)
			self.filter_items(build, "start", self.roles[role]["plays"]*.085)

	def get_boots(self, role, items_block):
		boots = items_block["boots"]
		if(len(boots) > 0):
			best_boot = max(boots, key=lambda boot:boots[boot]["rating"]/boots[boot]["used"])
			if(best_boot not in items_block["core"]):
				items_block["core"][best_boot] = {"rating":boots[best_boot]["rating"], "used":boots[best_boot]["used"], "info":boots[best_boot]["info"]}
			else:
				items_block["early_ahead"][best_boot] = {"rating":boots[best_boot]["rating"], "used":boots[best_boot]["used"], "info":boots[best_boot]["info"]}
		del self.roles[role]["build"]["boots"]	

	def remove_rare_items(self, items_block, num_plays, threshold):
		while(len(items_block) > threshold):
			del items_block[min(items_block, key=lambda item:items_block[item]["used"])]

	def filter_runes(self):
		for role in self.roles:
			runes_list = self.roles[role]["runes"]
			for rune_type,runes in runes_list.items():
				while(len(runes) > 1):
					del runes_list[rune_type][min(runes_list[rune_type], key=lambda r:runes_list[rune_type][r]["perf"]/runes_list[rune_type][r]["used"])]

	def filter_items(self, build, stage, role_plays):
		stage_items = build[stage]
		#print("items before: ", stage_items)
		if(stage == "late"):
			temp = {"defence":{}, "offense":{}}
			try:
				core_item = max(stage_items, key=lambda item:stage_items[item]["rating"]/stage_items[item]["used"])
				#print("add to core: ", stage_items[core_item]["info"]["name"], " rating: ", stage_items[core_item]["rating"])
				stats = stage_items[core_item]
				build["core"][core_item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
				del stage_items[core_item]			
			except:
				ValueError
			for item,stats in stage_items.items():
				item_tags = stats["info"]["tags"]
				if(stats["rating"] > 1 and stats["used"] > role_plays):
					if("Armor" in item_tags or "SpellBlock" in item_tags):
						temp["defence"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
					elif("Damage" in item_tags or "Attack" in item_tags):
						temp["offense"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
					else:
						build["core"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
		else:
			temp = {}
			cont = True
			while(len(temp) < 3 and cont):
				cont = False
				cur_rating = -900
				cur_item = -1
				for item,stats in stage_items.items():
					if(item not in temp and stats["rating"] > cur_rating and stats["used"] > role_plays):
						cur_item = item
						cur_rating = stats["rating"]
				#print("current item: ", cur_item)
				if(cur_item != - 1):
					cont = True
					stats = stage_items[cur_item]
					temp[cur_item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
		#print("new items: ", temp, " stage: ", stage)
		build[stage] = temp
		#print("build after: ", build)

	def get_core(self, build):
		temp = {}
		for item,stats in build["early_ahead"].items():
			if(item in build["early_behind"] and item not in build["core"]):
				early_b_stats = build["early_behind"][item]
				build["core"][item] = {"rating":stats["rating"]+early_b_stats["rating"], "used":stats["used"]+early_b_stats["used"], "info":stats["info"]}
				del build["early_behind"][item]
			else:
				temp[item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
		print(temp)
		build["early_ahead"] = temp

	def add_late(self, item_list, role, rating, items_dict):
		for item,item_id in item_list.items():
			if("item" in item and item_list[item] != 0):
				if(self.check_item(item_id, role, items_dict, "late")):
					if("Boots" in items_dict["complete"][item_id]["tags"]):
						self.add_item(item_id, items_dict["complete"][item_id], role, "boots", rating)
					#print("item: ", item, " start: ", self.items["start"], " early: ", self.items["early"])
					self.add_item(item_id, items_dict["complete"][item_id], role, "late", rating)

	def check_item(self, item_id, role, items_dict, stage):
		build = self.roles[role]["build"]
		if(stage == "late"):
			if(item_id not in build["start"] and item_id not in build["early_ahead"] and item_id not in build["early_behind"]):
				return item_id in items_dict["complete"]
			return False
		elif(stage == "start"):
			return item_id in items_dict["start"]
		elif(stage == "early_ahead" or stage == "early_behind"):
			if(item_id not in build["start"]):
				return item_id in items_dict["complete"]
			return False

	def add_item(self, item_id, item, role, stage, rating):
		#print("roles: ", self.roles)
		if(item_id not in self.roles[role]["build"][stage]):
			self.roles[role]["build"][stage][item_id] = {"rating":rating, "used":1, "info":item}
		else:
			self.roles[role]["build"][stage][item_id]["rating"] += rating
			self.roles[role]["build"][stage][item_id]["used"] += 1

	def __str__(self):
		return "Name: " + self.name + " Plays: " + str(self.plays) + " Wins: " + str(self.wins)

	def get_items(self):
		return self.items
