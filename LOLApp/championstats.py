class ChampionStats:
	def __init__(self, champ_id):
		self.champ_id = champ_id
		self.roles = {}
		self.plays = self.wins = self.bans = 0
		self.oa_rating = 0
		self.kills = self.deaths = self.assists = 0
		self.players = {}

	def add_role(self, role, win, kda, dmg, dmg_taken, laning, rating):
		#if(role == "")
		if(role not in self.roles):
			self.roles[role] = {"plays":1, "build":{"start":{}, "boots":{}, "consumables":{}, "jung_items":{}, 
								"vis_items":{}, "early_ahead":{}, "attk_speed_items":{}, "early_behind":{}, "core":{}, 
								"late":{}}, "kda":kda, "wins":win, "matchups":{}, "damage_dealt":dmg, 
								"damage_taken":dmg_taken, "runes":{"red":{},"yellow":{},"blue":{},"black":{}}, 
								"keystone":{},"spells":{}, "laning":laning, "oa_role_rating":rating, "skill_order":{}
								}
		else:
			self.roles[role]["plays"] += 1
			self.roles[role]["kda"]["kills"] += kda["kills"]
			self.roles[role]["kda"]["deaths"] += kda["deaths"]
			self.roles[role]["kda"]["assists"] += kda["assists"]			
			self.roles[role]["wins"] += win
			self.roles[role]["damage_dealt"] += dmg
			self.roles[role]["damage_taken"] += dmg_taken
			self.roles[role]["laning"] += laning
			self.roles[role]["oa_role_rating"] += rating
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

	def add_skill_order(self, role, data, par_id, win, performance):
		order = 1
		for frame in data:
			for event in frame["events"]:
				if(event["type"] == "SKILL_LEVEL_UP" and event["participantId"] == par_id):
					if(order not in self.roles[role]["skill_order"]):
						self.roles[role]["skill_order"][order] = {}
					if(event["skillSlot"] not in self.roles[role]["skill_order"][order]):
						self.roles[role]["skill_order"][order][event["skillSlot"]] = {"used":1, "wins":win, "perf":performance}
					else:
						self.roles[role]["skill_order"][order][event["skillSlot"]]["used"] += 1
						self.roles[role]["skill_order"][order][event["skillSlot"]]["wins"] += win
						self.roles[role]["skill_order"][order][event["skillSlot"]]["perf"] += performance
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
		self.kills += kda["kills"]
		self.deaths += kda["deaths"]
		self.assists += kda["assists"]

	def get_skill_order(self):
		for role in self.roles:
			temp = {}
			skill_rank = {1:0, 2:0, 3:0, 4:0}
			print("skill order: ", self.roles[role]["skill_order"].items())
			for lvl,skills in self.roles[role]["skill_order"].items():
				print(lvl, " skills: ", skills)
				print(skill_rank)
				while(True):
					if(len(skills) > 0):
						skill = self.get_best_skill(skills)
						if(len(temp) <= 0):
							temp[lvl] = skill
							skill_rank[skill] += 1
							break
						elif(lvl == 2):
							if(temp[1] != skill):
								temp[lvl] = skill
								skill_rank[skill] += 1
								break
						else:
							if(skill != 4):
								if(skill_rank[skill] < 5):
									temp[lvl] = skill
									skill_rank[skill] += 1
									break
							else:
								if(skill_rank[skill] < 3):
									temp[lvl] = skill
									skill_rank[skill] += 1
									break
						del skills[skill]
					else:
						break
			self.roles[role]["skill_order"] = temp

	def get_best_skill(self, skills_dict):
		print("skills: ", skills_dict)
		return max(skills_dict, key=lambda skill:skills_dict[skill]["perf"]/skills_dict[skill]["used"])

	def add_player(self, playerId, win, kda, p_score):
		#print("kda: ", kda, " acused id: ", acused_id, " perf: ", p_score)
		#print("Acused id: ", acused_id, " kda: ", kda)
		if(playerId not in self.players):
			self.players[playerId] = {"plays":1, "wins":win, "kda":kda, "perf":p_score}
		else:
			#print("Plays before: ", self.players[acused_id]["plays"])
			self.players[playerId]["wins"] += win
			self.players[playerId]["kda"]["kills"] += kda["kills"]
			self.players[playerId]["kda"]["deaths"] += kda["deaths"]
			self.players[playerId]["kda"]["assists"] += kda["assists"]
			self.players[playerId]["perf"] += p_score
			self.players[playerId]["plays"] += 1
		#print("Plays after: ", self.players[acused_id]["plays"])

	def get_best_players(self):
		self.get_most_played_players()
		temp = {}
		for player,stats in self.players.items():
			if(stats["plays"] > self.plays*.08):
				temp[player] = self.players[player]
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
					self.remove_rare_items(items, self.roles[role]["plays"], 5)
			self.get_boots(role, build)
			self.get_core(build)
			self.filter_items(build, "late", self.roles[role]["plays"]*.085)
			self.filter_items(build, "start", self.roles[role]["plays"]*.085)


	def get_boots(self, role, items_block):
		boots = items_block["boots"]
		if(len(boots) > 0):
			best_boot = max(boots, key=lambda boot:boots[boot]["rating"]/boots[boot]["used"])
			if(best_boot not in items_block["core"]):
				items_block["core"][best_boot] = boots[best_boot]
			else:
				items_block["early_ahead"][best_boot] = boots[best_boot]
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
			defense = {}
			offense = {}
			try:
				core_item = max(stage_items, key=lambda item:stage_items[item]["rating"]/stage_items[item]["used"])
				#print("add to core: ", stage_items[core_item]["info"]["name"], " rating: ", stage_items[core_item]["rating"])
				stats = stage_items[core_item]
				build["core"][core_item] = stage_items[item]
				del stage_items[core_item]			
			except:
				ValueError
			for item,stats in stage_items.items():
				if(item not in build["core"] and item not in build["early_behind"] and item not in build["early_ahead"]):
					item_tags = stats["info"]["tags"]
					if(stats["rating"] > 1 and stats["used"] > role_plays):
						if("Armor" in item_tags or "SpellBlock" in item_tags):
							defense[item] = stage_items[item]
						elif("Damage" in item_tags or "Attack" in item_tags):
							offense[item] = stage_items[item]
						else:
							build["core"][item] = stage_items[item]
			build["offense"] = offense
			build["defense"] = defense
			del stage_items
		else:
			temp = {}
			print("Before stage: ", stage, " items: ", stage_items)
			if(len(stage_items) > 3):
				cont = True
				while(len(temp) < 3 and cont):
					cont = False
					cur_rating = -900
					cur_item = -1
					for item,stats in stage_items.items():
						if(item not in temp and stats["rating"] > cur_rating and stats["used"] > role_plays):
							cur_item = item
							cur_rating = stats["rating"]
					print("current item: ", cur_item)
					if(cur_item != -1 and cur_item not in temp):
						cont = True
						temp[cur_item] = stage_items[cur_item]
			print("After stage: ", stage, " items: ", temp)
			build[stage] = temp

	def get_core(self, build):
		temp = {}
		for item,stats in build["early_ahead"].items():
			if(item in build["early_behind"] and item not in build["core"]):
				early_b_stats = build["early_behind"][item]
				build["core"][item] = early_b_stats
				del build["early_behind"][item]
			else:
				temp[item] = build["early_ahead"][item]
		if(len(build["jung_items"]) > 0):
			best_jung_item = max(build["jung_items"], key=lambda item:build["jung_items"][item]["rating"]/build["jung_items"][item]["used"])
			build["core"][best_jung_item] = build["jung_items"][best_jung_item]
		if(len(build["vis_items"]) > 0):
			best_vis_item = max(build["vis_items"], key=lambda item:build["vis_items"][item]["rating"]/build["vis_items"][item]["used"])
			build["core"][best_vis_item] = build["vis_items"][best_vis_item]
		if(len(build["attk_speed_items"]) > 0):
			best_as_item = max(build["attk_speed_items"], key=lambda item:build["attk_speed_items"][item]["rating"]/build["attk_speed_items"][item]["used"])
			build["core"][best_as_item] = build["attk_speed_items"][best_as_item]
		del build["jung_items"]
		del build["vis_items"]
		del build["attk_speed_items"]
		build["early_ahead"] = temp

	def add_late(self, item_list, role, rating, items_dict):
		for item,item_id in item_list.items():
			if("item" in item and item_list[item] != 0):
				if(self.check_item(item_id, role, items_dict, "late")):
					if("Boots" in items_dict["complete"][item_id]["tags"]):
						self.add_item(item_id, items_dict["complete"][item_id], role, "boots", rating)
					elif(item_id in items_dict):
						if("Jungle" in items_dict[item_id]["tags"]):
							self.add_item(item_id, items_dict["complete"][item_id], role, "jung_items", rating)
						else:
							self.add_item(item_id, items_dict["complete"][item_id], role, "vis_items", rating)
					else:
						self.add_item(item_id, items_dict["complete"][item_id], role, "late", rating)
						#print("item: ", item, " start: ", self.items["start"], " early: ", self.items["early"])

	def add_item(self, item_id, item, role, stage, rating):
		#print("roles: ", self.roles)
		if(item_id not in self.roles[role]["build"][stage]):
			self.roles[role]["build"][stage][item_id] = {"rating":rating, "used":1, "info":item}
		else:
			self.roles[role]["build"][stage][item_id]["rating"] += rating
			self.roles[role]["build"][stage][item_id]["used"] += 1

	def get_items(self):
		return self.items
