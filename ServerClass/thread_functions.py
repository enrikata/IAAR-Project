import numpy as np
import socket
import base64
import cv2
from threading import Event
from time import sleep
from tensorflow import keras
from tensorflow import convert_to_tensor, expand_dims
from .move_robot import move_robot
import os


def camera_handle(socket: socket.socket,
                  camera: cv2.VideoCapture,
                  event: Event) -> None:
    while True:
        msg, addr = socket.recvfrom(65535)
        while True:
            ret, frame = camera.read()
            if ret:
                _, buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])
                jpg_as_text = base64.b64encode(buffer)
                socket.sendto(jpg_as_text, addr)
                if event.is_set():
                    event.clear()
                    break


def robot_control(socket_1: socket.socket,
                  socket_2: socket.socket,
                  pos: np.array,
                  event: Event,
                  cam: cv2.VideoCapture,
                  model) -> None:
    while True:
        robot_conn, _ = socket_1.accept()
        print("Robot motion control connected.")
        conveyor_conn, _ = socket_2.accept()
        print("Conveyor belt control connected.")
        print("PLC connected. System started.")
        n = 0
        while True:
            while event.is_set():
                msg = conveyor_conn.recv(1024)
                if "START" in str(msg):
                    print("Object detected by the photosensor.")
                    while True:
                        ret,frame = cam.read()
                        if ret:
                            break

                    if ret:
                        frame = frame[140:340, 200:400]
                        name = os.path.join("model/predictions",str(n) + '.jpg' )
                        cv2.imwrite(name, frame)
                        n += 1
                        frame = cv2.resize(frame, (200, 200))
                        frame = convert_to_tensor(frame)
                        frame = expand_dims(frame, axis=0)

                        prediction = model.predict(frame)
                        print(prediction)
                        class_detected = np.argmax(prediction)

                    if class_detected == 0:
                        print("Square")
                        pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 0, vertical = 0, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 20, vertical = -0.13, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 20, vertical = -0.13, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = 160, horizontal = 0, vertical = 0, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 0)

                    if class_detected == 1:
                        print("Triangle")
                        pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = -3.5, horizontal = 20, vertical = -0.03, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 0, vertical = 0, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 20, vertical = -0.13, gripper = 1)
                        pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 20, vertical = -0.13, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = 210, horizontal = 0, vertical = 0, gripper = 0)
                        pos = move_robot(robot_conn, pos, rotation = 0, horizontal = 0, vertical = 0, gripper = 0)

                    if class_detected == 2:
                        print("Object not recognised. Remove it from the conveyor belt.")

                else:
                    print("Wrong message.")
