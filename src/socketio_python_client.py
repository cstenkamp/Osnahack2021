import threading
from time import sleep
import socketio
from queue import Queue
from infowin import InfowinManager
import routing_api
from show_map import show_map
from consts import SEEDHOUSE, GOAL_ADDR, POLL_INTERVAL
from datetime import datetime, timedelta

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
                # sio.emit("getCloseStops", self.coordinates, callback=self.handle_close_stops)
                self.get_close_stops()
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

        # show_map(start_coords, goal_coords, starting_busstops)

    def set_coordinates(self, lat, long):
        self.coordinates = {"lat": lat, "lon": long}

    def get_coords_from_addr(self, goal_addr):
        sio.emit("get_coords_from_addr", {"goal_addr": goal_addr}, callback=self.write_coords)

    def write_coords(self, *args):
        self.goal_coordinates = args[0]

    def get_close_stops(self, *args):
        print(f"asking for close stops @ {self.coordinates}")
        sio.emit("get_close_stops", {"start": self.coordinates, "goal": self.goal_coordinates}, callback=self.write_closestops)

    def write_closestops(self, *args):
        self.close_stops = args[0]
        self.from_coords = args[1]
        print(f"received for coordinates {args[1]}")
        show_map([ma.coordinates["lat"], ma.coordinates["lon"]],
                     [ma.goal_coordinates["lat"], ma.goal_coordinates["lon"]],
                     [
                         i for i in self.close_stops.values()
                     ],
                    fixed_lims = (52.271606115000004, 52.300210185, 8.002402674999999, 8.064383825)
                 )
        best_bet = [k for k,v in self.close_stops.items() if v[2] == "green"][0]
        stop_display.display("Beste Haltestelle: "+best_bet)

if __name__ == "__main__":
    with InfowinManager() as iwm:
        stop_display = iwm.new_window('closest_stop', (700, 800))
        ma = MockApp(stop_display, "localhost", 5000, POLL_INTERVAL)
        ma.set_coordinates(*SEEDHOUSE)
        #goal_addr = input("Wohin willst du?")
        ma.get_coords_from_addr(GOAL_ADDR)
        while not hasattr(ma, "goal_coordinates"):
            sleep(0.1)

        ma.mainloop_thread()
        sleep(10)
        print("changed coordinates")
        ma.set_coordinates(ma.coordinates["lat"], ma.coordinates["lon"]+0.015)
        sleep(30)
        ma.kill()



        # #TODO put this into the actual backend lol
        # #ask our routing-API for the best ways from start to goal
        # data = {"arriveBy": False,
        #         "date": "07-25-2021",
        #         "fromPlace": SEEDHOUSE, #TODO ma.coordinates
        #         "toPlace": (ma.goal_coordinates["lat"], ma.goal_coordinates["lon"]),
        #         "time": "13:00:00",
        #         "mode": ("WALK", "TRANSIT"),
        #         "maxWalkDistance": 3000} #TODO das ist jetzt ne random distanz etc, das muss noch vernünftig gesetzt werden
        # api_response = api.get("http://gtfsr.vbn.de/api/routers/connect/plan", data)
        #
        # #jot down start_coords and goal_coords, we need them later...
        # start_coords = (startcoord := api_response["plan"]["from"])["lat"], startcoord["lon"]
        # goal_coords = (goalcoord := api_response["plan"]["to"])["lat"], goalcoord["lon"]
        #
        # #for all possible itineraries, find the starting bus stop...
        # starting_busstops = set()
        # for itinerary in api_response["plan"]["itineraries"]:
        #     #for all of those, find the first bus-element of that route and find the required bus-stop
        #     first_buselement = [i for i in itinerary["legs"] if i["mode"] == "BUS"][0]
        #     route, fromstop, tostop = first_buselement["route"], first_buselement["from"]["name"], first_buselement["to"]["name"]
        #     print(f"You can walk to {fromstop} to take the {route} to {tostop}")
        #     #add the starting coordinates as tuple to our set of possible startign coordinates...
        #     starting_busstops.add((first_buselement["from"]["lat"], first_buselement["from"]["lon"], "green"))
        # #so now the problem is that it often only selects routes with the very same starting busstop
        # #sooo a better alternative would be to find all busstops around me, and then from all the coordinates of these
        # #try to find a route with zero inital walking
