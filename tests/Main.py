from grabAPI import APICalls

if __name__ == "__main__":
	api_call = RiotAPI('383ade41-23a5-4e68-a0e1-63ce90c30f85')
	name = "all i do is feed"
	res = api_call.get_summoner_by_name(name)
	if(" " in name):
		name = name.replace(" ", "")
	print(res['id'])