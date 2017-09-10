import _pickle, json
from .DBModels import *

def get_global_avg(all_champ_data):
	overall_rank_stats = {"kills":0, "deaths":0, "assists":0, "rating":0, "total_dmpg":0, "total_dpg":0, "total_vis":0, "total_obj":0, "rating":0, "laning":0}
	total_plays_this_patch = 0
	total_plays = 0
	overall_stats = ChampOverallStats.select()
	for role_champ in all_champ_data:
		total_plays_this_patch += role_champ.roleTotalPlays
		#if(role_champ.roleTotalPlays <= 0):
			#print(role_champ.role, role_champ.stats_by_league.get().champId, role_champ.stats_by_league.get().baseInfo.region)
		#print("t plays: ", role_champ.roleTotalRating, " role: ", role_champ.role)
		overall_rank_stats["laning"] += role_champ.laning
		overall_rank_stats["rating"] += role_champ.roleTotalRating
		for league_champ in role_champ.stats_by_league:
			game_dt = _pickle.loads(league_champ.patchStats)
			for patch,stats in game_dt.items():
				total_plays += stats["plays"]
			overall_rank_stats["kills"] += league_champ.kills
			overall_rank_stats["deaths"] += league_champ.deaths
			overall_rank_stats["assists"] += league_champ.assists
			league_champ.gameStats = _pickle.loads(league_champ.gameStats)

			overall_rank_stats["total_dmpg"] += league_champ.gameStats["dmpg"]
			overall_rank_stats["total_dpg"] += league_champ.gameStats["dpg"]
			overall_rank_stats["total_vis"] += league_champ.gameStats["visScore"]
			overall_rank_stats["total_obj"] += league_champ.gameStats["objScore"]
	#print("dpg: ", overall_rank_stats["total_dpg"], " total plays: ", total_plays)
	#print("laning: ", overall_rank_stats["laning"], " true total plays: ", total_plays)
	return [
			round((overall_rank_stats["rating"]/total_plays), 2),
			round((overall_rank_stats["kills"]+overall_rank_stats["assists"])/overall_rank_stats["deaths"],2),
			round((overall_rank_stats["laning"]/total_plays)*2,2),
			{'value': round((overall_rank_stats["total_dpg"]/total_plays),2),'label': "Damage per gold"},
			{'value': round((overall_rank_stats["total_dmpg"]/total_plays),2), 'label': "Damage Mitigated per gold"},
			round((overall_rank_stats["total_vis"]/total_plays),2),	
			round((overall_rank_stats["total_obj"]/total_plays),2)		
			]

def get_matchups(matchups):
	while(len(matchups) > 15):
		del matchups[min(matchups, key=lambda matchup:matchups[matchup]["used_against"])]
	temp = {"weak_against":{}, "strong_against":{}}
	for matchup,stats in matchups.items():
		#print(matchup, stats)
		if(len(temp["strong_against"]) < 5 and len(temp["weak_against"]) < 5):
			champ_q = ChampBase.get(ChampBase.champId == matchup)
			if(stats["perf_against"]/stats["used_against"] > 0.01 and len(temp["strong_against"]) < 5):
				temp["strong_against"][matchup] = stats
				temp["strong_against"][matchup]["image"] = champ_q.image
				temp["strong_against"][matchup]["name"] = champ_q.name
			elif(stats["perf_against"]/stats["used_against"] < -.01 and len(temp["weak_against"]) < 5):
					temp["weak_against"][matchup] = stats
					temp["weak_against"][matchup]["image"] = champ_q.image
					temp["weak_against"][matchup]["name"] = champ_q.name
	return temp

def get_best_build(items_list, role_plays, role, champ_key):
	#print("items: ", items)
	if(role == "Support" or role == "Jungle"):
		limit = 2
	else:
		limit = 3
	for stage,items in items_list.items():
		#print("stage: ", stage)
		remove_rare_items(items, role_plays, stage)
	get_boots(items_list)
	get_core(items_list)
	build_cont = []
	build_categories = ["start", "consumables", "core", "boots", "early_ahead", "early_behind", "situational"]
	filter_items(items_list, "late", role_plays*.2, limit)
	filter_items(items_list, "start", role_plays*.2, limit)
	for item_categ in build_categories:
		if(item_categ in items_list and len(items_list[item_categ]) > 0):
			build_cont.append(items_list[item_categ])

	item_set_file_name = "LOLApp/static/item_sets/" + champ_key + "SR.json"

	item_set_type_key = ["Starting Items", "Consumables", "Core", "Boots", "Early Ahead", "Early Behind", "Situational"]
	item_blocks = []
	loop_index = 0
	for champ_items in build_cont:
		if(len(champ_items) > 0):
			item_block = {
					"type": item_set_type_key[loop_index],
					"recMath": False,
					"minSummonerLevel": -1,
					"maxSummonerLevel": -1,
					"showIfSummonerSpell": "",
					"hideIfSummonerSpell": "",
					"items": []
				}
			print(item_block)
			loop_index += 1
			for item_id, item_data in champ_items.items():
				item_block["items"].append({
					"id": item_id,
					})
				item_q = ItemBase.get(ItemBase.itemId == item_id)
				item_data["name"] = item_q.name
				item_data["image"] = item_q.image
				item_data["des"] = item_q.des
				item_data["cost"] = item_q.cost
			item_blocks.append(item_block)
	item_set = {
		"title": champ_key + " build",
		"type": "custom",
		"map": "SR",
		"mode": "CLASSIC",
		"priority": True,
		"sortrank": 0,
		"blocks": item_blocks

	}
	with open(item_set_file_name, "w") as outfile:
		json.dump(item_set, outfile)
	#print(item_set)
	#print(build_cont)
	return build_cont


