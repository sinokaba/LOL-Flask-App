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
	laning = FloatField()
	players = TextField()
	info = TextField()
	region = CharField()
	rank = CharField()

	class Meta:
		order_by = ('plays',)

class Summoners(BaseModel):
	account_id = IntegerField()
	name = CharField(unique=True)
	#icon = TextField()
	region = CharField()
	league = TextField()
	#champions = TextField()
	matches = TextField()
	#position_score = IntegerField()
	#mechanics_score = IntegerField()
	#vision_score = IntegerField()
	#objective_score = IntegerField()

class GamesVisited(BaseModel):
	match_id = IntegerField(unique=True)

def initialize_db():
	database.connect()
	database.create_tables([Champions, Summoners, GamesVisited], safe=True)