import socket
import cv2
import json
import threading
import base64
import zmq
from communication.communication import send_message


def camera_thread(socket):
    # Cattura il video dalla webcam
    camera = cv2.VideoCapture(0)

    while True:
        grabbed, frame = camera.read()
        encoded, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        footage_socket.send(jpg_as_text)


context = zmq.Context()
footage_socket = context.socket(zmq.PUB)
footage_socket.bind('tcp://*:5555')

cam_thread = threading.Thread(target=camera_thread, args=(footage_socket,))
cam_thread.start()



#### CREARE CLASSE SERVER PER GESTIRE FLUSSO WEBCAM E THREADS
#### CREARE MODULO PER GESTIONE, RICEZIONE E INVIO MESSAGGI CON JSON
#### GESTIRE TUTTI I FLUSSI LATO CLIENT CON THREAD SEPARATI PER LA RICEZIONE E L'INVIO DEI MESSAGGI E L'AGGIORNAMENTO DELLA FINESTRA DELLA GUI
