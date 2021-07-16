import eventlet
import socketio
from geopy.geocoders import Nominatim

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


if __name__ == "__main__":
    app = socketio.WSGIApp(sio, static_files={
        "/": {"content_type": "text/html", "filename": "index.html"}
    })
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)