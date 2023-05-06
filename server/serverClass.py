import cv2
import zmq
import base64
import json
import threading
import socket

def recv_message(socket: socket.socket, chunk_length: int) -> dict:
    message = bytes()
    n = 0

    while True:
        content = socket.recv(chunk_length)
        message+=content

        if '{' in str(content, 'utf-8'):
            n+=1
        if '}' in str(content, 'utf-8'):
            n-=1
        if n == 0:
            break

    message = json.loads(message)
    return message


def send_message(socket: socket.socket, type: str, payload: str) -> dict:

    packet = {
        "type" : type,
        "payload" : payload
    }

    json_packet = bytes(json.dumps(packet), 'utf-8')
    socket.send(json_packet)
    return packet


def camera_handle(socket: socket.socket) -> None:
    camera = cv2.VideoCapture(0)

    while True:
        grabbed, frame = camera.read()
        encoded, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        socket.send(jpg_as_text)


class serverClass():
    
    def __init__(self, host: str, comm_port: int, video_port: int):
        self.host = host
        self.comm_port = comm_port
        self.video_port = video_port
        self.camera = cv2.VideoCapture(0)
        self.video_socket = zmq.Context().socket(zmq.PUB)
        self.comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_thread = threading.Thread(target=camera_handle, args=(self.video_socket,))
        self.matlab = matlab.engine.start_matlab()

    def start(self):
        self.video_socket.bind(f'tcp://{self.host}:{self.video_port}')
        self.comm_socket.bind((self.host, self.comm_port))
        self.video_thread.start()
        self.comm_socket.listen()
        conn, addr = self.comm_socket.accept()
        print(f"Client connected with address and port {addr}")
        while True:
            message = recv_message(conn, 32)
            if message["payload"] == "START":
                






