from influxdb import InfluxDBClient
import json

# save the db

host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'data'

# query = 'select Float_value from cpu_load_short;'
# query_where = 'select Int_value from cpu_load_short where host=$host;'
# bind_params = {'host': 'server01'}

file = open("data.json", 'r')
json_body = json.load(file)

client = InfluxDBClient(host, port, user, password, dbname)

print("Create database: " + dbname)
client.create_database(dbname)

# print("Write points: {0}".format(json_body))
# client.write_points(json_body)

results = client.query('SELECT "degree_celsius" FROM "temperature"')
# results.raw

points = results.get_points()

for point in points:
    print(point)
    print("Time: %s, Temperature: %i" % (point['time'], point['degree_celsius']))
    break
