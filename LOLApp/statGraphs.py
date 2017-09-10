import pygal
from .APIConstants import *

class StatGraphs():

	def get_half_pie(self, data, stat, colors, data_names, args=None):
		pie_style.colors = colors
		print("graph colors: ", colors)
		percent = round(stat*100,2)
		if(percent <= 50):
			label_1 = ""
			label_2 = str(percent) + "%"
		else:
			label_1 = str(percent) + "%"
			label_2 = ""
		half_pie = pygal.Pie(
			half_pie=True, 
			show_legend=True,
			legend_at_bottom=True, 
			legend_at_bottom_columns=2,
			print_labels=True,
			show_tooltip=False,
			print_values_position='bottom',
			style=pie_style
			)
		half_pie.add(data_names[0],[
			{'value': data[0], 'label': label_1}])
		half_pie.add(data_names[1],[
			{'value': data[1]-data[0], 'label': label_2}]
			)
		return half_pie.render_data_uri()

	def get_stacked_bar(self, labels, data, colors, args=None):
		bar_style.colors = colors
		stacked_hor_bar = pygal.StackedBar(
							show_legend=True,
							fill=True,
							height=240,
							show_y_guides=False,
							style=bar_style
						)
		stacked_hor_bar.x_labels = labels
		for label,val in data.items():
			stacked_hor_bar.add(label, val)
		return stacked_hor_bar.render_data_uri()

	def get_standard_bar(self, data, colors, args=None):
		pass

	def get_patch_line(self, data, colors, args=None):
		#print(data, args)
		metrics = {"Playrate":{"key":"plays"}, "Rating":{"key":"rating"},  "Winrate":{"key":"wins"}}
		patches = ["7.12.1", "7.13.1", "7.14.1", "7.15.1", "7.16.1"]
		charts = {}
		line_style.colors = colors

		for metric,m_data in metrics.items():
			key = m_data["key"]
			#print(key, data[patches[0]][key], data[patches[1]][key], data[patches[2]][key])
			line_chart = pygal.Line(
				height=400, 
				max_scale=4, 
				show_y_guides=False,
				show_legend=False, 
				fill=True, 
				style=line_style, 
				x_title='Patch')
			line_chart.x_labels = patches
			if(metric == "Playrate"):
				vals = []
				for patch in patches:
					if(patch not in data or patch not in args):
						vals.append(None)
					else:	
						vals.append(round((data[patch][key]/args[patch])*100,2))
				line_chart.add(metric, vals)
			else:
				vals = []
				for patch in patches:
					if(patch in data):
						if(metric != "Rating"):
							multiplier = 100
						else:
							multiplier = 1
						vals.append(round((data[patch][key]/data[patch]["plays"])*multiplier,2))
					else:
						vals.append(None)
				line_chart.add(metric, vals)
			charts[metric] = line_chart.render_data_uri()
		return charts

	def get_wr_line(self, data, colors):
		print("data: ", data)
		game_lengths = ["0-20", "20-30", "30-40", "40+"]
		line_style.colors = colors
		line_chart = pygal.Line(
			height=400, 
			max_scale=4, 
			show_y_guides=False,
			show_legend=False, 
			fill=True, 
			style=line_style, 
			x_title='Minute intervals')
		line_chart.x_labels = game_lengths
		values = []
		for game_length in game_lengths:
			if(game_length in data):
				values.append(round((data[game_length]["wins"]/data[game_length]["games"])*100,2))
			else:
				values.append(None)
		line_chart.add("Winrate", values)
		return line_chart.render_data_uri()
