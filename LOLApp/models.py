from peewee import *

database = SqliteDatabase("ScryerTest.db")

"""why not remove the players table and just store the highest rated players using flask session, whenever a player is searched if that player's rating is higher then replace"""
#table for keeping track of most popular items, keystone, summoner spell for each role for each league?
class BaseModel(Model):
	class Meta:
		database = database

class ChampBase(BaseModel):
	champId = IntegerField(unique=True)
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	statsRanking = BlobField()
	name = TextField()
	image = TextField()
	tags = BlobField()
	abilities = BlobField()
	passive = BlobField()
	enemyTips = BlobField()
	allyTips = BlobField()

class ItemData(BaseModel):
	itemId = IntegerField(unique=True)
	name = TextField()
	image = TextField()
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	cost = IntegerField()
	tags = BlobField(null=True)
	des = TextField()

"""Database normalization, reduce chance of error when updating or inserting data, make things more maintainable. 
	Will make use of foreign key field, where champKey is the thing that ties everything together
	perhaps make separate tables for big data hogs such as players, matchups, item build, runes, skill order, etc.
	http://docs.peewee-orm.com/en/latest/peewee/database.html
	http://docs.peewee-orm.com/en/latest/peewee/querying.html#foreign-keys
https://medium.com/@prabhath_kiran/introduction-to-peewee-and-relations-1c72af26e1b9
https://www.blog.pythonlibrary.org/2014/07/17/an-intro-to-peewee-another-python-orm/
"""
"""
class ItemStats(BaseModel):
	data = ForeignKeyField(ItemData, "item_stats")
	numUsed = IntegerField()
	role = CharField()
	region = CharField()
"""


#all attributes common to the specific champ andn its role, regardless of league, stored here
class ChampAddons(BaseModel):
	spells = BlobField(null=True)
	skillOrder = BlobField(null=True)
	keystone = BlobField(null=True)
	items = BlobField(null=True)
	runes = BlobField(null=True)
	matchups = BlobField()

class ChampRoleData(BaseModel):
	region = CharField()
	champId = IntegerField()
	role = CharField()
	roleTotalPlays = IntegerField()
	roleTotalWins = IntegerField()
	roleCCDealt = IntegerField()
	roleTotalRating = FloatField()
	totalBansByPatch = BlobField()
	addons = ForeignKeyField(ChampAddons, related_name="base", null=True)

class ChampPlayer(BaseModel):
	accountId = BigIntegerField()
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	performance = FloatField()
	wins = IntegerField()
	plays = IntegerField()
	champs = ForeignKeyField(ChampRoleData, related_name="player_details")
	class Meta:
		order_by = ('-performance','plays')

class ChampRankStats(BaseModel):
	#gameStats includes, dpg,dmpg, visScore, objScore
	gameStats = BlobField(null=True)
	#patchstats containts rating, wins, plays. should be blob field?
	patchStats = BlobField()
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	cspm = IntegerField()
	gpm = IntegerField()
	leagueTier = CharField()
	#result by time stores winrate by game length
	resultByTime = BlobField()
	champ = ForeignKeyField(ChampRoleData, related_name="champ_rank_stats")

class TeamBase(BaseModel):
	region = CharField()
	leagueTier = CharField()
	#100 = blue, 200 = red
	teamId = IntegerField()

class MonsterStats(BaseModel):
	monsterType = CharField()
	kills = IntegerField()
	wins = IntegerField()
	time = BigIntegerField(null=True) 
	games = IntegerField()
	subtypeData = BlobField(null=True)
	team = ForeignKeyField(TeamBase, related_name="monster_stats")

class GamesVisited(BaseModel):
	matchId = BigIntegerField()
	region = CharField()
	Patch = CharField(null=True)

class TeamStats(BaseModel):
	teamInfo = ForeignKeyField(TeamBase, related_name="team_stats")
	numRemakes = IntegerField(null=True)
	teamGameStats = BlobField() #firstTower, firstDragon, firstBaron, firstBlood, firstHerald, firstInhib

def initialize_db():
	database.connect()
	database.create_tables([
		ChampBase, 
		ChampRoleData, 
		ChampAddons, 
		ItemData, 
		ChampRankStats, 
		TeamStats,
		TeamBase, 
		ChampPlayer, 
		GamesVisited, 
		MonsterStats], 
		safe=True)
