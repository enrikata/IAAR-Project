import numpy as np
import socket
import base64
import cv2
from threading import Semaphore
from time import sleep
from tensorflow import keras
from tensorflow import convert_to_tensor, expand_dims
from .move_robot import move_robot



def camera_handle(socket, camera) -> None:

    while True:
        _, frame = camera.read()
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        socket.send(jpg_as_text)
        sleep(0.05)


def robot_control(socket_1: socket.socket,
                  socket_2: socket.socket,
                  pos: np.array,
                  sem: Semaphore,
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
            sem.acquire()
            msg = conveyor_conn.recv(1024)
            if "START" in str(msg):
                print("Object detected by the photosensor.")
                _,frame = cam.read()
                frame = frame[450:750, 800:1200]
                cv2.imwrite('model/predictions/' + str(n) + '.jpg', frame)
                n += 1
                frame = cv2.resize(frame, (200, 200))
                frame = convert_to_tensor(frame)
                frame = expand_dims(frame, axis=0)

                prediction = model.predict(frame)
                print(prediction)
                class_detected = np.argmax(prediction)

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

                if class_detected == 2:
                    print("Object not recognised. Remove it from the conveyor belt.")

            elif msg is None:
                print("PLC disconnected. Server listening.")
                sem.release()
                break
            else:
                print("Wrong message.")

            sem.release()
