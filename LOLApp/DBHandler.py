from DBModels import *
from playhouse.migrate import *
import operator
import _pickle as cPickle
import sys, psycopg2, time

top_ranks = ["CHALLENGER", "diamondPlus", "DIAMOND", "MASTER"]

"""NEED TO REOWWKR MODELS< FOR EACH ELAGUE THERE IS CHAMPS OVERALL"""
class DBHandler:
	def __init__(self, drop_all_tables=False):
		if(drop_all_tables):
			self.clear_db()
		initialize_db()

	def create_champ_info(self, champ_id, champ_data):
		tag1 = champ_data["tags"][0]
		if(len(champ_data["tags"]) > 1):
			tag2 = champ_data["tags"][1]
		else:
			tag2 = None 
		ChampBase.create(
			champId = champ_id,
			name = champ_data["name"].strip(),
			image = champ_data["image"],
			abilities = cPickle.dumps(champ_data["abilities"]),
			passive = cPickle.dumps(champ_data["passive"]),
			tips = cPickle.dumps(champ_data["tips"]),
			statsRanking = cPickle.dumps(champ_data["stats_ranking"]),
			tag1 = tag1,
			tag2 = tag2,
			role1 = None,
			role2 = None,
			aaRange	= champ_data["stats"]["attackrange"],
			resource = champ_data["resource"],
			movespeed = champ_data["stats"]["movespeed"],
			armor = champ_data["stats"]["armor"],
			armorPL = champ_data["stats"]["armorperlevel"],
			ad = champ_data["stats"]["attackdamage"],
			adPL = champ_data["stats"]["attackdamageperlevel"],
			hp = champ_data["stats"]["hp"],
			hpPL = champ_data["stats"]["hpperlevel"],
			hpRegen = champ_data["stats"]["hpregen"],
			hpRegenPL = champ_data["stats"]["hpregenperlevel"],
			mr = champ_data["stats"]["spellblock"],
			mrPL = champ_data["stats"]["spellblockperlevel"],
			attackspeed = champ_data["stats"]["attackspeed"],
			attackspeedPL = champ_data["stats"]["attackspeedperlevel"],
			mana = champ_data["stats"]["mp"],
			manaPL = champ_data["stats"]["mpperlevel"],
			manaRegen = champ_data["stats"]["mpregen"],
			manaRegenPL = champ_data["stats"]["mpregenperlevel"]	
		)

	def create_spell_info(self, spell_id, spell_data):
		SpellBase.create(
			spellId = spell_id,
			name = spell_data["name"],
			image = spell_data["image"],
			des = spell_data["des"]
		)

	def create_mastery_info(self, mastery_id, mastery_data):
		MasteryBase.create(
			masteryId = mastery_id,
			name = mastery_data["name"],
			des = mastery_data["description"][0]
		)

	def create_rune_info(self, rune_data):
		RuneBase.create(
			runeId = rune_data["id"],
			name = rune_data["name"],
			image = rune_data["image"]["full"],
			des = rune_data["description"]
		)

	def create_item_info(self, item_id, item_tags, item_data):
		if("sanitizedDescription" in item_data):
			item_q = ItemBase.select().where(ItemBase.itemId == item_id)
			if(not item_q.exists()):
				ItemBase.create(
					itemId = item_id,
					name = item_data["name"],
					image = item_data["image"]["full"],
					cost = item_data["gold"]["total"],
					tags = cPickle.dumps(item_tags),
					des = item_data["sanitizedDescription"]
				)
			else:
				item_update_q = ItemBase.select().where(ItemBase.itemId == item_id, ItemBase.cost == item_data["gold"]["total"])
				if(not item_update_q.exists()):
					item_q.get().update(
							name = item_data["name"],
							image = item_data["image"]["full"],
							cost = item_data["gold"]["total"],
							tags = cPickle.dumps(item_tags),
							des = item_data["sanitizedDescription"]
						).execute()
		print(item_data["name"])

	def create_base_info(self, region, league_tier):
		print("region: ", region)
		stats_base_q = StatsBase.select().where(StatsBase.region == region, StatsBase.leagueTier == league_tier)
		if(not stats_base_q.exists()):
			print("not exists")
			StatsBase.create(
				region = region,
				leagueTier = league_tier
			)
		return stats_base_q.get()

	def create_player_basic(self, region, name, account_id, summoner_id, rank):
		#print(rank)
		if(rank not in top_ranks):
			rank = None
		return PlayerBasic.create(
				region=region,
				name=name,
				accountId=account_id,
				summonerId=summoner_id,
				rank=rank
				)

	def create_champ_basic(self, champ_id, role):
		champ_basic_q = ChampBasic.select().where(ChampBasic.champId == champ_id, ChampBasic.role == role)
		if(not champ_basic_q.exists()):
			ChampBasic.create(
				champId = champ_id,
				role = role
				)
		return champ_basic_q.get()

	def create_player(self, base_q, champ_q, player_data):
		PlayerRankStats.create(
			basicInfo = base_q,
			kills = player_data["kills"],
			deaths = player_data["deaths"],
			assists = player_data["assists"],
			performance = player_data["performance"],
			wins = player_data["wins"],
			plays = player_data["plays"],
			champInfo = champ_q			
			)

	def update_player_stats(self, player_query, new_data):
		player_query.kills += new_data["kills"]
		player_query.deaths += new_data["deaths"]
		player_query.assists += new_data["assists"]
		player_query.performance += new_data["performance"]
		player_query.wins += new_data["wins"]
		player_query.plays += new_data["plays"]
		player_query.save()

	def change_player(self, basic_q, old_player_q, new_player_data):
		basic_q.accountId = new_player_data["accountId"]
		basic_q.name = new_player_data["name"]
		basic_q.rank = new_player_data["rank"]
		basic_q.summonerId = new_player_data["summonerId"]
		basic_q.save()
		self.update_player_stats(old_player_q.get(), new_player_data)

	def create_team(self, base, team_id):
		TeamBase.create(
			baseInfo = base,
			teamId = team_id
			)

	def create_team_stats(self, team_query, num_remakes, game_dur, team_stats):
		TeamStats.create(
			teamInfo = team_query,
			gameLength = game_dur,
			numRemakes = num_remakes,
			teamGameStats = cPickle.dumps(team_stats),
		)

	def update_team_stats(self, team_stat_q, new_num_remakes, new_game_dur, new_team_stats):
		#print("old num remakes: ", team_stat_q.numRemakes, " old game_length: ", team_stat_q.gameLength)
		team_stat_q.numRemakes += new_num_remakes
		team_stat_q.gameLength += new_game_dur
		old_stats = cPickle.loads(team_stat_q.teamGameStats)
		for stat,value in new_team_stats.items():
			old_stats[stat] += value
		team_stat_q.teamGameStats = cPickle.dumps(old_stats)
		team_stat_q.save()

	def create_monster(self, monster, monster_subtype, team, stats):
		MonsterStats.create(
			monsterType = monster,
			teamInfo = team,
			kills = stats["killed"],
			wins = stats["wins"],
			time = stats["time"], #if this was the first monster killed, add the time
			games = stats["games"],
			subtypeData = cPickle.dumps(monster_subtype)
		)

	def update_monster_stats(self, monster_query, new_stats):
		monster_query.kills += new_stats["killed"]
		monster_query.wins += new_stats["wins"]
		monster_query.time += new_stats["time"] #if this was the first monster killed, add the time
		monster_query.games += new_stats["games"]
		old_sub_data = cPickle.loads(monster_query.subtypeData)
		if(old_sub_data is not None):
			for drag_type,num_killed in new_stats["types"].items():
				if(drag_type is not None):
					if(drag_type not in old_sub_data):
						old_sub_data[drag_type] = num_killed
					else:
						old_sub_data[drag_type] += num_killed
		monster_query.save()		

	def create_game_info(self):
		pass

	def create_champ_addons(self, values, league_tier):
		if(league_tier != "silverMinus"):
			return ChampAddons.create(
				spells = cPickle.dumps(values["spells"]),
				skillOrder = cPickle.dumps(values["skill_order"]),
				keystone = cPickle.dumps(values["keystone"]),
				items = cPickle.dumps(values["build"]),
				runes = cPickle.dumps(values["runes"]),
				matchups = cPickle.dumps(values["matchups"])
			)
		return None			

	def create_champ_overall_stats(self, region, cur_champ_d):
		overall_q = ChampOverallStats.select().where(
			ChampOverallStats.region == region,
			ChampOverallStats.champId == cur_champ_d.champ_id
			)
		if(not overall_q.exists()):
			return ChampOverallStats.create(
					totalRatingByPatch = cPickle.dumps(cur_champ_d.patch_rating),
					totalPlaysByPatch = cPickle.dumps(cur_champ_d.patch_plays),
					totalBansByPatch = cPickle.dumps(cur_champ_d.patch_bans),
					totalWinsByPatch = cPickle.dumps(cur_champ_d.patch_wins),
					totalRating = cur_champ_d.t_rating,
					totalWins = cur_champ_d.t_wins,
					totalBans = cur_champ_d.t_bans,
					totalPlays = cur_champ_d.t_plays,
					region = region,
					champId = cur_champ_d.champ_id
				).get()
		else:
			old_data = overall_q.get()
			old_data.totalPlaysByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalPlaysByPatch), cur_champ_d.patch_plays))
			old_data.totalBansByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalBansByPatch), cur_champ_d.patch_bans))	
			old_data.totalWinsByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalWinsByPatch), cur_champ_d.patch_wins))	
			old_data.totalRatingByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalRatingByPatch), cur_champ_d.patch_rating))	
			old_data.totalRating += cur_champ_d.t_rating
			old_data.totalWins += cur_champ_d.t_wins
			old_data.totalBans += cur_champ_d.t_bans
			old_data.totalPlays += cur_champ_d.t_plays			
			old_data.save()	
		return overall_q.get()	

	def create_champ_role_stats(self, stats, role, this_patch, league_tier):
		#print("creating overall: id ", cur_champ_d.champ_id, " role: ", role)
		#print(overall_obj, overall_obj.totalWins)
		return ChampOverallStatsByRole.create(
				role = role,
				roleCCDealt = stats["cc_dealt"],
				roleTotalPlays = stats["t_plays"],
				roleTotalWins = stats["t_wins"],
				roleTotalRating = stats["t_rating"],
				laning = stats["laning"],
				addons = self.create_champ_addons(stats, league_tier)
			)

	def create_champ_rank_stats(self, contribution, rank_stats, champ_d, base, this_patch, role, role_overall):
		#print("creating rank stats, role: ", role)
		ChampStatsByRank.create(
			gameStats = cPickle.dumps(contribution),
			patchStats = cPickle.dumps(rank_stats["patches_stats"]),
			kills = rank_stats["kda"]["kills"],
			deaths = rank_stats["kda"]["deaths"],
			assists = rank_stats["kda"]["assists"],
			cspm = rank_stats["cspm"],
			gpm = rank_stats["gpm"],
			resultByTime = cPickle.dumps(rank_stats["game_result"]),
			champId = champ_d.champ_id,
			baseInfo = base,
			overallStats = role_overall
		)

	def add_players_db(self, champ_basic_q, region, players):
		#print(players)
		for player,data in players.items():
			all_players_this_champ_q = PlayerRankStats.select().join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
				PlayerBasic.region == region, 
				ChampBasic.champId == champ_basic_q.champId
				)
			if(all_players_this_champ_q.count() < 5):
				player_basic_q = PlayerBasic.select().where(PlayerBasic.region == region, PlayerBasic.accountId == data["accountId"])
				if(not player_basic_q.exists()):
					base = self.create_player_basic(region, data["name"], data["accountId"], data["summonerId"], data["rank"])
					self.create_player(base, champ_basic_q, data)
				else:
					player_stats_q = PlayerRankStats.select().join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
						PlayerBasic.region == region, 
						PlayerBasic.accountId == data["accountId"],
						ChampBasic.champId == champ_basic_q.champId
						)
					if(player_stats_q.exists()):
						self.update_player_stats(player_stats_q.get(), data)
					else:
						self.create_player(player_basic_q.get(), champ_basic_q, data)					
			else:
				for old_player in PlayerRankStats.select().join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
					PlayerBasic.region == region, 
					ChampBasic.champId == champ_basic_q.champId
					):
					if(old_player.basicInfo.accountId == data["accountId"]):
						self.update_player_stats(old_player, data)
						break;
					elif(data["rank"] in top_ranks and (data["performance"]/data["plays"]) > (old_player.performance/old_player.plays)):
						basic_q = PlayerBasic.get(
							PlayerBasic.accountId == old_player.basicInfo.accountId, 
							PlayerBasic.region == old_player.basicInfo.region)
						self.change_player(basic_q, old_player, data)
						break;

	def get_team(self, team_id, league_tier, region, base):
		team_q = TeamBase.select().join(StatsBase).where(StatsBase.region == region, TeamBase.teamId == team_id, StatsBase.leagueTier == league_tier)
		if(not team_q.exists()):
			self.create_team(base, team_id)
		return team_q.get()

	"""Need to fix, as well as update code in crawler"""
	def add_monsters_db(self, teams, league, region, base):
		for team,monster_stats in teams.items():
			team_ref = self.get_team(team, league, region, base)
			for mon,stats in monster_stats.items():
				#print("mon: ", mon, " stats: ", stats)
				#print(mon, " w: ",  stats["wins"], " k: ", stats["kills"])
				mon_query = MonsterStats.select().join(TeamBase).join(StatsBase).where(
					MonsterStats.monsterType == mon, 
					StatsBase.region == region,
					TeamBase.teamId == team,
					StatsBase.leagueTier == league
					)
				if(not mon_query.exists()):
					if("types" in stats):
						subtype_data = stats["types"]
					else:
						subtype_data = None 
					self.create_monster(mon, subtype_data, team_ref, stats)
				else:
					self.update_monster_stats(mon_query.get(), stats)

	def add_teams_db(self, teams_dict, game_dur, league, region, num_remakes, base):
		#print("duration team: ", game_dur)
		if(teams_dict[100]["wins"] + teams_dict[200]["wins"] > 0):
			for team,val in teams_dict.items():
				team_ref = self.get_team(team, league, region, base)
				if(len(team_ref.team_stats) <= 0):
					self.create_team_stats(team_ref, num_remakes, game_dur, val)
				else:
					self.update_team_stats(team_ref.team_stats.get(), num_remakes, game_dur, val)

	def add_games_visited_db(self, games_visited_list, games_visited):
		#print(games_visited)
		#time.sleep(5)
		try:
			with postgres_db.atomic():
				for i in range(0, len(games_visited), 100):
					GamesVisited.insert_many(games_visited[i:i+100]).execute()
		except IntegrityError as e:
			raise ValueError("already exists", e)

	def add_champ_stats(self, champs_list, cur_patch, base):
		for champ in champs_list:
			cur_champ = champs_list[champ]
			print(cur_champ)
			champ_id = cur_champ.champ_id
			if(champ_id != -1):
				region = base.region
				league = base.leagueTier
				self.create_champ_overall_stats(region, cur_champ)
				for role, stats in cur_champ.roles.items():
					print("role: ", role)
					self.add_players_db(self.create_champ_basic(champ_id, role), region, stats["players"])
					cur_champ.get_best_players(role)
					#cur_champ.sort_matchups(role)
					champ_role_overall_q = ChampOverallStatsByRole.select().join(ChampStatsByRank).switch(ChampStatsByRank).join(StatsBase).where(
										ChampOverallStatsByRole.role == role,
										ChampStatsByRank.champId == champ_id,
										StatsBase.region == region,
										)
					contribution_stats = {"dpg": stats["damage_dealt_per_gold"],
									"dmpg": stats["damage_mitigated_per_gold"],
									"visScore": stats["vision"],
									"objScore": stats["objectives"]
									}
					champ = champ_id
					print("id: ", champ, " role: ", role)
					#print("total plays: ", cur_champ.plays, " this role patch stats: ", stats["patches_stats"])
					if(not champ_role_overall_q.exists()):
						print("overall does not exist: ", champ_id, " role: ", role)
						all_overall = ChampOverallStatsByRole.select().join(ChampStatsByRank).join(StatsBase).where(
							ChampStatsByRank.champId == champ_id,
							StatsBase.region == region
							)
						for old_role in all_overall:
							print("roles from db: ", old_role.role)
						role_overall = self.create_champ_role_stats(stats, role, cur_patch, league)
						self.create_champ_rank_stats(contribution_stats, stats, cur_champ, base, cur_patch, role, role_overall)
						#self.add_players_to_db(champ_overall, stats["players"], cur_champ.champ_id, role)
					else:
						role_overall = champ_role_overall_q.get()
						print("t plays: ", role_overall.roleTotalPlays)
						self.update_role_stats(role_overall, stats, cur_patch, league)
						league_tier_stats_q = ChampStatsByRank.select().join(StatsBase).switch(ChampStatsByRank).join(ChampOverallStatsByRole).where(
							StatsBase.leagueTier == league, ChampStatsByRank.champId == champ_id, 
							StatsBase.region == region, ChampOverallStatsByRole.role == role)
						if(league_tier_stats_q.exists()):
							self.update_rank_stats(league_tier_stats_q.get(), stats, contribution_stats)
						else:
							if(role_overall.addons == None and league != "silverMinus"):
								role_overall.addons = self.create_champ_addons(stats, league)
								role_overall.save()
							self.create_champ_rank_stats(contribution_stats, stats, cur_champ, base, cur_patch, role, role_overall)
	
	def update_patch_stats(self, old_patch_stats, new_patch_stats):
		for patch,val in new_patch_stats.items():
			print("patch: ", patch, " val: ", val)
			if(patch not in old_patch_stats):
				old_patch_stats[patch] = val
			else:
				old_patch_stats[patch] += val
		return old_patch_stats
	
	def update_role_stats(self, old_data, new_data, patch, tier, from_db=False):
		#helper functions		
		def update_attribute(old, new, attribute):
			#print("old: ", old, " new: ", new, " type: ", attribute)
			if(old != None):
				if(attribute != "spells" and attribute != "keystone" and attribute != "matchups"):
					if(attribute == "skill order"):
						if(len(new) > len(old)):
							old,new = new,old
					print("old: ", old, "\n", " new: ", new)
					for old_type,old_values in old.items():
						if(old_type in new):
							for item,data in new[old_type].items():
								if(item in old[old_type]):
									#print("old: ", old[old_type][item], " new = key: ", item, " val: ", data)
									for key,val in data.items():
										#print("old: ", old[old_type][item], " new = key: ", key, " val: ", val)
										if(key != "rune_ids"):
											old[old_type][item][key] += val
								else:
									old[old_type][item] = data	
				else:
					for item,stats in new.items():
						if(item in old):
							#print("item: ", item, " old: ", old, " new: ", new)
							for stat,val in stats.items():
								if(stat != "info" and stat != "spells_id"):
									old[item][stat] += val				
								elif(stat == "info"):
									old[item][stat] = val
						else:
							old[item] = stats
			else:
				old = new
			#print("old updated: ", old)
			return old

		old_addons = old_data.addons
		#print("print addon item:", old_addons)
		if(tier != "silverMinus"):	
			if(old_addons is not None):
				if(from_db):
					new_addons = new_data.addons
					if(new_addons is not None):
							old_addons.skillOrder = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.skillOrder), 
								cPickle.loads(new_addons.skillOrder), "skill order"))	
							old_addons.spells = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.spells), 
								cPickle.loads(new_addons.spells), "spells"))
							old_addons.runes = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.runes), 
								cPickle.loads(new_addons.runes), "runes"))
							old_addons.keystone = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.keystone), 
								cPickle.loads(new_addons.keystone), "keystone"))
							old_addons.matchups = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.matchups), 
								cPickle.loads(new_addons.matchups), "matchups"))
							old_addons.items = cPickle.dumps(update_attribute(
								cPickle.loads(old_addons.items), 
								cPickle.loads(new_addons.items), "items"))
							old_addons.save()
				else:
					old_addons.skillOrder = cPickle.dumps(update_attribute(cPickle.loads(old_addons.skillOrder), new_data["skill_order"], "skill order"))	
					old_addons.spells = cPickle.dumps(update_attribute(cPickle.loads(old_addons.spells), new_data["spells"], "spells"))
					old_addons.runes = cPickle.dumps(update_attribute(cPickle.loads(old_addons.runes), new_data["runes"], "runes"))
					old_addons.keystone = cPickle.dumps(update_attribute(cPickle.loads(old_addons.keystone), new_data["keystone"], "keystone"))
					old_addons.matchups = cPickle.dumps(update_attribute(cPickle.loads(old_addons.matchups), new_data["matchups"], "matchups"))
					old_addons.items = cPickle.dumps(update_attribute(cPickle.loads(old_addons.items), new_data["build"], "items"))
					old_addons.save()			
			else:
				if(not from_db):
					old_data.addons = self.create_champ_addons(new_data, tier)		
				else:
					old_data.addons = new_data.addons
		#also need to update items			
		#print("league: ", league_champ_q.get().champ.role)
		if(not from_db):
			print("498: ", patch, new_data["patches_stats"])
			old_data.roleTotalPlays += new_data["t_plays"]
			old_data.roleTotalWins += new_data["t_wins"]
			old_data.roleTotalRating += new_data["t_rating"]	
			old_data.roleCCDealt += new_data["cc_dealt"]
			old_data.laning += new_data["laning"]
		else:
			old_data.roleTotalPlays += new_data.roleTotalPlays
			old_data.roleTotalWins += new_data.roleTotalWins
			old_data.roleTotalRating += new_data.roleTotalRating
			old_data.roleCCDealt += new_data.roleCCDealt
		old_data.save()

	def update_rank_stats(self, old_champ_stats, new_stats, new_game_scores):
		old_champ_stats.patchStats = self.update_patches_stats(cPickle.loads(old_champ_stats.patchStats), new_stats["patches_stats"])
		old_champ_stats.resultByTime = self.update_game_results(cPickle.loads(old_champ_stats.resultByTime), new_stats["game_result"])

		old_game_stats = cPickle.loads(old_champ_stats.gameStats)
		old_game_stats["dpg"] += new_game_scores["dpg"]
		old_game_stats["dmpg"] += new_game_scores["dmpg"]
		old_game_stats["visScore"] += new_game_scores["visScore"]
		old_game_stats["objScore"] += new_game_scores["objScore"]
		"""
		for game_stat,val in old_game_stats.items():
			print("current stat name: ", game_stat, " current value: ", val, " new val: ", new_game_scores[game_stat])
			val += new_game_scores[game_stat]
			print("val after: ", val)
			#time.sleep(3)
		"""
		old_champ_stats.gameStats = cPickle.dumps(old_game_stats)

		old_champ_stats.kills += new_stats["kda"]["kills"]
		old_champ_stats.deaths += new_stats["kda"]["deaths"]
		old_champ_stats.assists += new_stats["kda"]["assists"]
		old_champ_stats.cspm += new_stats["cspm"]
		old_champ_stats.gpm += new_stats["gpm"]
		old_champ_stats.save()

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
		#print("old: ", old_patches_stats)
		#print("new: ", new_patches_stats)		
		for patch,match_data in new_patches_stats.items():
			if(patch not in old_patches_stats):
				old_patches_stats[patch] = match_data
			else:
				old_patches_stats[patch]["wins"] += match_data["wins"]
				old_patches_stats[patch]["rating"] += match_data["rating"]
				old_patches_stats[patch]["plays"] += match_data["plays"]
		return cPickle.dumps(old_patches_stats)

	
	def add_column(table_name, new_col_name, new_col_field):
		my_db = Sqlitepostgres_db('ScryerTest.db')
		migrator = SqliteMigrator(my_db)

		migrate(
			migrator.add_column(table_name, new_col_name, new_col_field)
		)


	def print_data(self, static=True):
		"""
		roles = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).join(StatsBase).where(
			StatsBase.region == "NA",
			ChampStatsByRank.champId == 1
			)
		
		champs = ChampStatsByRank.select().join(StatsBase).where(StatsBase.region == "EUW")
		for champ in champs:
			print(champ.champId)
		"""
		all_games = GamesVisited.select().join(StatsBase).where(StatsBase.region == "NA")
		visited = []
		for game in all_games:
			if(game.matchId not in visited):
				print(game.matchId)
				visited.append(game.matchId)
			else:
				print("duppp")

	def clear_db(self):
		conn = psycopg2.connect("dbname=" + db_name + " user='postgres' password='1WILLchange!'")
		conn.set_isolation_level(0)
		cur = conn.cursor()
		try:
			cur.execute("SELECT table_schema,table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_schema,table_name")
			rows = cur.fetchall()
			for row in rows:
				print("dropping table: ", row[1])   
				cur.execute("drop table " + row[1] + " cascade") 
			cur.close()
			conn.close()
		except:
			print("Error: ", sys.exc_info()[1])

	def clear_static_data(self):
		RuneBase.delete().where(RuneBase.runeId != None).execute()
		ChampBase.delete().where(ChampBase.champId != None).execute()
		SpellBase.delete().where(SpellBase.spellId != None).execute()
		MasteryBase.delete().where(MasteryBase.masteryId != None).execute()
		ItemBase.delete().where(ItemBase.itemId != None).execute()

	def remove_db_items(self):
		ChampOverallStats.delete().where(ChampOverallStats.champId == -1).execute()

	def merge_roles(self):
		bot_champs_and_roles = ChampOverallStatsByRole.select().where(
			(ChampOverallStatsByRole.role == "Bot Support") | (ChampOverallStatsByRole.role == "Bot Carry"))
		"""
		for champ_role in bot_champs_and_roles:
			if(champ_role.role == "Bot Support"):
				old_support_data = ChampOverallStatsByRole.select().join(ChampStatsByRank).where(
					ChampOverallStatsByRole.role == "Support",
					ChampStatsByRank.champId == champ_role.stats_by_league.get().champId
					)
				if(old_support_data.exists()):
					self.update_role_stats(champ_role, old_support_data.get(), "7.14.1", "diamondPlus", True)
				else:
					champ_role.role = "Support"
					champ_role.save()					
			elif(champ_role.role == "Bot Carry"):
				old_adc_data = ChampOverallStatsByRole.select().join(ChampStatsByRank).where(
					ChampOverallStatsByRole.role == "ADC",
					ChampStatsByRank.champId == champ_role.stats_by_league.get().champId
					)
				if(old_adc_data.exists()):
					self.update_role_stats(champ_role, old_adc_data.get(), "7.14.1", "diamondPlus", True)
				else:
					champ_role.role = "ADC"
					champ_role.save()		
		"""
		for champ_role in bot_champs_and_roles:
			champ_role.delete_instance()

	def delete_dups(self):
		dups = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).switch(ChampStatsByRank).join(StatsBase).where(
			ChampStatsByRank.champId == 1,
			StatsBase.region == "NA"
			).aggregate_rows()
		for champ_role in dups:
			print(champ_role.id, champ_role.role, champ_role.roleTotalPlays, champ_role.laning, champ_role.roleCCDealt, champ_role.roleTotalWins, champ_role.roleTotalRating)

	def fix_matchups_dict(self):
		all_addons = ChampAddons.select()
		for addon in all_addons[:10]:
			matchups_new = {}
			matchups_d = cPickle.loads(addon.matchups)
			if("weak_against" in matchups_d):
				print("ERROR", matchups_d)
			if("strong_against" in matchups_d):
				print("ERROR", matchups_d)

	def fix_duplicate_spells(self):
		all_addons = ChampAddons.select()
		for addon in all_addons:
			spells_dict = cPickle.loads(addon.spells)
			for spell_group_key,spell_group_stats in spells_dict.items():
				if(len(spell_group_stats["spells_id"]) > 2):
					print("Spells: ", spells_dict)
			#addon.spells = cPickle.dumps(spells_dict)
			#addon.save()
			#time.sleep(4)

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
				#print("before: ", game.Patch)
				creation = self.get_match_details(game.matchId)["gameCreation"]/1000
				#print(creation)
				if(creation >= 1499875845):
					patch = "7.14.1"
				elif(creation >= 1498608682):
					patch = "7.13.1"
				elif(creation >= 1497399082):
					patch = "7.12.1"
				#print("patch: ", patch)
				if(GamesVisited.get(GamesVisited.region == region, GamesVisited.matchId == game.matchId).Patch != patch):
					game_q = GamesVisited.update(Patch=patch).where(GamesVisited.region == region, GamesVisited.matchId == game.matchId)
					game_q.execute() # Will do the SQL update query.
					print("after: ", GamesVisited.get(GamesVisited.region == region, GamesVisited.matchId == game.matchId).Patch)
			#region_games.save()
			#print(GamesVisited.select().where(GamesVisited.region == "NA", GamesVisited.Patch == self.current_patch).count())

	def add_champ_roles(self):
		all_champs = ChampBase.select()
		for champ in all_champs:
			champ_overall = ChampOverallStats.select().where(ChampOverallStats.champId == champ.champId)
			total_plays = 0
			for region in champ_overall:
				total_plays +=  region.totalPlays
			champ_roles = ChampOverallStatsByRole.select(ChampOverallStatsByRole, ChampStatsByRank).join(ChampStatsByRank).where(ChampStatsByRank.champId == champ.champId).aggregate_rows()
			roles = {}
			print("champ: ", champ.name)
			for champ_role in champ_roles:
				if(champ_role.role not in roles):
					roles[champ_role.role] = champ_role.roleTotalPlays
				else:
					roles[champ_role.role] += champ_role.roleTotalPlays
			most_common_roles = dict(sorted(roles.items(), key=operator.itemgetter(1), reverse=True)[:2])
			for role,plays in most_common_roles.items():
				role_playrate = plays/total_plays
				if(role_playrate > .5 and champ.role1 is None):
					champ.role1 = role
				elif(role_playrate > .1 and champ.role2 is None):
					champ.role2 = role
				champ.save()
				print("role: ", role, " playrate: ", (plays/total_plays)*100)
			#time.sleep(5)

	def close(self):
		postgres_db.close()

if __name__=="__main__":
	test = DBHandler()
	test.add_champ_roles()