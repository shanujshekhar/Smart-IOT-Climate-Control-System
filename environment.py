from influxdb import InfluxDBClient
import time
import json
from math import sqrt
from copy import deepcopy
import pdb
import datetime

# Initial Room Temp: Other than 0

class Heater:
    def __init__(self, target):
        self.enabled = False
#         target_temp of room = 10 (Assumption)
        self.target_temp = target        
#         each neighbour contributes = 0.1, heater = 1
        self.contribution = 1
#         power: high, low (settings)
        self.power = 1 
        
    def check_temp(self, room):
        if room.old_state['degree_celsius'] > self.target_temp :
            self.enabled = False
        else:
            self.enabled = True
        return self.enabled

def write_to_file(file, build_temp, rooms, env, heater_on, target_temp):
        
    room_temp = ''

    for room in rooms:
        room_temp += str(room.current_state['degree_celsius']) + ','

    if heater_on==True:
        file.write(str(build_temp) + ',' + room_temp + str(env.current_state['degree_celsius']) + ',' + '1,' + str(target_temp) + '\n')
    else:
        file.write(str(build_temp) + ',' + room_temp + str(env.current_state['degree_celsius']) + ',' + '0,' + str(target_temp) + '\n')
        
    
# create a state class
# create a StateObject parent that every class inherits from for better sense


class StateObject:
    def __init__(self, initial_state):
        self.current_state = initial_state
        self.old_state = initial_state
    def updateState(self, new_state):
        self.old_state = deepcopy(self.current_state)
        self.current_state = deepcopy(new_state)

        
class Environment(StateObject):
    def __init__(self, initial_state):
        self.current_state = initial_state
        self.old_state = initial_state


class Room(StateObject):
    def __init__(self, initial_state, room_no, heater):
        self.heater_component = heater
        self.room_no = room_no
        
        if(room_no==1):
            self.neighbours = ['e', 'e', 2, 8, 9, 'e', 'e', 'e']
        elif(room_no==2):
            self.neighbours = ['e', 'e', 1, 9, 3, 'e']
        elif(room_no==3):
            self.neighbours = ['e', 'e', 2, 9, 4, 'e']
        elif(room_no==4):
            self.neighbours = ['e', 'e', 3, 9, 5, 'e']
        elif(room_no==5):
            self.neighbours = ['e', 'e', 4, 9, 6, 'e', 'e']
        elif(room_no==6):
            self.neighbours = ['e', 'e', 9, 5, 'e', 'e']
        elif(room_no==7):
            self.neighbours = ['e', 'e', 9, 9, 9, 'e']
        elif(room_no==8):
            self.neighbours = ['e', 'e', 1, 9, 9, 'e']
        elif(room_no==9):
            self.neighbours = ['e', 'e', 1, 2, 3, 4, 5, 6, 7, 7, 7, 8, 8, 'e']
        
        self.current_state = initial_state
        self.old_state = initial_state
        
    def updateState(self, new_state, env, rooms):
        self.old_state = self.current_state
        current_state = deepcopy(new_state)

        change = 0
        heater_on = False
        
#         contribution = how much heater or neighbour is contributing to rate of change in temperature
#         Checking if heater is enabled or disabled
#         contribution of heater = 1 (Assumption)
        if self.heater_component.check_temp(self)==True :
            heater_on = True
            change = self.heater_component.contribution * ((self.heater_component.target_temp - self.old_state['degree_celsius']))


#         Room's Contribution depends on number of neighbours
        room_contribution = 1/len(self.neighbours)
#         Calculating contribution for each neighbour        
        for neighbour in self.neighbours:
            if neighbour=='e':
#                 change in env (new_state) and room's old state
                change += room_contribution * (new_state['degree_celsius'] - self.old_state['degree_celsius'])
            else:
#                 change in room's neighbours's old_state and room's old state            
                change += room_contribution * (rooms[int(neighbour)-1].old_state['degree_celsius'] - self.old_state['degree_celsius'])

        
#         Calculating new_state of room by including contribution of heater and room's neighbours
        new_temperature = (self.old_state['degree_celsius'] + change)
        current_state['degree_celsius'] = new_temperature
        return current_state
        
