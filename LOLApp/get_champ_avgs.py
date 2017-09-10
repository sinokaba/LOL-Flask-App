import requests, json 

def get_seed_data():
	url_base = "https://s3-us-west-1.amazonaws.com/riot-developer-portal/seed-data/matches{match_num}.json"
	stats = {}
	for i in range(1,11):
		print(url_base.format(match_num = i))
		print(stats)
		jsonurl = requests.get(url_base.format(match_num = i))
		get_average_stats(jsonurl.json()["matches"], stats)
		print(stats)
	stats_avg = {}
	for role,role_stats in stats.items():
		if(role not in stats_avg):
			stats_avg[role] = {}
		dur = role_stats["game_dur"]/1000
		stats_avg[role] = {
						"kda":(role_stats["kills"]+role_stats["assists"])/role_stats["deaths"],
						"cspm": role_stats["minionsKilled"]/dur,
						"wpm": role_stats["wardsPlaced"]/dur,
						"dmg_share": role_stats["totalDamageDealtToChampions"]/1000,
						"gold_share": role_stats["goldEarned"]/1000,
						"count": role_stats["count"]
						}
	avgs_file = open("champ_rank_stats_avg_by_role.txt", "w")
	for role,stats_val in stats_avg.items():
		avgs_file.write("role: " + role + " " + str(stats_val["count"]) + "\n")
		avgs_file.write("avg kda: " + str(stats_val["kda"]) + "\n")
		avgs_file.write("avg cspm: " + str(stats_val["cspm"]) + "\n")
		avgs_file.write("avg wpm: " + str(stats_val["wpm"]) + "\n")
		avgs_file.write("avg dmg_share: " + str(stats_val["dmg_share"]) + "\n")
		avgs_file.write("avg gold_share: " + str(stats_val["gold_share"]) + "\n")
	avgs_file.close()

def get_average_stats(data, stats_dict):
	for match in data:
		#print(match)
		game_length = match["matchDuration"]/60
		for participant in match["participants"]:
			stats = participant["stats"]
			lane = participant["timeline"]["lane"]
			#print(stats)
			if(lane != "BOTTOM"):
				role = lane
			else:
				role = participant["timeline"]["role"]
			if(role not in stats_dict):
				stats_dict[role] = {
									"kills":stats["kills"], 
									"deaths":stats["deaths"], 
									"assists":stats["assists"], 
									"minionsKilled":stats["minionsKilled"],
									"goldEarned":stats["goldEarned"], 
									"totalDamageDealtToChampions":stats["totalDamageDealtToChampions"]/game_length, 
									"wardsPlaced":stats["wardsPlaced"]/game_length,
									"game_dur":game_length,
									"count":1
									}
			else:
				for stat_name,val in stats_dict[role].items():
					#print("b:", val)
					if(stat_name != "game_dur" and stat_name != "count"):
						if(stat_name == "goldEarned" or stat_name == "totalDamageDealtToChampions"):
							print("before: ", val)
							val += stats[stat_name]/game_length
							print("after: ", val)
						else:
							val += stats[stat_name]
					#print("a:", val)
				stats_dict[role]["count"] += 1
				stats_dict[role]["game_dur"] += game_length


if __name__ == "__main__":
	get_seed_data()