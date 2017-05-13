from grabAPI import APICalls

class Summoner:
	def __init__(self, name, region):
		self._riotAPI = APICalls(region)
		acc = self._riotAPI.get_summoner_by_name(name)
		self.acc_id = acc["accountId"]
		self.profile_icon = acc["profileIconId"]


