import APIConstants, urllib, time, logging, ast
from random import randint
from championstats import ChampionStats
from playersStats import PlayerStats
from apiCalls import APICalls
from models import *

#can maybe record most optimal pathing, using match timeline, and also best ward placements
class LolCrawler:
	def __init__(self, region="NA"):
		self.api_obj = APICalls()
		self.api_obj.set_region(region)
		self.region = region
		initialize_db()
		self.error_log = open("crawl_error_log.txt", "w")
		#self.items_data = self.get_all_items_data()["data"]
		#logging.basicConfig(filename='crawl.log',level=logging.DEBUG)

	def get_champ_stats(self, desired_rank, num_matches=1000, reset=False):
		print("num games in db: ", GamesVisited.select().where(GamesVisited.region == "NA").count())
		start = time.time()
		self.coords = {"Top":{"x":range(500,4600),"y":range(9500,14500)},"Mid":{"x":range(5000,9000),"y":range(6000,9500)},
						"Bot":{"x":range(10000,14400),"y":range(600,4500)}, "Jungle":{"x":range(-120,14870),"y":range(-120,14980)}}
		if(reset):
			self.clear_db()
		if(self.api_obj.get_latest_cdn_ver() != APIConstants.CDN_VERSION):
			Champion.delete().where(Champion.champId != None).execute()
			Item.delete().where(Item.itemId != None).execute()
		self.items_info = self.get_items_data()
		self.champs_info = self.get_champs_data()
		self.keystones_info = self.get_keystones_data()
		self.spells_info = self.get_summ_spells_data()
		self.runes_info = self.get_runes_data()
		self.players_visited = {}
		self.matches_visited_list = []
		self.mh_visited = []
		self.matches_visited = []
		self.remakes = []
		self.rank_tiers_vis = []
		self.leagues = {"diamondPlus":{"rank_tiers":["DIAMOND", "CHALLENGER", "MASTER"],"champions":{}, "mons":{}},
						"bronze":{"rank_tiers":["BRONZE"],"champions":{}, "mons":{}},
						"silver":{"rank_tiers":["SILVER"],"champions":{}, "mons":{}},
						"gold":{"rank_tiers":["GOLD"],"champions":{}, "mons":{}},
						"platinum":{"rank_tiers":["PLATINUM"],"champions":{}, "mons":{}}
						}
		if(desired_rank == "diamondPlus"):
			league_players = self.api_obj.get_master_players()
		else:
			if(desired_rank in APIConstants.STARTING_PLAYERS[self.region]):
				league_players = self.api_obj.get_league(APIConstants.STARTING_PLAYERS[self.region][desired_rank])[0]
			else:
				return "Invalid Parameters"
		self.crawl_history(league_players, num_matches)

		self.add_champ_stats_db()
		self.add_gamed_visited_db()
		self.add_players_db()
		end = time.time()
		print("Searching ", len(self.matches_visited_list), " matches took: ", end - start, " seconds.")
		database.close()

	def close_err_log(self):
		self.error_log.close()

	def clear_db(self):
		GamesVisited.delete().where(GamesVisited.matchId != None).execute()
		ChampStats.delete().where(ChampStats.champId != None).execute()  # remove the rows
		Player.delete().where(Player.accountId != None).execute()

	def add_players_db(self):
		for player,data in self.players_visited.items():
			num_matches = data.wins+data.loses
			if(num_matches >= 3):
				player_query = Player.select().where(Player.accountId == data.accountId, Player.region == data.region)
				if(not player_query.exists()):
					Player.create(
						accountId = data.accountId,
						name = data.name,
						summId = data.summonerId,
						region = data.region,
						champions = data.champs,
						kda = data.kda,
						kills = data.kills,
						deaths = data.deaths,
						assists = data.assists,
						wins = data.wins,
						loses = data.loses,
						oaRating = data.oa_rating,
						tierRating = data.tier_rating,
						kp = data.kp,
						objScore = data.obj_sc,
						visScore = data.vis_sc,
						goldShare = data.gold_share,
						wpm = data.wpm,
						dpm = data.dpm,
						dmgShare = data.damage_share,
						playstyle = data.playstyle,
						numGames = data.num_games
					)
				else:
					player_data = player_query.get()
					player_data.kda += data.kda
					player_data.kda += data.kda
					player_data.kills += data.kills
					player_data.deaths += data.deaths
					player_data.assists += data.assists
					player_data.wins += data.wins
					player_data.loses += data.loses
					player_data.oaRating += data.oa_rating
					player_data.tierRating += data.tier_rating
					player_data.kp += data.kp
					player_data.objScore += data.obj_sc
					player_data.visScore += data.vis_sc
					player_data.goldShare += data.gold_share
					player_data.wpm += data.wpm
					player_data.dpm += data.dpm
					player_data.dmgShare += data.damage_share
					old = ast.literal_eval(player_data.champions)
					for champ in data.champs:
						if(champ in old):
							old[champ]["plays"] += data.champs[champ]["plays"]
							old[champ]["wins"] += data.champs[champ]["wins"]
							old[champ]["performance"] += data.champs[champ]["performance"]
						else:
							old[champ] = data.champs[champ]
					player_data.champions = old
					player_data.save()

	def add_champ_stats_db(self):
		for league in self.leagues:
			self.add_monsters_db(self.leagues[league]["mons"], league)
			champs = self.leagues[league]["champions"]
			if(len(champs) > 0):
				for champ in champs:
					cur_champ = champs[champ]
					if(cur_champ.deaths == 0):
						oa_kda = cur_champ.kills+cur_champ.assists
					else:
						oa_kda = (cur_champ.kills+cur_champ.assists)/cur_champ.deaths
					for role, stats in cur_champ.roles.items():
						print("id: ", cur_champ.champ_id, " role: ", role)
						champ_query = ChampStats.select().where(ChampStats.champId == cur_champ.champ_id, ChampStats.key == self.region + "-" + league, ChampStats.role == role)
						if(not champ_query.exists()):
							other = ChampStats.select().where(ChampStats.champId == cur_champ.champ_id, ChampStats.key.contains(self.region))
							if(len(other) > 1):
								for champ_role in other:
									if(champ_role != ChampStats.role):
										champ_role.totalPlays += cur_champ.plays
										t_plays = champ_role.totalPlays
										champ_role.totalWins += cur_champ.wins
										t_wins = champ_role.totalWins
										champ_role.bans += cur_champ.bans
										t_bans = champ_role.bans
										champ_role.kda += oa_kda
										t_kda = champ_role.kda
										champ_role.kills += cur_champ.kills
										t_kills = champ_role.kills
										champ_role.deaths += cur_champ.deaths
										t_deaths = champ_role.deaths
										champ_role.assists += cur_champ.assists
										t_assists = champ_role.assists
										champ_role.oaRating += cur_champ.oa_rating
										t_oaRating = champ_role.oaRating
										champ_role.save()
								ChampStats.create(
									champId = cur_champ.champ_id,
									role = role,
									totalPlays = t_plays,
									rolePlays = stats["plays"],
									totalWins = t_wins,
									roleWins = stats["game_result"],
									bans = t_bans,
									kda = t_kda,
									kills = t_kills,
									deaths = t_deaths,
									assists = t_deaths,
									oaRating = t_oaRating,
									roleRating = stats["oa_role_rating"],
									spells = stats["spells"],
									keystone = stats["keystone"],
									players = cur_champ.players,
									skillOrder = stats["skill_order"],
									dpg = stats["damage_dealt_per_gold"],
									dmpg = stats["damage_mitigated_per_gold"],
									matchups = stats["matchups"],
									key = self.region + "-" + league,
									runes = stats["runes"],
									items = stats["build"]
								)
							else:
								ChampStats.create(
									champId = cur_champ.champ_id,
									role = role,
									totalPlays = cur_champ.plays,
									rolePlays = stats["plays"],
									totalWins = cur_champ.wins,
									roleWins = stats["game_result"],
									bans = cur_champ.bans,
									kda = oa_kda,
									kills = cur_champ.kills,
									deaths = cur_champ.deaths,
									assists = cur_champ.assists,
									oaRating = cur_champ.oa_rating,
									roleRating = stats["oa_role_rating"],
									spells = stats["spells"],
									keystone = stats["keystone"],
									players = cur_champ.players,
									skillOrder = stats["skill_order"],
									dpg = stats["damage_dealt_per_gold"],
									dmpg = stats["damage_mitigated_per_gold"],
									matchups = stats["matchups"],
									key = self.region + "-" + league,
									runes = stats["runes"],
									items = stats["build"]
								)
						else:
							old_data = ChampStats.select().where(ChampStats.champId == cur_champ.champ_id, ChampStats.key.contains(self.region))
							for champ_role in old_data:
								print("adding champ and role already in db, role: ", champ_role.role)
								champ_role.totalPlays += cur_champ.plays
								champ_role.totalWins += cur_champ.wins
								champ_role.bans += cur_champ.bans
								champ_role.kda += oa_kda
								champ_role.kills += cur_champ.kills
								champ_role.deaths += cur_champ.deaths
								champ_role.assists += cur_champ.assists
								champ_role.oaRating += cur_champ.oa_rating
								champ_role.save()
							old_champ = champ_query.get()
							old_champ.dpg += stats["damage_dealt_per_gold"]
							old_champ.dmpg += stats["damage_mitigated_per_gold"]
							old_champ.roleRating += stats["oa_role_rating"]
							old_champ.rolePlays += stats["plays"]
							temp = ast.literal_eval(old_champ.roleWins)
							for duration,game_res in stats["game_result"].items():
								print(game_res)
								if(duration not in temp):
									temp[duration] = game_res
								else:
									if(duration == "totalRoleWins"):
										temp[duration] += game_res
									else:
										temp[duration]["wins"] += game_res["wins"]
										temp[duration]["games"] += game_res["games"]
							old_champ.roleWins = temp

							old_players = ast.literal_eval(old_champ.players)
							for player in cur_champ.players:
								if(player not in old_players):
									old_players[player] = cur_champ.players[player]
								else:
									old_players[player]["wins"] += cur_champ.players[player]["wins"]
									old_players[player]["kda"]["kills"] += cur_champ.players[player]["kda"]["kills"]
									old_players[player]["kda"]["deaths"] += cur_champ.players[player]["kda"]["deaths"]
									old_players[player]["kda"]["assists"] += cur_champ.players[player]["kda"]["assists"]
									old_players[player]["perf"] += cur_champ.players[player]["perf"]
									old_players[player]["plays"] += cur_champ.players[player]["plays"]
							old_champ.players = old_players
							if(league == "diamondPlus"):
								print("stats: ", stats)
								old_champ.skillOrder = self.update_skill_order(ast.literal_eval(old_champ.skillOrder), stats["skill_order"])								
								self.update_attribute(ast.literal_eval(old_champ.spells), stats["spells"], "spells")
								if(len(old_champ.runes) > 0):
									self.update_runes(ast.literal_eval(old_champ.runes), stats["runes"])
								else:
									old_champ.runes = stats["runes"]
								if(len(old_champ.keystone) > 0):
									self.update_attribute(ast.literal_eval(old_champ.keystone), stats["keystone"], "keystone")
								else:
									old_champ.keystone = stats["keystone"]
								if(len(old_champ.matchups) > 0):
									print("matchups ", old_champ.matchups, " length: ", len(old_champ.matchups))
									self.update_attribute(ast.literal_eval(old_champ.matchups), stats["matchups"], "matchups")
								else:
									old_champ.matchups = stats["matchups"]
							old_champ.save()

	def add_monsters_db(self, monsters, league):
		for mon,stats in monsters.items():
			print(mon, " w: ",  stats["wins"], " k: ", stats["kills"])
			mon_query = MonsterStats.select().where(MonsterStats.monsterKey == league + "-" + mon)
			if(not mon_query.exists()):
				MonsterStats.create(
					monsterKey = league + "-" + mon,
					kills = stats["kills"],
					wins = stats["wins"],
					time = stats["time"], #if this was the first monster killed, add the time
					games = stats["games"]
				)
			else:
				old_d = mon_query.get()
				old_d.kills += stats["kills"]
				old_d.wins += stats["wins"]
				old_d.time += stats["time"] #if this was the first monster killed, add the time
				old_d.games += stats["games"]
				old_d.save()

	def update_skill_order(self, old, new):
		if(len(new) > len(old)):
			old,new = new,old
		for lvl,skills in old.items():
			if(lvl in new):
				self.update_attribute(skills, new[lvl], "skill_order")
		return old

	def update_runes(self, old, new):
		for rune_type,runes in old.items():
			if(rune_type in new):
				self.update_attribute(runes, new[rune_type], "runes")

	def update_attribute(self, old, new, attribute):
		print("old: ", old, " new: ", new, " type: ", attribute)
		for item,stats in new.items():
			if(item in old):
				if(attribute != "matchups"):
					old[item]["used"] += stats["used"]
					old[item]["perf"] += stats["perf"]
					old[item]["wins"] += stats["wins"]		
				else:
					old[item]["used_against"] += stats["used_against"]
					old[item]["perf_against"] += stats["perf_against"]
					old[item]["wins_against"] += stats["wins_against"]						
			else:
				if(attribute == "skill_order"):
					old[item] = stats
				elif(attribute == "matchups"):
					old[item] = stats
				else:
					old[item] = stats
		print("old updated: ", old)

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

	def print_data(self, rank):
		for champ in ChampStats.select().where(ChampStats.rankTier == rank):
			champ_info = Champion.get(Champion.champId == champ.champId) 
			print(champ_info.name, " role: ", champ.role, " for ranks: ", champ.rankTier)
			print("Winrate: ", round(champ.totalWins/champ.totalPlays, 2), " overall rating: ", round(champ.oaRating/champ.totalPlays, 2))
			"""
			build = ast.literal_eval(champ.build)
			for stage,item in build.items():
				print(stage)
				for itemId,stats in item.items():
					if(stage == "late"):
						print(itemId)
						for item,val in stats.items():
							name = val["info"]["name"]
							print(item, " name: ", name, " rating: ", val["rating"], " used: ", val["used"])
					else:
						name = stats["info"]["name"]
						print(itemId, " name: ", name, " rating: ", stats["rating"], " used: ", stats["used"])
			"""
			print(champ.skillOrder)
			print(ChampStats.select().where(ChampStats.rankTier == rank).count())

	def crawl_history(self, league, num_matches, season=8, q=420):
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
							if(self.check_game(game_id)):
								print(len(self.matches_visited_list), "/", num_matches)
								self.matches_visited.append({"matchId":game_id, "region":self.region})
								self.matches_visited_list.append(game_id)
								print("game id :", game_id)
								match_details = self.get_match_details(game_id)
								if(len(player_leagues_to_visit) < 2):
									player_leagues_to_visit.append(match_details)
								#1496197986 represents latest paatch date
								if(match_details is not None and match_details["gameCreation"] > 1496197986):
									tier = self.get_tier_k(league["tier"])
									print("315 tier: ", tier)
									if(match_details["gameDuration"] < 300):
										self.remakes.append(game_id)
									else:
										self.add_banned_champs(match_details, tier)
										match_timeline = self.api_obj.get_match_timeline(game_id)
										par = match_details["participants"]
										self.get_team_stats(par)
										self.process_player_pairs(match_details, match_timeline, par, tier)
								else:
									break
						else:
							break							
		for player in player_leagues_to_visit.pop():
			if(len(self.matches_visited_list) < num_matches):
				acc_id = player["player"]["currentAccountId"]
				if(acc_id not in self.players_visited):
					rank = self.api_obj.get_league(player["player"]["summonerId"])[0]
					print((rank["tier"] + " " + rank["name"]))
					if((rank["tier"] + " " + rank["name"]) not in self.rank_tiers_vis):
						self.crawl_history(rank, num_matches)

	def check_game(self, game_id):
		game_query = GamesVisited.select().where(GamesVisited.matchId == game_id, GamesVisited.region == self.region)
		return game_id not in self.matches_visited_list and not game_query.exists()

	def get_rank(self, summ_id):
		rank = self.api_obj.get_league(summ_id)
		if(len(rank) > 0):
			return rank[0]["tier"]
		return "UNRANKED"

	def add_player(self, acc_id, name, summ_id, curr_player_rank):
		if(type(summ_id) is int):
			rank = self.get_rank(summ_id)
			if(rank is "UNRANKED"):
				rank = curr_player_rank
		else:
			rank = summ_id
		new_player = PlayerStats(acc_id, summ_id, name, self.region, rank)
		self.players_visited[acc_id] = new_player

	def get_tier_k(self, player_rank):
		print("rank: ", player_rank)
		if(player_rank == "DIAMOND" or player_rank == "MASTER" or player_rank == "CHALLENGER"):
			return "diamondPlus"
		else:
			return player_rank.lower()

	def process_player_pairs(self, match_details, match_timeline, par, curr_rank):
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
				self.add_champs_data(match_details, {"team1":[p1,p1_rank],"team2":[p2,p2_rank]}, {"team1":p1_tier_key, "team2":p2_tier_key}, p1_role, timeline)
				#print("build for: ", champ_name, " - ", self.leagues[rank]["champions"][champ_name].get_items())	
			else:
				print("no pair for: ", p1["championId"])

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
	def add_champs_data(self, match_details, players, rank_tier_key, role=None, match_timeline=[]):
		laning_perf = self.analyze_matchup(match_timeline, players["team1"][0], players["team2"][0], role, rank_tier_key)
		game_dur = match_details["gameDuration"]/60
		for team,player in players.items():
			if(team == "team2"):
				laning_perf = 1 - laning_perf
			champ_id = player[0]["championId"]
			champ_obj = self.leagues[rank_tier_key[team]]["champions"][champ_id]
			acc_id = match_details["participantIdentities"][player[0]["participantId"]-1]["player"]["currentAccountId"]
			win = 1 if player[0]["stats"]["win"] else 0
			player_perf = self.get_player_performance(match_timeline, player[0], acc_id, role, team, game_dur)
			rating = (player_perf*.7) + (laning_perf*.3)
			oa_rating = rating*self.get_multiplier(player[1])

			self.leagues[rank_tier_key[team]]["champions"][champ_id].add_player(acc_id, win, self.get_kda(player[0]), oa_rating)
			self.add_players_data(player[0], acc_id, win, oa_rating, rating, game_dur)
			self.players_visited[acc_id].add_champ(champ_id, win, player_perf)
			champ_obj.plays += 1
			self.add_champ_stats(champ_obj, player[0], win, role, self.get_kda(player[0]), laning_perf, oa_rating, game_dur)

			if(rank_tier_key[team] == "diamondPlus" or rank_tier_key[team] == "platinum"):
				self.process_timeline(role, match_timeline, player[0], rank_tier_key[team], laning_perf, oa_rating, win)
				self.add_keystone(champ_obj, player[0], role, win, laning_perf)
				self.add_spells(champ_obj, player[0], role, win, laning_perf)
				self.add_runes(champ_obj, player[0], role, win, laning_perf)
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
		points += (stats["damageDealtToObjectives"]/game_dur)**.2
		return points

	def get_vis_sc(self, player, game_dur):
		#using riot's own visonscore which is calculated based on how much vision you provided/denied
		try:
			return player["stats"]["visionScore"]/game_dur
		except:
			KeyError
		return 0

	def add_banned_champs(self, match, desired_rank):
		banned_champs = []
		curr_section = self.leagues[desired_rank]
		for team in match["teams"]:
			for ban in team["bans"]:
				champ_id = ban["championId"]
				if(champ_id not in banned_champs):
					if(champ_id in self.champs_info):
						if(champ_id not in curr_section["champions"]):
							curr_section["champions"][champ_id] = ChampionStats(champ_id)	
						curr_section["champions"][champ_id].bans += 1
						banned_champs.append(champ_id)

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

	def get_player_performance(self, timeline, player, acc_id, role, team, duration):
		teams = {"team1": [self.team1_dmg, self.team1_gold, self.team1_kills], 
				"team2":[self.team2_dmg, self.team2_gold, self.team2_kills]}
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
		return (score/9.5)

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

	def add_runes(self, champ, player_details, role, win, perf):
		try:
			runes = player_details["runes"]
			"""
			temp = {"reds":0, "yellows":0, "blues":0, "blacks":0}
			length = len(runes)
			index = 0
			if(length >= 4):
				while(index < length):
					temp[]
					champ.add_attribute(role, win, perf, "runes", self.runes_info[runes[index]["runeId"], "red")
			"""
			rune_types = {0:"red", 1:"blue", 2:"yellow", 3:"black"}
			index = 0
			similar = []
			if(len(runes) == 4):
				for rune in runes:
					if(rune["runeId"] in self.runes_info):
						champ.add_attribute(role, win, perf, "runes", self.runes_info[rune["runeId"]], rune_types[index])
					index += 1
		except:
			KeyError

	def process_timeline(self, role, timeline, player_details, rank_tier_key, laning, rating, win):
		champ_id = player_details["championId"]
		par_id = player_details["participantId"]
		champ = self.leagues[rank_tier_key]["champions"][champ_id]
		monsters = self.leagues[rank_tier_key]["mons"]
		for idx,frame in enumerate(timeline[1:]):
			for event in frame["events"]:
				if("participantId" in event and event["participantId"] == par_id and event["type"] == "ITEM_PURCHASED"):
					item_id = event["itemId"]
					if(item_id in self.items_info["consumables"]):
						champ.add_item(item_id, self.items_info["consumables"][item_id], role, "consumables", rating, win)
					else:
						if(event["timestamp"] < 20000):
							if(item_id in self.items_info["start"]):
								champ.add_item(item_id, self.items_info["start"][item_id], role, "start", rating, win)
						else:
							if(item_id in self.items_info["complete"]):			
								self.add_build(item_id, idx, laning, rating, champ, role, win)		
				elif(event["type"] == "ELITE_MONSTER_KILL"):
					self.add_monster(event, monsters, win)

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

	def add_monster(self, timeframe, mon_dict, win):
		if(timeframe["monsterType"]  != "DRAGON"):
			mon = timeframe["monsterType"] 
		else:
			mon = timeframe["monsterSubType"]
		if(mon not in mon_dict):
			mon_dict[mon] = {"wins":win, "time":timeframe["timestamp"]/60000, "kills":1, "games":1}
		else:
			mon_dict[mon]["wins"] += win
			mon_dict[mon]["time"] += timeframe["timestamp"]/60000
			mon_dict[mon]["kills"] += 1

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

	def add_champ_stats(self, champ, player, win, role, kda, laning, rating, dur):
		champ.add_kda(kda)
		champ.oa_rating += rating
		champ.wins += win
		stats = player["stats"]
		champ.add_role(role, win, dur, kda, stats["totalDamageDealtToChampions"]/stats["goldEarned"], stats["damageSelfMitigated"]/stats["goldEarned"], laning, rating)

	def analyze_matchup(self, timeline, p1, p2, role, rank_tier_key):
		#print("des rank: ", desired_rank)
		p1_champ = p1["championId"]
		p2_champ = p2["championId"]
		stats = ["csDiffPerMinDeltas", "xpDiffPerMinDeltas"]
		win = 1 if p1["stats"]["win"] else 0
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
		self.leagues[rank_tier_key["team1"]]["champions"][p1_champ].add_matchup(role, p2_champ, matchup_res, win)
		self.leagues[rank_tier_key["team2"]]["champions"][p2_champ].add_matchup(role, p1_champ, -matchup_res, win)
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

	def get_items_data(self):
		items_raw_data = self.api_obj.get_static_data("items")["data"]
		temp = {"complete":{}, "trinket":{}, "start":{}, "consumables":{}}
		for item,val in items_raw_data.items():
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
				query = Item.select().where(Item.itemId == item_int)
				if(None in tags):
					tags = None
				if(not query.exists()):
					Item.create(
						itemId = item_int,
						name = val["name"],
						image = val["image"]["full"],
						cost = val["gold"]["total"],
						tags = tags,
						des = val["sanitizedDescription"]
					)
		return temp

	def check_item_complete(self, info):
		return "into" not in info and ("tags" not in info or "Consumable" not in info["tags"])

	def get_champs_data(self):
		champs_data = self.api_obj.get_static_data("champions")["data"]
		temp = {}
		for champ_key,champ in champs_data.items():
			temp[champ["id"]] = {"name":champ["name"], "image":champ["image"]["full"], 
								"passive":champ["passive"], "abilities":champ["spells"], 
								"enemy_tips":champ["enemytips"], "ally_tips":champ["allytips"],
								"tags":champ["tags"]
								}
			query = Champion.select().where(Champion.champId == champ["id"])
			if(not query.exists()):
				Champion.create(
					champId = champ["id"],
					name = champ["name"],
					image = champ["image"]["full"],
					tags = champ["tags"],
					abilities = champ["spells"],
					passive = champ["passive"],
					enemyTips = champ["enemytips"],
					allyTips = champ["allytips"]
				)
		return temp

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
		runes_data = self.api_obj.get_static_data("runes")["data"]
		temp = {}
		for rune_id,data in runes_data.items():
			if("Quintessence" in data["name"] or "Greater" in data["name"]):
				temp[int(rune_id)] = {"name":data["name"], "image":data["image"]["full"], "id":data["id"]}
		return temp

	def get_summ_spells_data(self):
		spells_data = self.api_obj.get_static_data("summoner-spells")["data"]
		temp = {}
		for spell,data in spells_data.items():
			if("CLASSIC" in data["modes"]):
				temp[data["id"]] = {"name":data["name"], "id":data["id"], "image":data["image"]["full"], "des":data["description"]}
		return temp

	def get_history(self, acc_id, season = 8, queues=[]):
		return self.api_obj.get_matches_all(acc_id, season, queues)["matches"]

	def get_match_details(self, game_id):
		return self.api_obj.get_match_data(game_id)

	def get_champ_tags(self, champ_id):
		return self.api_obj.get_champ_data(champ_id)["tags"]

if __name__ == "__main__":
	na_crawler = LolCrawler()
	na_crawler.get_champ_stats("diamondPlus", 5)
	#crawler.get_champ_stats("diamondPlus", 100, True)
	#na_crawler.get_champ_stats("pl", 60)
	na_crawler.close_err_log()
	#eu_crawler = LolCrawler("EUW")
	#eu_crawler.get_champ_stats("platinum", 100)
	#eu_crawler.get_champ_stats("diamondPlus", 100)
	#eu_crawler.get_champ_stats("bronze", 100)
	#eu_crawler.close_err_log()
	#kr_crawler = LolCrawler("KR")
	#kr_crawler.get_champ_stats("diamondPlus", 150)
	#crawler.print_data("diamondPlus")
	#crawler.get_champ_stats("platinum", 150, False)
	#crawler.get_champ_stats("gold", 6, False)
	#kr_crawler.close_err_log()
	#euCrawler.close_err_log()