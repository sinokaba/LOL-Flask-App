from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase

"""
#app.config["SQLALCHEMY_DATABSE_URI"] = "postgresql://postgres:1WILLchange!@localhost/mydatabase"
postgress user: postgres, password: 1WILLchange
"""
postgres_db = PostgresqlDatabase("FlaskScryer", user="postgres", password="1WILLchange!")

"""
why not remove the players table and just store the highest rated players using flask session, whenever a player is searched if that player's rating is higher then replace
Database normalization, reduce chance of error when updating or inserting data, make things more maintainable. 
	Will make use of foreign key field, where champKey is the thing that ties everything together
	perhaps make separate tables for big data hogs such as players, matchups, item build, runes, skill order, etc.
	http://docs.peewee-orm.com/en/latest/peewee/database.html
	http://docs.peewee-orm.com/en/latest/peewee/querying.html#foreign-keys
https://medium.com/@prabhath_kiran/introduction-to-peewee-and-relations-1c72af26e1b9
https://www.blog.pythonlibrary.org/2014/07/17/an-intro-to-peewee-another-python-orm/
class ItemStats(BaseModel):
	data = ForeignKeyField(ItemData, "item_stats")
	numUsed = IntegerField()
	role = CharField()
	region = CharField()
"""
#The model that which all database tables inherit from, so that they all point to the same database
class BaseModel(Model):
	class Meta:
		database = postgres_db

#static data for items and champion tables. So don't need to waste time making api calls when retrieving their static data
class ChampBase(BaseModel):
	champId = IntegerField(unique=True)
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	name = CharField()
	image = CharField()
	statsRanking = BlobField()
	abilities = BlobField()
	passive = BlobField()
	tips = BlobField()

class ItemBase(BaseModel):
	itemId = IntegerField(unique=True)
	name = CharField()
	image = CharField()
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	cost = IntegerField()
	tags = BlobField(null=True)
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

class ChampRoleOverallStats(BaseModel):
	role = CharField()
	roleTotalPlays = IntegerField()
	roleTotalWins = IntegerField()
	roleCCDealt = IntegerField()
	roleTotalRating = FloatField()
	totalBansByPatch = BlobField()
	totalPlaysByPatch = BlobField()
	addons = ForeignKeyField(ChampAddons, related_name="base", null=True)

class PlayerBasic(BaseModel):
	accountId = BigIntegerField()
	region = CharField()
	name = CharField()

class ChampBasic(BaseModel):
	champId = IntegerField()
	role = CharField()

class PlayerRankStats(BaseModel):
	basicInfo = ForeignKeyField(PlayerBasic, related_name="stats")
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	performance = FloatField()
	wins = IntegerField()
	plays = IntegerField()
	champInfo = ForeignKeyField(ChampBasic, related_name="players")
	class Meta:
		order_by = ('-performance','plays')

class ChampRankStats(BaseModel):
	champId = IntegerField()
	baseInfo = ForeignKeyField(StatsBase, related_name="champ_stats")
	overallStats = ForeignKeyField(ChampRoleOverallStats, related_name="stats_by_rank")
	gameStats = BlobField(null=True)	#gameStats includes, dpg,dmpg, visScore, objScore
	patchStats = BlobField()	#patchstats containts rating, wins, plays. should be blob field?
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	cspm = IntegerField()
	gpm = IntegerField()
	resultByTime = BlobField()	#result by time stores winrate by game length

class TeamBase(BaseModel):
	baseInfo = ForeignKeyField(StatsBase, related_name="teams")
	teamId = IntegerField()	#100 = blue, 200 = red

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

class TeamStats(BaseModel):
	teamInfo = ForeignKeyField(TeamBase, related_name="team_stats")
	gameLength = IntegerField(null=True)
	numRemakes = IntegerField(null=True)
	teamGameStats = BlobField() #firstTower, firstDragon, firstBaron, firstBlood, firstHerald, firstInhib

def initialize_db():
	postgres_db.connect()
	postgres_db.create_tables([
		ChampBase, 
		ItemBase,
		StatsBase,
		ChampRoleOverallStats, 
		ChampAddons,  
		ChampRankStats, 
		TeamStats,
		TeamBase, 
		PlayerBasic,
		PlayerRankStats, 
		ChampBasic,
		GamesVisited, 
		MonsterStats], 
		safe=True)
