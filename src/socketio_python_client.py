import threading
from time import sleep
import socketio
from queue import Queue
from infowin import InfowinManager
import routing_api

sio = socketio.Client()

@sio.event
def connect():
    print(f"connection established with ID {sio.sid}")

@sio.event
def connect_response(data):
    print(f"Server said the following: {data}")

@sio.event
def disconnect():
    print("disconnected from server")


class MockApp():
    def __init__(self, stop_display, url, port, poll_interval=5):
        self.stop_display = stop_display
        self.comqueue = Queue()
        sio.connect(f"http://{url}:{port}")
        self.poll_interval = poll_interval
        self.set_coordinates(None, None)

    def _mainloop(self):
        while True:
            while self.comqueue.empty():
                sio.emit("getCloseStops", self.coordinates, callback=self.handle_close_stops)
                sleep(self.poll_interval)
            cont = self.comqueue.get()
            if cont == "kill":
                sio.disconnect()
                break

    def mainloop_thread(self):
        sqlproxy = threading.Thread(target=self._mainloop)
        sqlproxy.setDaemon(True)
        sqlproxy.start()

    def kill(self):
        print("Sending Kill request...")
        self.comqueue.put("kill")

    def handle_close_stops(self, *args):
        close_stops = args[0]
        self.closest_stop = min(close_stops.items(), key=lambda x: x[1]["DistanceInSeconds"])[0]
        print(f"Closest stop is {self.closest_stop} with {close_stops[self.closest_stop]}")
        stop_display.display(self.closest_stop)

    def set_coordinates(self, lat, long):
        self.coordinates = {"lat": lat, "long": long}

    def get_coords_from_addr(self, goal_addr):
        sio.emit("get_coords_from_addr", {"goal_addr": goal_addr}, callback=self.write_coords)

    def write_coords(self, *args):
        self.goal_coordinates = args[0]

if __name__ == "__main__":
    #find start and goal coordinates using geopy
    # goal_addr = input("Wohin willst du?")
    with InfowinManager() as iwm:
        seedhouse_coords = (52.2880747, 8.01449985)
        goal_addr = "Theodor-Heuss-Platz 2. 49074 Osnabrück"
        POLL_INTERVAL = 2
        stop_display = iwm.new_window('closest_stop', (700, 800))
        ma = MockApp(stop_display, "localhost", 5000, POLL_INTERVAL)
        ma.set_coordinates(50, 50)
        ma.get_coords_from_addr(goal_addr)
        while not hasattr(ma, "goal_coordinates"):
            sleep(0.1)

        #TODO put this into the actual backend lol
        #ask our routing-API for the best ways from start to goal
        api = routing_api.API()
        data = {"arriveBy": False,
                "date": "07-25-2021",
                "fromPlace": seedhouse_coords,
                "toPlace": (ma.goal_coordinates["lat"], ma.goal_coordinates["long"]),
                "time": "13:00:00",
                "mode": ("WALK", "TRANSIT"),
                "maxWalkDistance": 3000} #TODO das ist jetzt ne random distanz etc, das muss noch vernünftig gesetzt werden
        api_response = api.get("http://gtfsr.vbn.de/api/routers/connect/plan", data)

        #jot down start_coords and goal_coords, we need them later...
        start_coords = (startcoord := api_response["plan"]["from"])["lat"], startcoord["lon"]
        goal_coords = (goalcoord := api_response["plan"]["to"])["lat"], goalcoord["lon"]

        #for all possible itineraries, find the starting bus stop...
        starting_busstops = set()
        for itinerary in api_response["plan"]["itineraries"]:
            #for all of those, find the first bus-element of that route and find the required bus-stop
            first_buselement = [i for i in itinerary["legs"] if i["mode"] == "BUS"][0]
            route, fromstop, tostop = first_buselement["route"], first_buselement["from"]["name"], first_buselement["to"]["name"]
            print(f"You can walk to {fromstop} to take the {route} to {tostop}")
            #add the starting coordinates as tuple to our set of possible startign coordinates...
            starting_busstops.add((first_buselement["from"]["lat"], first_buselement["from"]["lon"]))
        #so now the problem is that it often only selects routes with the very same starting busstop
        #sooo a better alternative would be to find all busstops around me, and then from all the coordinates of these
        #try to find a route with zero inital walking



        ma.mainloop_thread()
        sleep(3)
        ma.set_coordinates(40, 50)
        sleep(3)
        ma.kill()