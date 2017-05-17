from grabAPI import APICalls

if __name__ == "__main__":
	api_call = RiotAPI()
	name = "all i do is feed"
	res = api_call.get_summoner_by_name(name)
	if(" " in name):
		name = name.replace(" ", "")
	print(res['id'])