class PlayerStats:
	def __init__(self, account_id, summ_id, name, region, rank):
		self.accountId = account_id
		self.summonerId = summ_id
		self.name = name
		self.region = region
		self.currentRank = rank
		self.kills = self.deaths = self.assists = self.kda = 0
		self.wins = self.loses = self.oa_rating = self.tier_rating = 0
		self.kp = self.obj_sc = self.vis_sc = self.gold_share = 0
		self.wpm = self.dpm = self.damage_share = 0
		self.champs = {}
		self.playstyle = {}

	def add_kills_stats(self, kda_dict, kda):
		self.kills += kda_dict["kills"]
		self.deaths += kda_dict["deaths"]
		self.assists += kda_dict["assists"]
		self.kda += kda

	def add_damage_share(self, dmg_share):
		self.damage_share += dmg_share

	def add_gold_share(self, gs):
		self.gold_share += gs

	def add_obj_score(self, score):
		self.obj_sc += score

	def add_vis_score(self, score):
		self.vis_sc += score

	def add_ratings(self, oa_rating, tier_rating):
		self.oa_rating += oa_rating
		self.tier_rating += tier_rating

	def add_wins_loses(self, win):
		if(win == 1):
			self.wins += 1
		else:
			self.loses += 1

	def add_stat(self, categ, stat):
		if(categ not in self.stats):
			self.stats[categ] = stat
		else:
			self.stats[categ] += stat

	def add_champ(self, champ_id, win, performance):
		if(champ_id not in self.champs):
			self.champs[champ_id] = {"plays":1, "wins":win, "performance":performance}
		else:
			self.champs[champ_id]["plays"] += 1
			self.champs[champ_id]["wins"] += win
			self.champs[champ_id]["performance"] += performance

	def get_data_list_dict(self):
		temp = []
		for k,v in self.info.items():
			temp.append({k:v})
		for k,v in self.stats.items():
			temp.append({k:v})
		temp.append({"champions":self.champs})