class ChampionStats:
	def __init__(self, champ_id):
		self.champ_id = champ_id
		self.roles = {}
		self.patch_bans = {}
		self.patch_plays = {}
		self.patch_wins = {}
		self.patch_rating = {}
		self.t_plays = self.t_wins = self.t_rating = self.t_bans = 0
		self.kills = self.deaths = self.assists = 0

	def add_bans(self, patch, this_patch):
		if(patch not in self.patch_bans):
			self.patch_bans[patch] = 1
		else:
			self.patch_bans[patch] += 1
		#if(patch == this_patch):
		self.t_bans += 1

	def add_plays(self, patch, this_patch):
		if(patch not in self.patch_plays):
			self.patch_plays[patch] = 1
		else:
			self.patch_plays[patch] += 1
		#if(patch == this_patch):
		self.t_plays += 1

	def add_rating(self, patch, rating, this_patch):
		if(patch not in self.patch_rating):
			self.patch_rating[patch] = rating
		else:
			self.patch_rating[patch] += rating
		#if(patch == this_patch):
		self.t_rating += rating

	def add_wins(self, patch, win, this_patch):
		if(patch not in self.patch_wins):
			self.patch_wins[patch] = win
		else:
			self.patch_wins[patch] += win
		#if(patch == this_patch):
		self.t_wins += win

	def add_role(self, role, win, game_dur, kda, dpg, dmpg, laning, rating, patch):
		print("damage_mitigated_per_gold", dmpg, "dpg: ", dpg,  " patch: ", patch)
		if(game_dur <= 20):
			dur = "0-20"
		elif(game_dur > 20 and game_dur <= 30):
			dur = "20-30"
		elif(game_dur > 30 and game_dur <= 40):
			dur = "30-40"
		else:
			dur = "40+"	
		if(role not in self.roles):
			self.roles[role] = {"patches_stats": {patch:{"plays":1, "rating":rating, "wins":win}}, "t_plays":1, "players":{}, 
								"build":{"start":{}, "boots":{}, "consumables":{}, "jung_items":{}, 
								"vis_items":{}, "early_ahead":{}, "attk_speed_items":{}, "early_behind":{}, "core":{},
								"late":{}}, "kda":kda, "game_result":{}, "matchups":{}, "t_rating":rating,
								"damage_dealt_per_gold":dpg, "damage_mitigated_per_gold":dmpg, 
								"runes":{"reds":{},"yellows":{},"blues":{},"blacks":{}}, "t_wins":win,
								"keystone":{},"spells":{}, "laning":laning, "skill_order":{}
								}
		else:
			self.roles[role]["kda"]["kills"] += kda["kills"]
			self.roles[role]["kda"]["deaths"] += kda["deaths"]
			self.roles[role]["kda"]["assists"] += kda["assists"]			
			self.roles[role]["damage_dealt_per_gold"] += dpg
			self.roles[role]["damage_mitigated_per_gold"] += dmpg
			self.roles[role]["laning"] += laning
			self.roles[role]["t_plays"] += 1
			self.roles[role]["t_rating"] += rating
			self.roles[role]["t_wins"] += win
			if(patch not in self.roles[role]["patches_stats"]):
				self.roles[role]["patches_stats"][patch] = {"plays":1, "rating":rating, "wins":win}
			else:
				self.roles[role]["patches_stats"][patch]["plays"] += 1
				self.roles[role]["patches_stats"][patch]["rating"] += rating
				self.roles[role]["patches_stats"][patch]["wins"] += win
		self.add_game_res(win, dur, self.roles[role])

		#print("CALLED")

	def add_cspm(self, role, cspm):
		if("cspm" not in self.roles[role]):
			self.roles[role]["cspm"] = cspm
		else:
			self.roles[role]["cspm"] += cspm

	def add_gpm(self, role, gpm):
		if("gpm" not in self.roles[role]):
			self.roles[role]["gpm"] = gpm
		else:
			self.roles[role]["gpm"] += gpm

	def add_cc_dealt(self, role, cc):
		if("cc_dealt" not in self.roles[role]):
			self.roles[role]["cc_dealt"] = cc
		else:
			self.roles[role]["cc_dealt"] += cc

	def add_game_scores(self, role, objective, vision):
		role_champ = self.roles[role]
		if("vision" not in role_champ):
			role_champ["vision"] = vision
		else:
			role_champ["vision"] += vision
		if("objectives" not in role_champ):
			role_champ["objectives"] = objective
		else:
			role_champ["objectives"] += objective

	def add_game_res(self, win, dur, role):
		if(dur not in role["game_result"]):
			role["game_result"][dur] = {"wins":win, "games":1}
		else:
			role["game_result"][dur]["wins"] += win
			role["game_result"][dur]["games"] += 1

	def add_runes(self, role, win, perf, data, category, key):
		runes = self.roles[role]["runes"][category]
		if(key not in runes):
			runes[key] = {"used":1, "wins":win, "perf":perf, "rune_ids":data}
		else:
			runes[key]["used"] += 1
			runes[key]["wins"] += win
			runes[key]["perf"] += perf

	def add_spells(self, role, win, perf, key, spells):
		spells_dict = self.roles[role]["spells"]
		if(key not in spells_dict):
			spells_dict[key] = {"used":1, "wins":win, "perf":perf, "spells_id":spells}
		else:
			spells_dict[key]["used"] += 1
			spells_dict[key]["wins"] += win
			spells_dict[key]["perf"] += perf			

	def add_attribute(self, role, win, perf, attr, data):
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
		win = 1 if win else 0
		if(role in self.roles):
			temp = self.roles[role]["matchups"]
			if(enemy_champ not in temp):
				temp[enemy_champ] = {"used_against":1, "perf_against":perf, "wins_against":win}
			else:
				temp[enemy_champ]["used_against"] += 1
				temp[enemy_champ]["perf_against"] += perf
				temp[enemy_champ]["wins_against"] += win
			
	def sort_matchups(self, role):
		matchups = self.roles[role]["matchups"]
		temp = {"weak_against":{}, "strong_against":{}}
		for matchup,stats in matchups.items():
			if(stats["perf_against"]/stats["used_against"] > 0):
				temp["strong_against"][matchup] = stats
			else:
				temp["weak_against"][matchup] = stats
		self.roles[role]["matchups"] = temp

	def add_kda(self, kda):
		self.kills += kda["kills"]
		self.deaths += kda["deaths"]
		self.assists += kda["assists"]

	def get_skill_order(self):
		for role in self.roles:
			temp = {}
			skill_rank = {1:0, 2:0, 3:0, 4:0}
			#print("skill order: ", self.roles[role]["skill_order"].items())
			for lvl,skills in self.roles[role]["skill_order"].items():
				#print(lvl, " skills: ", skills)
				#print(skill_rank)
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

	def add_player(self, playerId, name, win, kda, p_score, role, rank, summ_id):
		print("kda: ", kda, " playerId: ", playerId, " perf: ", p_score)
		#print("Acused id: ", acused_id, " kda: ", kda)
		players_dict = self.roles[role]["players"]
		if(playerId not in players_dict):
			players_dict[playerId] = {"accountId": playerId, "name":name, "plays":1, 
										"wins":win, "kills":kda["kills"], "assists":kda["assists"], 
										"deaths":kda["deaths"], "performance":p_score, "rank":rank, "summonerId":summ_id}
		else:
			#print("Plays before: ", self.players[acused_id]["plays"])
			players_dict[playerId]["wins"] += win
			players_dict[playerId]["kills"] += kda["kills"]
			players_dict[playerId]["deaths"] += kda["deaths"]
			players_dict[playerId]["assists"] += kda["assists"]
			players_dict[playerId]["performance"] += p_score
			players_dict[playerId]["plays"] += 1
		print(" playerId: ", playerId, " Plays after: ", players_dict[playerId]["plays"])

	def get_best_players(self, role):
		players = self.roles[role]["players"]
		#print("players before: ", players)
		self.get_most_played_players(players, role)
		temp = []
		"""
		temp = {}
		for player,stats in players.items():
			if(stats["plays"] > self.plays*.08):
				temp[player] = self.players[player]
		"""
		if(len(players) > 5):
			while(len(players) > 5):
				cur_player = max(players, key=lambda player:(players[player]["performance"]/players[player]["plays"]))
				temp.append(players[cur_player])
				del players[cur_player]
		else:
			for player,val in players.items():
				temp.append(val)
		self.roles[role]["players"] = temp
		#print("players after in dict: ", self.roles[role]["players"])

	def get_most_played_players(self, players, role):
		if(len(players) > 5):
			temp = {}
			while(len(temp) < 5):
				base = -1
				cur = -1
				for player,stats in players.items():
					if(stats["plays"] > base):
						base = stats["plays"]
						cur = player
				temp[cur] = players[cur]
				del players[cur]
			self.roles[role]["players"] = temp

	def most_common_roles(self, roles, num):
		if(len(roles) > 0):
			#print("most picked: ", most_picked)
			temp = {}
			for role,val in roles.items():
				if(val["plays"]/self.plays >= .9):
					temp[role] = val
			if(len(temp) > 3):
				del temp[min(temp, key=lambda role:(val["plays"]/self.plays))]
			self.roles = temp

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
						self.add_item(item_id, role, "boots", rating)
					elif(item_id in items_dict):
						if("Jungle" in items_dict[item_id]["tags"]):
							self.add_item(item_id, role, "jung_items", rating)
						else:
							self.add_item(item_id, role, "vis_items", rating)
					else:
						self.add_item(item_id, role, "late", rating)
						#print("item: ", item, " start: ", self.items["start"], " early: ", self.items["early"])

	def add_item(self, item_id, role, stage, rating, win):
		#print("roles: ", self.roles)
		if(item_id not in self.roles[role]["build"][stage]):
			self.roles[role]["build"][stage][item_id] = {"rating":rating, "used":1, "wins":win}
		else:
			self.roles[role]["build"][stage][item_id]["rating"] += rating
			self.roles[role]["build"][stage][item_id]["used"] += 1
			self.roles[role]["build"][stage][item_id]["wins"] += win

	def get_items(self):
		return self.items
