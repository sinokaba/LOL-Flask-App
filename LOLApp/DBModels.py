from peewee import *

db_name = "Scryer2"
#db_name = "Scryer"
postgres_db = PostgresqlDatabase(db_name, user="postgres", password="1WILLchange!")

#The model that which all database tables inherit from, so that they all point to the same database
class BaseModel(Model):
	class Meta:
		database = postgres_db

#static data for items and champion tables. So don't need to waste time making api calls when retrieving their static data
class ChampBase(BaseModel):
	champId = IntegerField(unique=True)
	title = CharField()
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	tag1 = CharField()
	tag2 = CharField(null=True)
	role1 = CharField(null=True)
	role2 = CharField(null=True)
	name = CharField()
	image = CharField()
	statsRanking = BlobField()
	abilities = BlobField()
	passive = BlobField()
	tips = BlobField()
	aaRange	= FloatField()
	resource = CharField()
	movespeed = FloatField()
	armor = FloatField()
	armorPL = FloatField()
	ad = FloatField()
	adPL = FloatField()
	hp = FloatField()
	hpPL = FloatField()
	hpRegen = FloatField()
	hpRegenPL = FloatField()
	mr = FloatField() 
	mrPL = FloatField()
	attackspeed = FloatField()
	attackspeedPL = FloatField()
	mana = FloatField()
	manaPL = FloatField()
	manaRegen = FloatField()
	manaRegenPL = FloatField()

class ItemBase(BaseModel):
	itemId = IntegerField(unique=True)
	name = CharField()
	image = CharField()
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	cost = IntegerField()
	tags = BlobField(null=True)
	des = TextField()

class SpellBase(BaseModel):
	spellId = IntegerField(unique=True)
	name = CharField()
	image = CharField()
	des = TextField()

class RuneBase(BaseModel):
	runeId = IntegerField(unique=True)
	name = CharField()
	image = CharField()
	des = TextField()

class MasteryBase(BaseModel):
	masteryId = IntegerField(unique=True)
	name = CharField()
	des = TextField()
#all the tables which store the aggragated stats gathered by the crawler

#Pretty much all stats tables contain this info, so decided to make it its own table and have other tables refer to it. normalization
class StatsBase(BaseModel):
	region = CharField()
	leagueTier = CharField()

#all attributes common to the specific champ and its role, regardless of league, stored here
class ChampAddons(BaseModel):
	spells = BlobField(null=True)
	skillOrder = BlobField(null=True)
	keystone = BlobField(null=True)
	items = BlobField(null=True)
	runes = BlobField(null=True)
	matchups = BlobField()

class ChampOverallStats(BaseModel):
	totalRatingByPatch = BlobField()
	totalBansByPatch = BlobField()
	totalPlaysByPatch = BlobField()	
	totalWinsByPatch = BlobField()
	totalRating = FloatField(null=True)
	totalWins = IntegerField(null=True)
	totalBans = IntegerField(null=True)
	totalPlays = IntegerField(null=True)
	champ = ForeignKeyField(ChampBase, related_name="overall_stats")
	region = CharField()

#new
class ChampStatsByRole(BaseModel):
	role = CharField()
	roleTotalPlays = IntegerField()
	roleTotalWins = IntegerField()
	roleTotalRating = FloatField()
	laning = FloatField()
	addons = ForeignKeyField(ChampAddons, related_name="stats_by_role", null=True)
	overall = ForeignKeyField(ChampOverallStats, related_name="role_stats")
#new
class ChampStatsByRank(BaseModel):
	roleStats = ForeignKeyField(ChampStatsByRole, related_name="rank_stats")
	baseInfo = ForeignKeyField(StatsBase, related_name="champ_stats_by_league")
	gameStats = BlobField(null=True)	#gameStats includes, dpg,dmpg, visScore, objScore
	patchStats = BlobField()	#patchstats containts rating, wins, plays. should be blob field?
	kills = IntegerField(null=True)
	deaths = IntegerField(null=True)
	assists = IntegerField(null=True)
	cspm = IntegerField(null=True)
	gpm = IntegerField(null=True)
	resultByTime = BlobField()	#result by time stores winrate by game length

class PlayerBasic(BaseModel):
	accountId = BigIntegerField(unique=True)
	region = CharField()
	name = CharField()
	rank = BlobField(null=True)
	summonerId = BigIntegerField()

class PlayerRankStats(BaseModel):
	basicInfo = ForeignKeyField(PlayerBasic, related_name="stats")
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	rating = FloatField()
	wins = IntegerField()
	plays = IntegerField()
	champs = ForeignKeyField(ChampOverallStats, related_name="players")
	#champInfo = ForeignKeyField(ChampStatsByRole, related_name="players")
	class Meta:
		order_by = ('-rating','plays')
		
class TeamBase(BaseModel):
	baseInfo = ForeignKeyField(StatsBase, related_name="teams")
	teamId = IntegerField()	#100 = blue, 200 = red

class TeamStats(BaseModel):
	teamInfo = ForeignKeyField(TeamBase, related_name="team_stats")
	gameLength = FloatField(null=True)
	numRemakes = IntegerField(null=True)
	teamGameStats = BlobField() #firstTower, firstDragon, firstBaron, firstBlood, firstHerald, firstInhib

class MonsterStats(BaseModel):
	monsterType = CharField()
	kills = IntegerField()
	wins = IntegerField()
	time = BigIntegerField(null=True) 
	games = IntegerField()
	subtypeData = BlobField(null=True)
	teamInfo = ForeignKeyField(TeamBase, related_name="monster_stats")

class GamesVisited(BaseModel):
	baseInfo = ForeignKeyField(StatsBase, related_name="games_info")
	matchId = BigIntegerField()
	patch = CharField(null=True)

def initialize_db():
	postgres_db.connect()
	postgres_db.create_tables([
		ChampBase, 
		ItemBase,
		SpellBase,
		MasteryBase,
		RuneBase,
		StatsBase,
		ChampOverallStats,
		ChampStatsByRole,
		ChampAddons,  
		ChampStatsByRank,
		TeamStats,
		TeamBase, 
		PlayerBasic,
		PlayerRankStats, 
		GamesVisited, 
		MonsterStats], 
		safe=True)