def get_boots(items_block):
	boots = items_block["boots"]
	temp = {}
	while(len(boots) > 2):
		best_boot = max(boots, key=lambda boot:boots[boot]["rating"]/boots[boot]["used"])
		if(best_boot in items_block["core"]):
			del items_block["core"][best_boot]
		temp[best_boot] = boots[best_boot]
		del boots[best_boot]

def remove_rare_items(items_block, num_plays, stage):
	print(stage, " len of items block before: ", len(items_block))
	if(len(items_block) > 3):
		if(stage == "late"):
			threshold = int(round(len(items_block)/5))
		else:
			threshold = int(round(len(items_block)/3))
		while(len(items_block) > threshold):
			del items_block[min(items_block, key=lambda item:items_block[item]["used"])]
	print(stage, " len of items block after: ", len(items_block))

def filter_runes(runes_list, total_role_plays):
	#print("runes b: ", runes_list)
	rune_type_names = {"reds":"Marks", "yellows":"Seals", "blues":"Glyphs", "blacks":"Quints"}
	for rune_type,runes in runes_list.items():
		while(len(runes) > 3):
			del runes_list[rune_type][min(runes_list[rune_type], key=lambda r:runes_list[rune_type][r]["used"])]
		while(len(runes) > 1):
			del runes_list[rune_type][min(runes_list[rune_type], key=lambda r:runes_list[rune_type][r]["perf"]/runes_list[rune_type][r]["used"])]
	#print("runes b: ", runes_list)
	runes_clean = []
	for rune_type,runes_block in runes_list.items():
		for rune_code,rune_data in runes_block.items():
			best_runes = []
			for rune_key,rune_id in rune_data["rune_ids"].items():
				print(rune_data)
				rune_q = RuneBase.get(RuneBase.runeId == rune_id)
				best_runes.append({
					"name":rune_q.name, 
					"des": rune_q.des,
					"image":rune_id, 
					"count":int(rune_key/rune_id)
					})
			runes_clean.append({
				"type":rune_type_names[rune_type],
				"runes":best_runes,  
				"use_rate":round((rune_data["used"]/total_role_plays)*100, 1),
				"performance": round(rune_data["perf"]/rune_data["used"],2) 
				})
	#print("runes: ", runes_clean)
	return runes_clean

def filter_items(build, stage, role_plays, limit):
	stage_items = build[stage]
	print("items before: ", stage_items)
	if(stage == "late"):
		used_index = 0
		while(used_index < 2):
			if(len(stage_items) > 0):
				core_item = max(stage_items, key=lambda item:stage_items[item]["used"])
				stats = stage_items[core_item]
				build["core"][core_item] = stage_items[core_item]
				del stage_items[core_item]			
				used_index += 1
			else:
				break
		if(len(stage_items) > 1):
			core_item_2 = max(stage_items, key=lambda item:(stage_items[item]["rating"]/stage_items[item]["used"]))
			#print("add to core: ", stage_items[core_item_2]["info"]["name"], " rating: ", stage_items[core_item_2]["rating"])
			stats = stage_items[core_item_2]
			build["core"][core_item_2] = stage_items[core_item_2]
			del stage_items[core_item_2]		
		build["situational"] = {}
		for item, stats in stage_items.items():
			if(item not in build["core"] and item not in build["early_behind"] and item not in build["early_ahead"]):
				build["situational"][item] = stage_items[item]
		del build[stage]
	else:
		temp = {}
		num_starting_items = 0
		print("Before stage: ", stage, " items: ", stage_items)
		if(len(stage_items) > limit):
			cont = True
			while(num_starting_items < limit and cont):
				cont = False
				cur_rating = -900
				cur_item = -1
				for item,stats in stage_items.items():
					if((item not in temp and item not in build["consumables"]) and stats["rating"] > cur_rating and stats["used"] > role_plays):
						cur_item = item
						cur_rating = stats["rating"]
				print("current item: ", cur_item)
				if(cur_item != -1 and (cur_item not in temp and cur_item not in build["consumables"])):
					cont = True
					print("item id? ", cur_item, " temp: ", temp)
					item_tags = _pickle.loads(ItemBase.get(ItemBase.itemId == cur_item).tags)
					print("tags: ", item_tags)
					#don't count trinkets and refillable potion
					if(item_tags is not None and "Trinket" not in item_tags):
						if(cur_item == 2031):
							build["consumables"][cur_item] = stage_items[cur_item]
						else:
							temp[cur_item] = stage_items[cur_item]
							num_starting_items += 1
					else:
						temp[cur_item] = stage_items[cur_item]

			#print("After stage: ", stage, " items: ", temp)
			build[stage] = temp

