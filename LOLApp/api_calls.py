from .APIConstants import *
import requests, time

class APICalls:
	def __init__(self, region="NA"):
		self.api_key = API_KEY
		self.platform = PLATFORMS[region]
		#self.api_callcount = 0
		#print(self.platform)

	def _request(self, api_ref, params = {}):
		if("static-data" not in api_ref):
			time.sleep(1)
		"""self.api_callcount += 1
		if(self.api_callcount > 8):
			time.sleep(5)
			self.api_callcount = 0
		"""
		args = {'api_key': self.api_key}
		for k,v in params.items():
			if k not in args:
				args[k] = v
		response = requests.get(
				URL['api_url'].format(
				platform=self.platform, 
				rest=api_ref),
			params=args 
				)
		print(response.url)
		return response.json()

	def get_summoner_by_name(self, name):
		summoner_url = URL['summoner_by_name'].format(
			api_version=API_VERSION,
			summonerName=name 
			)
		return self._request(summoner_url)

	def get_matches_rec(self, acc_id):
		match20_url = URL['matches_recent'].format(
			api_version=API_VERSION,
			accountId=acc_id,
			)
		return self._request(match20_url)

	def get_matches_all(self, acc_id, start=0, end=10, cson=""):
		if(cson != ""):
			cson = "season=" + cson
		matches_all_url = URL['match_history_all'].format(
			api_version=API_VERSION,
			accountId=acc_id,
			season=cson,
			start=start,
			end=end
			)
		return self._request(matches_all_url)

	def get_match_data(self, match_id):
		match_url = URL['match_data'].format(
			api_version=API_VERSION,
			matchId=match_id
			)
		return self._request(match_url)

	def get_champ_data(self, champion_id):
		champ_url = URL['champ_data'].format(
			api_version=API_VERSION,
			champ_id=champion_id
			)
		return self._request(champ_url)

	def get_league(self, acc_id):
		league_url = URL["league"].format(
			api_version=API_VERSION,
			accountId=acc_id
			)
		return self._request(league_url)

	def get_latest_cdn_ver(self):
		return self._request(URL['static_ver'].format(api_version=API_VERSION))[0]