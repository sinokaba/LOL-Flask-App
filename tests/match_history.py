from grabAPI import APICalls
import RiotAPI as statics

class MatchHistory:
	def __init__(self, region, name):
		self.api = APICalls(region)
		acc_id = self.api.get_summoner_by_name(name)["accountId"]
		match_history = self.api.get_matches_rec(acc_id)
		self.matches_10 = match_history["matches"]
		print(self.matches_10[0]["gameId"])

	def get_recent(self):
		return self.matches_10

	def match_data(self):
		self.match_info = self.api.get_match_data(self.matches_10[0]["gameId"])
		self.champ_id = self.match_info["participants"][0]["championId"]
		return self.champ_id

	def get_champ_icon(self):
		self.match_data()
		champ = self.api.get_champ_data(self.champ_id)["image"]["full"]
		current_ver = self.api.get_latest_cdn_ver()
		champ_icon = statics.URL["champ_img"].format(champ=champ, static_ver=current_ver)
		return champ_icon