def filter_attribute(data, num, att=None):
	#print(data)
	while(len(data) > (num * 2)):
		del data[min(data, key=lambda k:data[k]["used"])]
	while(len(data) > num):
		del data[min(data, key=lambda k:data[k]["perf"]/data[k]["used"])]
	print(len(SpellBase.select()))
	if(att == "spells"):
		for spell_combo_key,stats in data.items():
			spells_info = []
			#print("SPELLS: ", stats["spells_id"])
			for spell in stats['spells_id']:
				spell_info = SpellBase.get(SpellBase.spellId == spell)
				temp = {"name": spell_info.name, "image": spell_info.image, "des": spell_info.des}
				spells_info.append(temp)
			stats["spells"] = spells_info
		print("spells: ", data)
	elif(att == "keystone"):
		for keystone,stats in data.items():
			print(stats)
	return data

def get_core(build):
	if(len(build["early_ahead"]) > 0):
		item = max(build["early_ahead"], key=lambda item:build["early_ahead"][item]["rating"]/build["early_ahead"][item]["used"])
		temp = {}
		temp[item] = build["early_ahead"][item]
		if(item in build["late"]):
			del build["late"][item]
		build["early_ahead"] = temp
	if(len(build["early_behind"]) > 0):	
		item = max(build["early_behind"], key=lambda item:build["early_behind"][item]["rating"]/build["early_behind"][item]["used"])
		temp = {}
		temp[item] = build["early_behind"][item]
		if(item in build["late"]):
			del build["late"][item]
		if(item in build["early_ahead"]):
			build["early_ahead"] = []
			build["core"] = temp
			build["early_behind"] = []
		else:		
			build["early_behind"] = temp
	if(len(build["jung_items"]) > 0):
		best_jung_item = max(build["jung_items"], key=lambda item:build["jung_items"][item]["rating"]/build["jung_items"][item]["used"])
		build["core"][best_jung_item] = build["jung_items"][best_jung_item]
	if(len(build["vis_items"]) > 0):
		best_vis_item = max(build["vis_items"], key=lambda item:build["vis_items"][item]["rating"]/build["vis_items"][item]["used"])
		build["core"][best_vis_item] = build["vis_items"][best_vis_item]
	if(len(build["attk_speed_items"]) > 1):
		best_as_item = max(build["attk_speed_items"], key=lambda item:build["attk_speed_items"][item]["used"])
		build["core"][best_as_item] = build["attk_speed_items"][best_as_item]
	del build["jung_items"]
	del build["vis_items"]
	del build["attk_speed_items"]
	#build["early_ahead"] = temp

def get_skill_order(skills_list, champ):
	temp = {}
	skill_rank = {1:0, 2:0, 3:0, 4:0}
	transforming_champs = ["Jayce", "Nidalee", "Elise", "Quinn"]
	ult_lvls = [6, 11, 16]
	if(champ == transforming_champs[0]):
		limit = 6
	else:
		limit = 5
	#print("skill order: ", self.roles[role]["skill_order"].items())
	for lvl,skills in skills_list.items():
		#print(lvl, " skills: ", skills)
		#print(skill_rank)
		while(True):
			if(len(skills) > 0):
				if(champ not in transforming_champs and lvl in ult_lvls):
					skill = 4
				else:
					skill = get_best_skill(skills)
					print("skill: ", skill, " lv: ", lvl, " rank: ", skill_rank[skill], " det: ", lvl/2, " less? ", lvl/2 > skill_rank[skill])

				if(skill == 4):
					if(skill_rank[skill] < 3 and lvl >= ult_lvls[skill_rank[skill]]):
						temp[lvl] = skill
						skill_rank[skill] += 1
						break;
					else:
						del skills[skill]
				else:
					if(skill_rank[skill] < limit and ((lvl/2) > skill_rank[skill])):
						temp[lvl] = skill
						skill_rank[skill] += 1		
						break;		
					else:		
						del skills[skill]
			else:
				break
	#print("skill order: ", temp)
	return temp

def get_best_skill(skills_dict):
	print("skills: ", skills_dict)
	while(len(skills_dict) > 3):
		#skill_used_least = min(skills_dict, key=lambda skill:skills_dict[skill]["used"])
		del skills_dict[min(skills_dict, key=lambda skill:skills_dict[skill]["perf"]/skills_dict[skill]["used"])]
		#print("deleting: ", skill_used_least, " uses: ", skills_dict[skill_used_least]["used"])
		#del skills_dict[skill_used_least]
	return max(skills_dict, key=lambda skill:skills_dict[skill]["used"])