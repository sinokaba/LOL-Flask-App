from DBModels import *
from playhouse.migrate import *
import _pickle as cPickle
import sys, psycopg2


"""NEED TO REOWWKR MODELS< FOR EACH ELAGUE THERE IS CHAMPS OVERALL"""
class DBHandler:
	def __init__(self, drop_all_tables=False):
		if(drop_all_tables):
			self.clear_db()
		initialize_db()

	def create_champ_info(self, stats_ranking, champ_data):
		ChampBase.create(
			champId = champ_data["id"],
			name = champ_data["name"].strip(),
			image = champ_data["image"]["full"],
			abilities = cPickle.dumps(champ_data["spells"]),
			passive = cPickle.dumps(champ_data["passive"]),
			tips = cPickle.dumps({"enemy":champ_data["enemytips"], "ally":champ_data["allytips"]}),
			statsRanking = cPickle.dumps(stats_ranking)
		)

	def create_item_info(self, item_id, item_tags, item_data):
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

	def create_player_basic(self, region, name, account_id, rank):
		print(rank)
		return PlayerBasic.create(
				region=region,
				name=name,
				accountId=account_id
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
		print("old num remakes: ", team_stat_q.numRemakes, " old game_length: ", team_stat_q.gameLength)
		team_stat_q.numRemakes += new_num_remakes
		team_stat_q.gameLength += new_game_dur
		old_stats = cPickle.loads(team_stat_q.teamGameStats)
		for stat,value in new_team_stats.items():
			old_stats[stat] += value
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
		overall_q = ChampOverallStats.select().join(ChampOverallStatsByRole).switch(ChampOverallStatsByRole).join(ChampStatsByRank).switch(ChampStatsByRank).join(StatsBase).where(
			StatsBase.region == region,
			ChampStatsByRank.champId == cur_champ_d.champ_id
			)
		if(not overall_q.exists()):
			ChampOverallStats.create(
				totalRating = cur_champ.oa_rating,
				totalPlaysByPatch = cPickle.dumps(cur_champ_d.patch_plays),
				totalBansByPatch = cPickle.dumps(cur_champ_d.patch_bans),
				totalWins = cur_champ.wins
				)
		else:
			old_data = overall_q.get()
			old_data.totalPlaysByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalPlaysByPatch), new_patch_plays))
			old_data.totalBansByPatch = cPickle.dumps(self.update_patch_stats(cPickle.loads(old_data.totalBansByPatch), new_patch_bans))	
			old_data.totalWins += cur_champ.wins
			old_data.totalRating += cur_champ.oa_rating
			old_data.save()	
		return overall_q.get()		

	def create_champ_role_stats(self, stats, role, this_patch, league_tier, overall_obj):
		#print("creating overall: id ", cur_champ_d.champ_id, " role: ", role)
		if(this_patch in stats["patches_stats"]):
			t_plays = stats["patches_stats"][this_patch]["plays"]
			t_wins = stats["patches_stats"][this_patch]["wins"]
			t_rating = stats["patches_stats"][this_patch]["rating"]
		else:
			t_plays = t_wins = t_rating = 0
		return ChampOverallStatsByRole.create(
				role = role,
				roleCCDealt = stats["cc_dealt"],
				roleTotalPlays = t_plays,
				roleTotalWins = t_wins,
				roleTotalRating = t_rating,
				addons = self.create_champ_addons(stats, league_tier),
				overall = overall_obj
			)

	def create_champ_rank_stats(self, contribution, rank_stats, champ_d, base, this_patch, role, overall):
		print("creating rank stats, role: ", role)
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
			overallStats = overall
		)

	def add_players_db(self, champ_basic_q, region, players):
		print(players)
		for player,data in players.items():
			all_players_this_champ_q = PlayerRankStats.select().join(PlayerBasic).switch(PlayerRankStats).join(ChampBasic).where(
				PlayerBasic.region == region, 
				ChampBasic.champId == champ_basic_q.champId
				)
			if(all_players_this_champ_q.count() < 5):
				player_basic_q = PlayerBasic.select().where(PlayerBasic.region == region, PlayerBasic.accountId == data["accountId"])
				if(not player_basic_q.exists()):
					base = self.create_player_basic(region, data["name"], data["accountId"], data["rank"])
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
					elif(data["performance"]/data["plays"] > old_player.performance/old_player.plays):
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
				print("mon: ", mon, " stats: ", stats)
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
		print("duration team: ", game_dur)
		if(teams_dict[100]["wins"] + teams_dict[200]["wins"] > 0):
			for team,val in teams_dict.items():
				team_ref = self.get_team(team, league, region, base)
				if(len(team_ref.team_stats) <= 0):
					self.create_team_stats(team_ref, num_remakes, game_dur, val)
				else:
					self.update_team_stats(team_ref.team_stats.get(), num_remakes, game_dur, val)

	def add_games_visited_db(self, games_visited_list, games_visited):
		visited_for_champ = open("matches_visited.txt", "w")
		visited_for_champ.write("List of games visited: \n")
		for game in games_visited_list:
			visited_for_champ.write("game id: " + str(game) + " \n")
		visited_for_champ.close()
		try:
			with postgres_db.atomic():
				for i in range(0, len(games_visited), 100):
					GamesVisited.insert_many(games_visited[i:i+100]).execute()
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
		"""
		for game in GamesVisited.select().where(GamesVisited.region == "NA"):
			if(game.Patch != self.current_patch):
				print(game.Patch)
		print(GamesVisited.select().where(GamesVisited.region == "NA", Games
		"""

	def add_champ_stats(self, champs_list, cur_patch, base):
		for champ in champs_list:
			cur_champ = champs_list[champ]
			print(cur_champ)
			champ_id = cur_champ.champ_id
			region = base.region
			league = base.leagueTier
			overall = self.create_champ_overall_stats(region, cur_champ)
			for role, stats in cur_champ.roles.items():
				print("role: ", role)
				self.add_players_db(self.create_champ_basic(champ_id, role), region, stats["players"])
				cur_champ.get_best_players(role)
				cur_champ.sort_matchups(role)
				champ_role_overall_q = ChampOverallStatsByRole.select().join(ChampStatsByRank).join(StatsBase).where(
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
					role_overall = self.create_champ_role_stats(stats, role, cur_patch, league, role_overall)
					self.create_champ_rank_stats(contribution_stats, stats, cur_champ, base, cur_patch, role, role_overall)
					#self.add_players_to_db(champ_overall, stats["players"], cur_champ.champ_id, role)
				else:
					role_overall = champ_role_overall_q.get()
					self.update_role_stats(role_overall, stats, cur_champ.patch_bans, cur_champ.patch_plays, cur_patch, league)
					league_tier_stats_q = ChampStatsByRank.select().join(StatsBase).switch(ChampStatsByRank).join(ChampOverallStatsByRole).where(
						StatsBase.leagueTier == league, ChampStatsByRank.champId == champ_id, 
						StatsBase.region == region, ChampOverallStatsByRole.role == role)
					if(league_tier_stats_q.exists()):
						self.update_rank_stats(league_tier_stats_q.get(), stats, contribution_stats)
					else:
						if(role_overall.addons == None and league != "silverMinus"):
							role_overall.addons = self.create_champ_addons(stats, league)
							role_overall.save()
						self.create_champ_role_stats(stats, role, cur_patch, league, role_overall)		
	
	def update_patch_stats(self, old_patch_stats, new_patch_stats):
		for patch,val in new_patch_stats.items():
			print("patch: ", patch, " val: ", val)
			if(patch not in old_patch_stats):
				old_patch_stats[patch] = val
			else:
				old_patch_stats[patch] += val
		return old_patch_stats
	
	def update_role_stats(self, old_data, new_data, new_patch_bans, new_patch_plays, patch, tier):
		#helper functions		
		def update_attribute(old, new, attribute):
			#print("old: ", old, " new: ", new, " type: ", attribute)
			if(old != None):
				if(attribute != "spells" and attribute != "keystone"):
					if(attribute == "skill order"):
						if(len(new) > len(old)):
							old,new = new,old
					for old_type,old_values in old.items():
						if(old_type in new):
							for item,data in new[old_type].items():
								if(item in old[old_type]):
									#print("old: ", old[old_type][item], " new = key: ", item, " val: ", data)
									for key,val in data.items():
										#print("old: ", old[old_type][item], " new = key: ", key, " val: ", val)
										if(key != "info"):
											old[old_type][item][key] += val
								else:
									old[old_type][item] = data	
				else:
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

		old_addons = old_data.addons
		#print("print addon item:", old_addons)
		if(tier != "silverMinus"):
			if(old_addons is not None):
				old_addons.skillOrder = cPickle.dumps(update_attribute(cPickle.loads(old_addons.skillOrder), new_data["skill_order"], "skill order"))	
				old_addons.spells = cPickle.dumps(update_attribute(cPickle.loads(old_addons.spells), new_data["spells"], "spells"))
				old_addons.runes = cPickle.dumps(update_attribute(cPickle.loads(old_addons.runes), new_data["runes"], "runes"))
				old_addons.keystone = cPickle.dumps(update_attribute(cPickle.loads(old_addons.keystone), new_data["keystone"], "keystone"))
				old_addons.matchups = cPickle.dumps(update_attribute(cPickle.loads(old_addons.matchups), new_data["matchups"], "matchups"))
				old_addons.items = cPickle.dumps(update_attribute(cPickle.loads(old_addons.items), new_data["build"], "items"))
				old_addons.save()		
			else:
				self.create_champ_addons(new_data, tier)		
		#also need to update items			
		#print("league: ", league_champ_q.get().champ.role)
		if(patch in new_data["patches_stats"]):
			old_data.roleTotalPlays += new_data["patches_stats"][patch]["plays"]
			old_data.roleTotalWins += new_data["patches_stats"][patch]["wins"]
			old_data.roleTotalRating += new_data["patches_stats"][patch]["rating"]					
		old_data.roleCCDealt += new_data["cc_dealt"]
		old_data.save()

	def update_rank_stats(self, old_champ_stats, new_stats, new_game_scores):
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
		conn = psycopg2.connect("dbname='FlaskScryer' user='postgres' password='1WILLchange!'")
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

	def close(self):
		postgres_db.close()

if __name__=="__main__":
	test = DBHandler()
	test.print_data()