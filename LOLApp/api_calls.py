from APIConstants import *
#from config import *
import requests, time, urllib, json
#from log import logger

class APICalls:
	def __init__(self, region="NA"):
		self.api_key = API_KEY
		self.platform = PLATFORMS[region]
		#self.curr_cdn_ver = self.get_latest_cdn_ver()
		#logging.basicConfig(filename='crawl.log',level=logging.DEBUG)
		#self.api_callcount = 0
		#print(self.platform)
		#self.log_file = logging.FileHandler("crawl.log", "w")
		#self.log_file.setLevel("DEBUG")

	def _request(self, api_ref, params = {}):
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
		headers = response.headers
		if("X-App-Rate-Limit-Count" in headers and int(headers["X-App-Rate-Limit-Count"][0:1]) >= 6):
			print("rate_limit: ", headers["X-App-Rate-Limit-Count"][0:1])
			time.sleep(1.6)
		if(response.status_code != 200):
			print("Response code: ", response.status_code)
			print("Response headers: ", response.headers)
			print("Response url: ", response.url)
			"""
			logger.debug("Bad response code: ", str(response.status_code))
			logger.info("Response headers: ", str(response.headers))
			logger.info("Response url: ", str(response.url))
			"""
			if(response.status_code != 404):
				time.sleep(.5)
				return self._request(api_ref)
			else:
				return None
		else:
			#print(response.status_code)
			return response.json()

	def get_summoner_by_name(self, name):
		summoner_url = URL['summoner_by_name'].format(
			api_version=API_VERSION,
			summonerName=name 
			)
		return self._request(summoner_url)

	def get_summoner_by_summid(self, summ_id):
		#print(URL)
		summoner_url = URL['summoner_by_summid'].format(
			api_version=API_VERSION,
			summonerId=summ_id 
			)
		return self._request(summoner_url)

	def get_matches_rec(self, acc_id):
		match20_url = URL['matches_recent'].format(
			api_version=API_VERSION,
			accountId=acc_id,
			)
		return self._request(match20_url)

	def get_matches_all(self, acc_id, season=8, queue=420):
		#if(cson != ""):
			#cson = "season=" + cson

		matches_all_url = URL['match_history_all'].format(
			api_version=API_VERSION,
			accountId=acc_id,
			current_season=season,
			queue="queue="+str(queue)# + "&queue="+str(queue[1])
			#season=cson,
			#start=start,
			#end=end
			)
		return self._request(matches_all_url)

	def get_match_data(self, match_id):
		match_url = URL['match_data'].format(
			api_version=API_VERSION,
			matchId=match_id
			)
		return self._request(match_url)

	def get_match_timeline(self, match_id):
		match_url = URL['match_timeline'].format(
			api_version=API_VERSION,
			matchId=match_id
			)
		return self._request(match_url)

	def get_champ_data(self, champion_id):
		champ_url = URL['champ'].format(
			api_version=API_VERSION,
			champ_id=champion_id
			)
		return self._request(champ_url)

	def get_league(self, summ_id):
		league_url = URL["league"].format(
			api_version=API_VERSION,
			summonerId=summ_id
			)
		return self._request(league_url)

	def get_static_data(self, category):
		if(category == "champions" or "summoner-spells"):
			return self._request(URL["static_data"].format(
				api_version=API_VERSION,
				category=category
				)+"&dataById=false")
		else:
			return self._request(URL["static_data"].format(
				api_version=API_VERSION,
				category=category
				))

	def get_master_players(self):
		return self._request(URL["master_players"])

	def get_all_champs_json(self):
		with urllib.request.urlopen(URL["champs_json"].format(cdn_ver=self.curr_cdn_ver)) as url:
			data = json.loads(url.read().decode())
			return data

	def get_latest_cdn_ver(self):
		return self._request(URL['static_ver'].format(api_version=API_VERSION))[0]