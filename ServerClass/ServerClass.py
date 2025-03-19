import socket
import threading
import cv2
import numpy as np
from keras.models import load_model
from Communication import send, receive
from .thread_functions import camera_handle, robot_control


class ServerClass():
    
    def __init__(self, params: dict):

        BUFF_SIZE = 65535
        self.host_pc = params["host_pc"]
        self.comm_port = params["comm_port"]
        self.video_port = params["video_port"]
        self.video2port = params["video2_port"]
        self.host_plc = params["host_plc"]
        self.plc_port_1 = params["plc_port_1"]
        self.plc_port_2 = params["plc_port_2"]
        self._footage_camera = cv2.VideoCapture(params["footage_cam_ID"])
        self._AI_camera = cv2.VideoCapture(params["AI_cam_ID"])
        self._AI_model = load_model(params["AI_model_path"])
        self._video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

        self._video2_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._video2_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        
        self._comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._plc_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._plc_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_sync = threading.Event()
        self._video_sync = threading.Event()
        self._system_state = "STOP"
        self._initial_position = np.array([[0],[0],[0],[0],[0],[0],[0],[0]])
        self._video_thread = threading.Thread(target=camera_handle, args=(self._video_socket,
                                                                          self._footage_camera,
                                                                          self._video_sync))
        self._robot_thread = threading.Thread(target=robot_control, args=(self._plc_socket_1,
                                                                          self._plc_socket_2,
                                                                          self._initial_position,
                                                                          self._client_sync,
                                                                          self._AI_camera,
                                                                          self._AI_model))

    def start(self):
        self._video_socket.bind((self.host_pc, self.video_port))
        self._comm_socket.bind((self.host_pc, self.comm_port))
        self._plc_socket_1.bind((self.host_plc, self.plc_port_1))
        self._plc_socket_2.bind((self.host_plc, self.plc_port_2))
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
                message = receive(conn)
                if message is None:
                    if self._system_state == "RUNNING":
                        self._client_sync.clear()
                        self._system_state = "STOP"
                        print("Due to client disconnection, the system has been stopped.")
                    self._video_sync.set()
                    print("Client disconnected.\nServer listening.")
                    break

                if message["payload"] == "START":
                    if self._system_state == "STOP":
                        self._system_state = "RUNNING"
                        self._client_sync.set()
                        send(conn, "message", "System started.\n")
                    else:
                        print("A Start command has been received, but the system is already running.")
                        send(conn, "message", "A Start command has been received, but the system is already running.\n")


                if message["payload"] == "STOP":
                    if self._system_state == "RUNNING":
                        self._client_sync.clear()
                        self._system_state = "STOP"
                        print("System stopped.")
                        send(conn, "message", "System stopped.\n")
                    else:
                        print("A Stop command has been received, but the system is not running.")
                        send(conn, "message", "A Stop command has been received, but the system is not running.\n")
                    