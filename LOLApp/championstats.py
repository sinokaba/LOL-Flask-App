class ChampionStats:
	def __init__(self, champ_id, info):
		#self.name = champ_name
		self.champ_id = champ_id
		self.info = info
		self.roles = {}
		self.plays = 0
		self.wins = 0
		self.kda = 0
		self.bans = 0
		self.laning = 0
		self.players = {}

	def add_role(self, role, win, kda, dmg, dmg_taken):
		#if(role == "")
		if(role not in self.roles):
			self.roles[role] = {"count":1, "build":{"start":{}, 
								"early_ahead":{}, "early_behind":{}, "core":{}, "late":{}}, "kda":kda, 
								"wins":win, "matchups":{}, "damage":dmg, "damage_taken":dmg_taken,
								"runes":{"red":{},"yellow":{},"blue":{},"black":{}}, "keystone":{}, "spells":{}
								}
		else:
			self.roles[role]["count"] += 1
			self.roles[role]["kda"]["kills"] += kda["kills"]
			self.roles[role]["kda"]["deaths"] += kda["deaths"]
			self.roles[role]["kda"]["assists"] += kda["assists"]			
			self.roles[role]["wins"] += win
			self.roles[role]["damage"] += dmg
			self.roles[role]["damage_taken"] += dmg_taken
		#print("CALLED")

	def add_attribute(self, role, win, performance, attr, data, extra=None):
		if(attr == "runes"):
			temp = self.roles[role][attr][extra]
		else:
			temp = self.roles[role][attr]
		item_id = data["id"] 
		if(item_id not in temp):
			temp[item_id] = {"count":1, "wins":win, "perf":performance, "info":data}
		else:
			temp[item_id]["count"] += 1
			temp[item_id]["wins"] += win
			temp[item_id]["perf"] += performance

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
						self.roles[role]["skill_order"][order][event["skillSlot"]] = {"count":1, "wins":win}
					else:
						self.roles[role]["skill_order"][order][event["skillSlot"]]["count"] += 1
						self.roles[role]["skill_order"][order][event["skillSlot"]]["wins"] += win
					order += 1
		#print(self.roles[role]["skill_order"])

	def add_matchup(self, role, enemy_champ, perf, win):
		if(role in self.roles):
			if(enemy_champ not in self.roles[role]["matchups"]):
				self.roles[role]["matchups"][enemy_champ] = {"count_against":1, "perf_against":perf, "wins_against":win}
			else:
				self.roles[role]["matchups"][enemy_champ]["count_against"] += 1
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
					del skill[(min(skill, key=lambda x:skill[x]["count"]))]
				if(len(skill) > 1):
					del skill[(min(skill, key=lambda x:(skill[x]["wins"]/skill[x]["count"])))]

	def add_player(self, account_id, win, kda, p_score):
		#print("kda: ", kda, " account id: ", account_id, " performance: ", p_score)
		#print("Account id: ", account_id, " kda: ", kda)
		if(account_id not in self.players):
			self.players[account_id] = {"plays":1, "wins":win, "kda":kda, "performance":p_score}
		else:
			#print("Plays before: ", self.players[account_id]["plays"])
			self.players[account_id]["wins"] += win
			self.players[account_id]["kda"]["kills"] += kda["kills"]
			self.players[account_id]["kda"]["deaths"] += kda["deaths"]
			self.players[account_id]["kda"]["assists"] += kda["assists"]
			self.players[account_id]["performance"] += p_score
			self.players[account_id]["plays"] += 1
		#print("Plays after: ", self.players[account_id]["plays"])

	def get_best_players(self):
		pass

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
							"kda":self.players[cur]["kda"], "performance":self.players[cur]["performance"]
							}
				del self.players[cur]
			self.players = temp

	def most_common_roles(self, roles, num):
		if(len(roles) > 0):
			most_picked = max(roles, key=lambda x:roles[x]["count"])
			#print("most picked: ", most_picked)
			if(roles[most_picked]["count"]/self.plays >= .9):
				num = 1
			while(len(roles) > num):
				least = float("inf")
				rarest = None
				for role,val in roles.items():
					if(val["count"] < least):
						least = val["count"]
						rarest = role
				del roles[rarest]

	def get_best_build(self):
		#print("items: ", self.items)
		for role in self.roles:
			build = self.roles[role]["build"]
			for stage,items in build.items():
				#print("stage: ", stage)
				if(stage == "early_ahead" or stage == "early_behind" or stage == "start"):
					self.remove_extra_items(items, self.roles[role]["count"], 5)
				else:
					self.remove_extra_items(items, self.roles[role]["count"], 8)
			self.get_core(build)
			self.filter_late_items(build)

	def remove_extra_items(self, items_block, num_plays, threshold):
		while(len(items_block) > threshold):
			del items_block[min(items_block, key=lambda x:items_block[x]["rating"])]

	def filter_runes(self):
		for role in self.roles:
			runes_list = self.roles[role]["runes"]
			for rune_type,runes in runes_list.items():
				while(len(runes) > 1):
					del runes_list[rune_type][min(runes_list[rune_type], key=lambda x:runes_list[rune_type][x]["perf"]/runes_list[rune_type][x]["count"])]

	def filter_late_items(self, build):
		print("late items: ", build["late"])
		temp = {"armor":{}, "mr":{}, "damage":{}}
		for item,stats in build["late"].items():
			if("Armor" in stats["info"]["tags"]):
				temp["armor"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
			elif("SpellBlock" in stats["info"]["tags"]):
				temp["mr"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
			elif("Damage" in stats["info"]["tags"]):
				temp["damage"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
			else:
				build["core"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
		print("late items after: ", temp  )
		build["late"] = temp

	def get_core(self, build):
		temp = {}
		for item,stats in build["early_ahead"].items():
			if(item in build["early_behind"]):
				build["core"][item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
				del build["early_behind"][item]
			else:
				temp[item] = {"rating":stats["rating"], "used":stats["used"], "info":stats["info"]}
		print(temp)
		build["early_ahead"] = temp

	def add_late(self, item_list, role, performance, items_dict):
		for item,item_id in item_list.items():
			if("item" in item and item_list[item] != 0):
				if(self.check_item(item_id, role, items_dict, "late")):
					#print("item: ", item, " start: ", self.items["start"], " early: ", self.items["early"])
					self.add_item(item_id, items_dict["complete"][item_id], role, "late", performance)

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

	"""need to hash a dictionary or something doing a linear search will take too long as size of dictionary grows"""
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
