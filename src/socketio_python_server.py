import eventlet
import socketio

sio = socketio.Server()

@sio.event
def connect(sid, environ):
    print("connected: ", sid)
    sio.emit("connect_response", {"ID": sid})

@sio.event
def getCloseStops(sid, data):
    assert "lat" in data and "long" in data
    if data["lat"] > 45:
        response = {"Neumarkt": {"DistanceInSeconds": 2}, "ADP": {"DistanceInSeconds": 15}}
    else:
        response = {"Neumarkt": {"DistanceInSeconds": 15}, "ADP": {"DistanceInSeconds": 5}}
    return response

@sio.event
def disconnect(sid):
    print("disconnect ", sid)

if __name__ == "__main__":
    app = socketio.WSGIApp(sio, static_files={
        "/": {"content_type": "text/html", "filename": "index.html"}
    })
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)