import cv2
import zmq
import base64
import threading
import socket


def camera_handle(socket: socket.socket) -> None:
    camera = cv2.VideoCapture(0)

    while True:
        grabbed, frame = camera.read()
        encoded, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        socket.send(jpg_as_text)


class serverClass():
    
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        self.video_socket = zmq.Context().socket(zmq.PUB)
        self.comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_thread = threading.Thread(target=camera_handle, args=(self.video_socket,))

    def start(self):
        self.video_socket.bind('tcp://*:5555')
        self.video_thread.start()
