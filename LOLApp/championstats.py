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
								"early_ahead":{}, "early_behind":{}, "core":{}}, "kda":kda, 
								"wins":win, "matchups":{}, "damage":dmg, "damage_taken":dmg_taken}
		else:
			self.roles[role]["count"] += 1
			self.roles[role]["kda"]["kills"] += kda["kills"]
			self.roles[role]["kda"]["deaths"] += kda["deaths"]
			self.roles[role]["kda"]["assists"] += kda["assists"]			
			self.roles[role]["wins"] += win
			self.roles[role]["damage"] += dmg
			self.roles[role]["damage_taken"] += dmg_taken
		#print("CALLED")

	def add_spells(self, role, spells, win):
		if "spells" not in self.roles[role]:
			self.roles[role]["spells"] = {}
		for spell in spells:
			if(spell not in self.roles[role]["spells"]):
				self.roles[role]["spells"][spell] = {"count":1, "wins":win}
			else:
				self.roles[role]["spells"][spell]["count"] += 1
				self.roles[role]["spells"][spell]["wins"] += win

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

	def add_matchup(self, role, enemy_champ, win):
		if(role in self.roles):
			if(enemy_champ in self.roles[role]["matchups"]):
				self.roles[role]["matchups"][enemy_champ]["against"] += 1
				self.roles[role]["matchups"][enemy_champ]["wins"] += win
			else:
				self.roles[role]["matchups"][enemy_champ] = {"against":1, "wins":win}

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
		print("Account id: ", account_id, " kda: ", kda)
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
		if(len(self.players) > 10):
			temp = {}
			while(len(temp) < 10):
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
			for stage, items in self.roles[role]["build"].items():
				#print("stage: ", stage)
				self.remove_extra_items(items, self.roles[role]["count"], 6)

	def remove_extra_items(self, items_block, num_plays, threshold):
		while(len(items_block) > threshold):
			del items_block[min(items_block, key=lambda x:items_block[x]["used"])]

	def add_core(self, item_list, role, win, items_dict):
		for item,item_id in item_list.items():
			if("item" in item and item_list[item] != 0):
				item_id = str(item_id)
				if(self.check_item(item_id, role, items_dict, "core")):
					#print("item: ", item, " start: ", self.items["start"], " early: ", self.items["early"])
					self.add_item(item_id, items_dict["complete"][item_id], win, role, "core")

	def check_item(self, item_id, role, items_dict, stage):
		build = self.roles[role]["build"]
		if(stage == "core"):
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
	def add_item(self, item_id, item, win, role, stage):
		#print("roles: ", self.roles)
		if(item_id not in self.roles[role]["build"][stage]):
			self.roles[role]["build"][stage][item_id] = {"wins":0, "used":1, "info":item}
		self.roles[role]["build"][stage][item_id]["wins"] += win
		self.roles[role]["build"][stage][item_id]["used"] += 1

	def __str__(self):
		return "Name: " + self.name + " Plays: " + str(self.plays) + " Wins: " + str(self.wins)

	def get_items(self):
		return self.items
