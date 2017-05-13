from summoner_info import Summoner
import RiotAPI as statics

class MatchHistory:
	def __init__(self, region, name):
		self.summoner = Summoner(name, region)
		match_history = self.summoner._riotAPI.get_matches_all(self.summoner.acc_id, 0, 30)
		self.matches_30 = match_history["matches"]
		self.current_ver = self.summoner._riotAPI.get_latest_cdn_ver()
		#print(summoner.acc_id)
		#print(self.matches_10[0]["gameId"])

	def get_recent(self):
		return self.matches_30

	def match_data(self):
		self.match_info = self.summoner._riotAPI.get_match_data(self.matches_30[0]["gameId"])
		self.champ_id = self.match_info["participants"][0]["championId"]
		return self.champ_id

	def get_champ_icon(self):
		self.match_data()
		champ = self.summoner._riotAPI.get_champ_data(self.champ_id)["image"]["full"]
		champ_icon = statics.URL["champ_img"].format(champ=champ, static_ver=self.current_ver)
		return champ_icon

	def get_summoner_icon(self):
		return statics.URL["profile_icons"].format(
			static_ver=self.current_ver,
			icon_id=str(self.summoner.profile_icon) + ".png"
			)
