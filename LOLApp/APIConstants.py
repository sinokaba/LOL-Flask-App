from pygal.style import Style

URL = {
	'api_url': 'https://{platform}.api.riotgames.com/lol/{rest}',
	'summoner_by_name': 'summoner/v{api_version}/summoners/by-name/{summonerName}',
	'match_history_all': 'match/v{api_version}/matchlists/by-account/{accountId}?{queue}{current_season}',
	'matches_recent': 'match/v{api_version}/matchlists/by-account/{accountId}/recent',
	'match_data': 'match/v{api_version}/matches/{matchId}',
	'match_timeline': 'match/v{api_version}/timelines/by-match/{matchId}',
	'champ': 'static-data/v{api_version}/champions/{champ_id}?champData=all',
	'current_game': 'spectator/v{api_version}/active-games/by-summoner/{summonerId}',
	'master_players': 'league/v3/masterleagues/by-queue/RANKED_SOLO_5x5',
	'league': 'league/v{api_version}/leagues/by-summoner/{summonerId}',
	'player_league_data': 'league/v{api_version}/positions/by-summoner/{summonerId}',
	'static_data': 'static-data/v{api_version}/{category}?locale=en_US&tags=all',
	'static_ver': 'static-data/v{api_version}/versions',
	'profile_icon': 'http://avatar.leagueoflegends.com/{region}/{summonerName}',
	'summoner_by_summid': 'summoner/v{api_version}/summoners/{summonerId}',
	'summoner_by_acc_id': 'summoner/v{api_version}/summoners/by-account/{accountId}',
	'static_data_imgs': 'http://ddragon.leagueoflegends.com/cdn/{cdn_version}/img/{category}/{name}',
	'items_json': 'http://ddragon.leagueoflegends.com/cdn/{cdn_ver}/data/en_US/item.json',
	'champs_json': 'http://ddragon.leagueoflegends.com/cdn/{cdn_ver}/data/en_US/champion.json'
}	


API_VERSION = '3'

CURRENT_PATCH = '7.16.1'
LAST_PATCH = '7.15.1'

API_KEY = 'RGAPI-db236f3d-f586-4bfe-bba3-ed49d8196590'

PLATFORMS = {
	"NA": 'NA1',
	"EUW": 'EUW1',
	"EUNE": 'EUN1',
	"KR": 'KR',
	'RU': 'RU',
	"BR": "BR1"
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

JUNGLE_CORE = ["1039","1041","1400","1401","1402","1416","3706","3711","3715","1412","1413","1414","1419","1408","1409","1410","1418"]

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
	420 : ["Ranked Solo", "TEAM_BUILDER_RANKED_SOLO"],
	440 : ["Ranked Flex", "RANKED_FLEX_SR"],
	610 : ["Darkstar", "DARKSTAR_3x3"],
	76 : ["URF", "URF_5x5"],
	-1 : ["Seasonal Gamemode"]
}

KEYSTONE_MASTERIES = [6161, 6162, 6164, 6361, 6362, 6363, 6261, 6262, 6263]

STATIC_DATA = ["spell", "champion", "item", "mastery", "rune", "passive", "profileicon"]

STARTING_PLAYERS = {
	"NA":{
		"bronze":75839440,
		"silver":80110621,
		"gold":32267301,
		"platinum":32346594
	},
	"EUW":{
		"bronze":81474049,
		"silver":28189089,
		"gold":20890344,
		"platinum":32780784
	},
	"EUNE":{
		"bronze":36419033,
		"silver":47389637,
		"gold":30681957,
		"platinum":37144012
	},
	"KR":{
		"bronze":26552432,
		"silver":3987416,
		"gold":7907368,
		"platinum":9153059
	}
}

late_game_monsters = ["Vayne", "Jinx", "Kog'Maw", "Twitch", "Tristana", "Vladimir"]
late_game_scalers = ["Nasus", "Veigar", "Jax", "Kindred", "Kassadin", "Cassiopeia", "Gangplank", "Yasuo", "Azir", "Rumble", "Kayle", "Singed", "Master Yi", "Cho'Gath", "Rammus", "Brand", "Thresh", "Syndra", "Tryndamere", "Bard", "Janna", "Fiora", "Zac"]
early_game_bullies = ["Pantheon", "Lee Sin", "Renekton", "Garen", "Caitlyn", "Lucian", "Sona", "Elise", "Zyra", "Annie", "Teemo", "Gnar", "Draven", "Malzahar", "Quinn"]
early_game_eggs = ["Cho'Gath", "Kassadin", "Singed", "Malphite"]

pie_style = Style(
	background='transparent',
	plot_background='transparent',
	value_label_font_size=50,
	label_font_size=60,
	value_font_size=60,
	title_font_size=60,
	tooltip_font_size=0,
	legend_font_size=50,
	opacity='.8',
	opacity_hover='1',
	value_colors=('white','white'),
	transition='400ms ease-in',
)

bar_style = Style(
	background='white',
	plot_background='white',
	opacity='.8',
	opacity_hover='1',
	transition='400ms ease-in'
)

line_style = Style(
	background='white',
	plot_background='white',
	value_label_font_size=50,
	label_font_size=20,
	tooltip_font_size=44,
	opacity='.8',
	opacity_hover='1',
	transition='400ms ease-in',
	legend_font_size=40
)

player_tags = {
	"Sorcerer": "A player who did a ton of Magic damage.",
	"Warrior": "A player who did a ton of Physical damage.", 
	"Farmer": "A player who had a lot of farm.",
	"Daredevil": "A player who took a lot of risk.",
	"Executioner": "A player who had a lot of kills.",
	"Mercenary": "A player who had a lot of killing sprees.",
	"Team Player": "A player who had a lot of assists.",
	"Banker": "A player who had a lot of gold.", 
	"Protector": "A player who dealt the most and longest Crowd Control.", 
	"Godlike": "A player who stayed alive for a long time.",
	"Medic": "A player who healed a lot.", 
	"Juggernaut": "A player who took a lot of damge.", 
	"Visionary": "A player that provided a lot of vision for their team.", 
	"Demolisher": "A player that did a lot of damage to structures."
}