import cv2
import zmq
import base64
import json
import threading
import socket
import numpy as np
from time import sleep
from move_robot import move_robot
from keras.models import load_model
from tensorflow import keras
from tensorflow import convert_to_tensor, expand_dims

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
        sleep(0.05)


def robot_control(socket_1: socket.socket,
                  socket_2: socket.socket,
                  pos: np.array,
                  sem: threading.Semaphore,
                  cam: cv2.VideoCapture,
                  model) -> None:
    while True:
        robot_conn, _ = socket_1.accept()
        print("Robot motion control connected.")
        conveyor_conn, _ = socket_2.accept()
        print("Conveyor belt control connected.")
        print("PLC Connected. System started.")
        while True:
            sem.acquire()
            msg = conveyor_conn.recv(6)
            if "START" in str(msg):
                print("Object detected by the photosensor.")
                ret, frame = cam.read()
                if not ret:
                    print("Eccezione da gestire.")
                    raise Exception
                frame = frame[450:750, 800:1200]
                frame = cv2.resize(frame, (200, 200))
                frame = convert_to_tensor(frame)
                frame = expand_dims(frame, axis=0)

                prediction = model.predict(frame)
                print(prediction)
                class_detected = int(np.round(prediction, decimals=0))

                if class_detected == 0:
                    pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 0, vertical = 0, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 20, vertical = -0.13, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 20, vertical = -0.13, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 0, vertical = 0, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 0)

                if class_detected == 1:
                    pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 0, vertical = 0, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 20, vertical = -0.13, gripper = 1)
                    pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 20, vertical = -0.13, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 0, vertical = 0, gripper = 0)
                    pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 0)

            elif msg is None:
                print("PLC disconnected. Server listening.")
                sem.release()
                break
            else:
                print("Wrong message.")

            ### GET THE FRAME FROM THE WEBCAM ###
            ### RUN THE AI ALGORITHM ###
            ### CALL MOVE ROBOT FUNCTION ###
            sem.release()



class serverClass():
    
    def __init__(self, host: str, comm_port: int, video_port: int):
        self.host = host
        self.comm_port = comm_port
        self.video_port = video_port
        self._footage_camera = cv2.VideoCapture(1)
        self._AI_camera = cv2.VideoCapture(0)
        self._AI_model = load_model('model/MLModel.keras')
        self._video_socket = zmq.Context().socket(zmq.PUB)
        self._comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._plc_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._plc_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_sync = threading.Semaphore(0)
        self._system_state = "STOP"
        self._initial_position = np.array([[0],[0],[0],[0],[0],[0],[0],[0]])
        self._video_thread = threading.Thread(target=camera_handle, args=(self._video_socket,
                                                                          self._footage_camera))
        self._robot_thread = threading.Thread(target=robot_control, args=(self._plc_socket_1,
                                                                          self._plc_socket_2,
                                                                          self._initial_position,
                                                                          self._client_sync,
                                                                          self._AI_camera,
                                                                          self._AI_model))

    def start(self):
        self._video_socket.bind(f'tcp://{self.host}:{self.video_port}')
        self._comm_socket.bind((self.host, self.comm_port))
        self._plc_socket_1.bind(('192.168.0.241', 2000))
        self._plc_socket_2.bind(('192.168.0.241', 2001))
        self._video_thread.start()
        self._comm_socket.listen()
        self._plc_socket_1.listen()
        self._plc_socket_2.listen()
        self._robot_thread.start()
        print("Server listening.")
        while True:
            conn, addr = self._comm_socket.accept()
            print(f"Client connected with address and port {addr}.")
            while True:
                message = recv_message(conn, 32)
                if message is None:
                    if self._system_state == "RUNNING":
                        self._client_sync.acquire()
                        self._system_state = "STOP"
                        print("Due to client disconnection, the system has been stopped.")
                    print("Client disconnected.\n Server listening.")
                    break

                if message["payload"] == "START":
                    if self._system_state == "STOP":
                        self._system_state = "RUNNING"
                        self._client_sync.release()
                    else:
                        print("A Start command has been received, but the system is already running.")

                if message["payload"] == "STOP":
                    if self._system_state == "RUNNING":
                        self._client_sync.acquire()
                        self._system_state = "STOP"
                        print("System stopped.")
                    else:
                        print("A Stop command has been received, but the system is not running.")
                    