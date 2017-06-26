from peewee import *

database = SqliteDatabase("Scryer.db")

class BaseModel(Model):
	class Meta:
		database = database

class Champion(BaseModel):
	champId = IntegerField(unique=True)
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	name = TextField()
	image = TextField()
	tags = TextField()
	abilities = TextField()
	passive = TextField()
	enemyTips = TextField()
	allyTips = TextField()
	armorPerlevel = FloatField()
	attackDamage = FloatField()
	manaPerLvl = FloatField()
	attackSpeed = FloatField()
	mana = FloatField()
	armor = FloatField()
	hp = FloatField()
	hpRegenPerLvl =  FloatField()
	attackSpeedPerLvl = FloatField()
	aaRange = FloatField()
	movementSpeed = FloatField()
	attackDamagePerLvl = FloatField()
	manaRegenPerLevel = FloatField()
	mrPerLvl = FloatField()
	manaRegen = FloatField()
	mr = FloatField()
	hpRegen = FloatField()
	hpPerLvl = FloatField()

class Item(BaseModel):
	itemId = IntegerField(unique=True)
	name = TextField()
	image = TextField()
	#perhaps take out everything below this point as this is static data and can make as amny calls as needed
	#or delete this entire table itself
	cost = IntegerField()
	tags = TextField(null=True)
	des = TextField()
	requiredChamp = TextField(null=True)
	complete = BooleanField()

class ChampStats(BaseModel):
	#test whether clumping up info reduces file size, such as kda into one textfield instead of 3 sperate int fields, as well as the build
	champId = IntegerField()
	totalPlays = IntegerField()
	rolePlays = IntegerField()
	totalWins = IntegerField()
	role = TextField()
	roleWins = IntegerField()
	bans = IntegerField()
	kda = FloatField()
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	oaRating = FloatField()
	roleRating = FloatField()
	spells = TextField()
	players = TextField()
	skillOrder = TextField()
	dpm = FloatField()
	dtpm = FloatField()
	matchups = TextField()
	region = CharField()
	rankTier = CharField()
	runes = TextField()
	startingItems = TextField()
	consumeableItems = TextField()
	earlyBehindItems = TextField()
	earlyAheadItems = TextField()
	coreItems = TextField()
	offenseItems = TextField()
	defenseItems = TextField()

	class Meta:
		order_by = ('totalPlays',)


class Player(BaseModel):
	#test whether putting all scores into one field will save spaces
	accountId = IntegerField()
	summId = IntegerField()
	name = CharField()
	region = CharField()
	champions = TextField()
	kda = FloatField()
	kills = IntegerField()
	deaths = IntegerField()
	assists = IntegerField()
	wins = IntegerField()
	loses = IntegerField()
	oaRating = FloatField()
	tierRating = FloatField()
	kp = FloatField()
	objScore = FloatField()
	visScore = FloatField()
	goldShare = FloatField()
	wpm = FloatField()
	dpm = FloatField()
	dmgShare = FloatField()
	playstyle = TextField()

	class Meta:
		order_by = ('oaRating',)

class GamesVisited(BaseModel):
	matchId = IntegerField()
	region = CharField()

def initialize_db():
	database.connect()
	database.create_tables([Champion, ChampStats, Player, Item, GamesVisited], safe=True)