import socket
import cv2
import json
import threading
import base64
from communication.communication import send_message, recv_message


def camera_thread(socket):
    # Cattura il video dalla webcam
    cap = cv2.VideoCapture(0)

    # Ciclo while per catturare continuamente i frame video dalla webcam e inviarli al client
    while True:
        ret, frame = cap.read()
        # Codifica il frame come JPEG
        _, img_encoded = cv2.imencode('.jpg', frame)
        # Converti il frame in bytes
        data = img_encoded.tobytes()
        data = base64.b64encode(data).decode('utf-8')
        send_message(socket, "video_frame", data)
   


HOST = '192.168.1.5' # Indirizzo IP del server
PORT = 8000 # Numero di porta del server

# Crea la socket del server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Ascolta per connessioni in ingresso
server_socket.bind((HOST, PORT))
server_socket.listen(1)

# Accetta la connessione dal client
conn, addr = server_socket.accept()
print('Connesso da', addr)

cam_thread = threading.Thread(target=camera_thread, args=(conn,))
cam_thread.start()



#### CREARE CLASSE SERVER PER GESTIRE FLUSSO WEBCAM E THREADS
#### CREARE MODULO PER GESTIONE, RICEZIONE E INVIO MESSAGGI CON JSON
#### GESTIRE TUTTI I FLUSSI LATO CLIENT CON THREAD SEPARATI PER LA RICEZIONE E L'INVIO DEI MESSAGGI E L'AGGIORNAMENTO DELLA FINESTRA DELLA GUI
