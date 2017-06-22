from peewee import *

database = SqliteDatabase("Scryer.db")

class BaseModel(Model):
	class Meta:
		database = database

class Champions(BaseModel):
	champId = IntegerField()
	plays = IntegerField()
	wins = IntegerField()
	bans = IntegerField()
	roles = TextField()
	kda = TextField()
	rating = FloatField()
	players = TextField()
	info = TextField()
	region = CharField()
	rank = CharField()

	class Meta:
		order_by = ('plays',)

class Summoners(BaseModel):
	accountId = IntegerField(unique=True)
	name = CharField()
	region = CharField()
	currentRank = CharField()
	champions = TextField()
	kda = FloatField()
	rating = FloatField()
	stats = TextField()
	wins = IntegerField()
	loses = IntegerField()
	behavior = TextField()

	class Meta:
		order_by = ('rating',)

class GamesVisited(BaseModel):
	matchId = IntegerField(unique=True)
	region = CharField()

def initialize_db():
	database.connect()
	database.create_tables([Champions, Summoners, GamesVisited], safe=True)