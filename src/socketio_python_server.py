import eventlet
import socketio
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta

import routing_api

sio = socketio.Server()

@sio.event
def connect(sid, environ):
    print("connected: ", sid)
    sio.emit("connect_response", {"ID": sid})

@sio.event
def getCloseStops(sid, data):
    assert "lat" in data and "lon" in data
    if data["lat"] > 45:
        response = {"Neumarkt": {"DistanceInSeconds": 2}, "ADP": {"DistanceInSeconds": 15}}
    else:
        response = {"Neumarkt": {"DistanceInSeconds": 15}, "ADP": {"DistanceInSeconds": 5}}
    return response

@sio.event
def disconnect(sid):
    print("disconnect ", sid)

@sio.event
def get_coords_from_addr(sid, data):
    geolocator = Nominatim(user_agent="appapp123")
    location = geolocator.geocode(data["goal_addr"])
    goal_coords = {"lat": location.latitude, "lon": location.longitude}
    return goal_coords

@sio.event
def get_close_stops(sid, data):
    api = routing_api.API()
    best = api.bestRoutes(data["start"], data["goal"])
    best = {k: {**v, **{"next_bus": (nb := datetime.fromtimestamp(
        [i for i in v["plan"]["itineraries"][0]["legs"] if i["mode"] == "BUS"][0]["startTime"] / 1000)),
                        "walk_time": (wt := timedelta(seconds=v["plan"]["itineraries"][0]["legs"][0]["duration"])),
                        "arrive_time": (at := nb - datetime.now()),
                        "arrive_early": (at - wt).total_seconds(),
                        "goal_time": v["plan"]["itineraries"][0]["endTime"]
                        }
                }
            for k, v in best.items()
            if "plan" in v
            }
    stop_positions = {k: [*[float(i) for i in v["requestParameters"]["intermediatePlaces"].split(",")],
                          "green" if v["goal_time"] <= min([i["goal_time"] for i in best.values()]) else (
                              "yellow" if v["arrive_early"] < sum([v["arrive_early"] for v in best.values()]) / len(
                                  best) else "red")] for k, v in best.items()}
    return stop_positions, data["start"]





if __name__ == "__main__":
    app = socketio.WSGIApp(sio, static_files={
        "/": {"content_type": "text/html", "filename": "index.html"}
    })
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)