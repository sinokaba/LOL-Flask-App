import os

path = os.getcwd()
filenames = os.listdir(path)

for filename in filenames:
	os.rename(filename, filename[:len(filename)-3] + filename[len(filename)-3:].lower())