#         self.current_state['degree_celsius'] = sqrt(abs(new_state['degree_celsius'] - self.old_state['degree_celsius'])) * sign


class Building:
    def __init__(self, initial_state, num_rooms, target=10):
        self.heater = Heater(target)
        self.rooms = [Room(initial_state, i+1, self.heater) for i in range(num_rooms)]            
            
    def updateState(self, new_state, env):
        new_state_rooms = []
        for i in range(len(self.rooms)):
            new_state_rooms.append(self.rooms[i].updateState(new_state, env, self.rooms))

        for i in range(len(self.rooms)):
            self.rooms[i].old_state = deepcopy(self.rooms[i].current_state)
            self.rooms[i].current_state = deepcopy(new_state_rooms[i])

         
class Simulation:
    def __init__(self, initial_state, num_rooms, birthday):
        self.num_rooms = num_rooms       
        self.target = 23.3
        self.env = Environment(initial_state)
        self.house = Building(initial_state, num_rooms, self.target)
        
        self.birthday = birthday
        self.state = initial_state
    def updateState(self, timestamp, client, file):
        # query the db for the state
        
        response = client.query("SELECT degree_celsius FROM temperature WHERE time = '" + timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") + "'")
    
#         print(len(response))
        if len(response) != 0:
            print(timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"))
            for i in response.get_points():
                self.state = i
            
        self.env.updateState(self.state)
        self.house.updateState(self.state, self.env)
        
#       Assumption - Room 1 is considered as the building temperature for now
        avg_building_temp = self.house.rooms[0].current_state['degree_celsius']
        
        if(avg_building_temp > self.target):
            heater_on = False
        else:
            heater_on = True
        
        write_to_file(file, avg_building_temp, self.house.rooms, self.env, heater_on, self.house.heater.target_temp)

    def showUpdates(self):
        print('ENVIRONMENT')
        print('Old temperature:', self.env.old_state['degree_celsius'])
        print('Updated temperature:', self.env.current_state['degree_celsius'])

        print('BUILDING')
        for i in range(self.num_rooms):
            print('******************  Room {}  *********************'.format(i+1))
            print('Neighbours: ', self.house.rooms[i].neighbours)
            n = self.house.rooms[i].neighbours
            for j in range(len(n)):
                if(n[j]!='e'):
                    print('    Room ', n[j],': ', self.house.rooms[int(n[j])-1].current_state['degree_celsius'])
                else:
                    print('    Environment: ', self.env.current_state['degree_celsius'])
            print('Old temperature:', self.house.rooms[i].old_state['degree_celsius'])
            print('Updated temperature:', self.house.rooms[i].current_state['degree_celsius'])
        print("------------------------------------------")
              
def main():
    initial_state = json.loads('{"time": "2020-01-16T00:00:00Z", "degree_celsius": 0.00}') #initial state
    num_rooms = 9
    birthday = datetime.datetime.strptime("2020-01-16T00:00:00Z","%Y-%m-%dT%H:%M:%SZ")
    sim = Simulation(initial_state, num_rooms, birthday)
    time_unit = datetime.timedelta(minutes=1)
    timestamp = birthday
    # print("hi", birthday + time_unit)
    host = 'localhost'
    port = 8086
    user = 'root'
    password = 'root'
    dbname = 'data'


    client = InfluxDBClient(host, port, user, password, dbname)

#     print(client)
#     states = client.query('SELECT "degree_celsius" FROM "temperature"').get_points()
#     print(states)
    count = 1
    file = open('output_safe.csv', 'w')
    rooms = ''
    for i in range(num_rooms):
        rooms += 'room' + str(i+1) + ','
    
    file.write('building_temp,' + rooms + 'env_temp,heater,target_temp\n')
    
#     while True:
    for i in range(n):
        timestamp += time_unit
#         print(timestamp)
        sim.updateState(timestamp, client, file)   
    file.close()

n = int(input("Enter how many hours you want to visualize since creation:")) * 60
if __name__ == '__main__':
    main()
