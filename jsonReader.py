import json
import time

file = open("simData.json", 'r')

reader = json.load(file)

f = open('data.txt', 'w')

# newjson = []
pattern = '%Y.%m.%d %H:%M:%S'
count = 0

for data in reader:
	line = ''
	date_time = str(data['Year']) + '.' + data['Month'] + '.' + str(data['Day']) + ' ' + str(data['Hour']) + ':' + data['Minute'] + ':00'
	epoch = int(time.mktime(time.strptime(date_time, pattern)))
	# s = str(data['Year']) + '-' + data['Month'] + '-' + str(data['Day']) + 'T' + str(data['Hour']) + ':' + data['Minute'] + ':00Z'
	
	if count==0:	
		line += 'temperature degree_celsius=' + str(data['Temperature']) + ' ' + str(epoch)
		count += 1
	else:
		line += '\ntemperature degree_celsius=' + str(data['Temperature']) + ' ' + str(epoch)

	print (line)
	f.write(line)
	

	# d = {}
	# d['measurement'] = 'temperature'
	
	# d['time'] = s
	# d['fields'] = {
	# 	'degree_celsius' : float(data['Temperature'])
	# }
	# newjson.append(d)

f.close()
# with open('data.json', 'w') as file:
# 	json.dump(newjson, file)



	