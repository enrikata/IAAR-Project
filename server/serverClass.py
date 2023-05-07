import cv2
import zmq
import base64
import json
import threading
import socket
import matlab.engine

def recv_message(socket: socket.socket, chunk_length: int) -> dict:
    message = bytes()
    n = 0

    while True:
        content = socket.recv(chunk_length)
        if not content:
            return None
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


def camera_handle(socket: socket.socket, camera: cv2.VideoCapture) -> None:

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
        self._camera = cv2.VideoCapture(0)
        self._video_socket = zmq.Context().socket(zmq.PUB)
        self._comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._video_thread = threading.Thread(target=camera_handle, args=(self._video_socket, self._camera))
        self._matlab = matlab.engine.start_matlab()

    def start(self):
        self._video_socket.bind(f'tcp://{self.host}:{self.video_port}')
        self._comm_socket.bind((self.host, self.comm_port))
        self._video_thread.start()
        self._comm_socket.listen()
        print("Server listening.")
        while True:
            conn, addr = self._comm_socket.accept()
            print(f"Client connected with address and port {addr}.")
            while True:
                message = recv_message(conn, 32)
                if message is None:
                    print("Client disconnected.\n Server listening.")
                    break
                if message["payload"] == "START":
                    print("START")
                    ### START THE SYSTEM ###
                if message["payload"] == "STOP":
                    print("STOP")
                    ### STOP THE SYSTEM ###
                if message["payload"] == "DISCONNECT":
                    print("DISCONNECT")
                    ### STOP THE SYSTEM AND SHUT EVERYTHING DOWN ###
                    