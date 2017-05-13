import RiotAPI as const
import requests

class APICalls:
	def __init__(self, region):
		self.api_key = const.API_KEY
		self.region = region
		#print(self.region)

	def _request(self, api_ref, params = {}):
		args = {'api_key': self.api_key}
		for k,v in params.items():
			if k not in args:
				args[k] = v
		response = requests.get(
			const.URL['api_url'].format(
				region=self.region, 
				rest=api_ref),
			params=args 
				)
		print(response.url)
		return response.json()

	def get_summoner_by_name(self, name):
		summoner_url = const.URL['summoner_by_name'].format(
			api_version=const.API_VERSION,
			summonerName=name 
			)
		return self._request(summoner_url)

	def get_matches_rec(self, acc_id):
		match20_url = const.URL['matches_recent'].format(
			api_version=const.API_VERSION,
			accountId=acc_id,
			)
		return self._request(match20_url)

	def get_matches_all(self, acc_id, start=0, end=10, cson=""):
		if(cson != ""):
			cson = "season=" + cson
		matches_all_url = const.URL['match_history_all'].format(
			api_version=const.API_VERSION,
			accountId=acc_id,
			season=cson,
			start=start,
			end=end
			)
		return self._request(matches_all_url)

	def get_match_data(self, match_id):
		match_url = const.URL['match_data'].format(
			api_version=const.API_VERSION,
			matchId=match_id
			)
		return self._request(match_url)

	def get_champ_data(self, champion_id):
		champ_url = const.URL['champ_data'].format(
			api_version=const.API_VERSION,
			champ_id=champion_id
			)
		return self._request(champ_url)

	def get_latest_cdn_ver(self):
		return self._request(const.URL['static_ver'].format(api_version=const.API_VERSION))[0]