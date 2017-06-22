class PlayerStats:
	def __init__(self, account_id, name, region, rank):
		self.info = {"accountId":account_id, "name":name, "region":region, "currentRank":rank}
		self.stats = {"kda":None}
		self.wins = 0
		self.loses = 0
		self.rating = 0
		self.champs = {}
		self.behavior = {}

	def add_kda(self, kda):
		if(self.stats["kda"] is None):
			self.stats["kda"] = {"kills":kda["kills"], "deaths":kda["deaths"], "assists":kda["assists"]}
		else:
			self.stats["kda"]["kills"] += kda["kills"]
			self.stats["kda"]["deaths"] += kda["deaths"]
			self.stats["kda"]["assists"] += kda["assists"]

	def add_damage_dealt(self, dmg):
		self.add_stat("damage_dealt", dmg)

	def add_gold(self, gold):
		self.add_stat("gold_earned", gold)

	def add_o_score(self, score):
		self.add_stat("objectiveScore", score)

	def add_v_score(self, score):
		self.add_stat("visionScore", score)

	def add_rating(self, rating):
		self.rating += rating

	def add_wins_loses(self, win):
		if(win == 1):
			self.stats["wins"] += 1
		else:
			self.stats["loses"] += 1

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