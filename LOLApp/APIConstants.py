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

API_KEY = 'RGAPI-918806e7-fc91-4da8-84a6-50f591dc9ee0'

PLATFORMS = {
	"NA": 'NA1',
	"EUW": 'EUW1',
	"EUNE": 'EUN1',
	"KR": 'KR' 
}

SPELLS = {
	12 : "SummonerTeleport.png",
	3 : "SummonerExhaust.png",
	21 : "SummonerBarrier.png",
	11 : "SummonerSmite.png",
	4 : "SummonerFlash.png",
	14 : "SummonerDot.png",
	7 : "SummonerHeal.png",
	1 : "SummonerBoost.png",
	31 : "SummonerPoroThrow.png",
	6 : "SummonerHaste.png",
	32 : "SummonerSnowball.png",
	13 : "SummonerMana.png",
	0 : "SummonerSiegeChampSelect1.png"
}

GAMEMODE = {
	8 : ["Twisted Treeline", "NORMAL_3x3"],
	0 : ["Custom", "CUSTOM"],
	2 : ["Normal Blind", "NORMAL_5x5_BLIND"],
	14 : ["Normal Draft", "NORMAL_5x5_DRAFT"],
	4 : ["Ranked Solo", "RANKED_SOLO_5x5"],
	42 : ["Ranked Team", "RANKED_TEAM_5x5"],
	31 : ["Normal Bot Intro", "BOT_5x5_INTRO"],
	32 : ["Normal Bot Biggener", "BOT_5x5_BEGINNER"],
	33 : ["Normal Bot Intermediate", "BOT_5x5_INTERMEDIATE"],
	52 : ["Twisted Treeline Bot", "BOT_TT_3x3"],
	65 : ["ARAM", "ARAM_5x5"],
	420 : ["Team Builder Ranked Solo", "TEAM_BUILDER_RANKED_SOLO"],
	440 : ["Ranked Flex", "RANKED_FLEX_SR"],
	610 : ["Darkstar", "DARKSTAR_3x3"],
	76 : ["URF", "URF_5x5"],
	-1 : ["Seasonal Gamemode"]
}

STATIC_DATA = ["spell", "champion", "item", "mastery", "rune", "passive", "profileicon"]