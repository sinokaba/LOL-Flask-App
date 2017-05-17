URL = {
	'api_url': 'https://{platform}.api.riotgames.com/lol/{rest}',
	'summoner_by_name': 'summoner/v{api_version}/summoners/by-name/{summonerName}',
	'match_history_all': 'match/v{api_version}/matchlists/by-account/{accountId}?endIndex={end}&{season}&beginIndex={start}',
	'matches_recent': 'match/v{api_version}/matchlists/by-account/{accountId}/recent',
	'match_data': 'match/v{api_version}/matches/{matchId}',
	'champ_data': 'static-data/v{api_version}/champions/{champ_id}?champData=image',
	'current_game': '/spectator/v{api_version}/active-games/by-summoner/{summonerId}',
	'league': 'league/v{api_version}/leagues/by-summoner/{accountId}',
	'static_data_imgs': 'http://ddragon.leagueoflegends.com/cdn/{cdn_version}/img/{category}/{name}',
	'static_ver': 'static-data/v{api_version}/versions',
	'profile_icon': 'http://avatar.leagueoflegends.com/{region}/{summonerName}'
}	

API_VERSION = '3'

API_KEY = '383ade41-23a5-4e68-a0e1-63ce90c30f85'

PLATFORMS = {
	"NA": 'NA1',
	"EUW": 'EUW1',
	"EUNE": 'EUN1',
	"KR": 'KR' 
}
