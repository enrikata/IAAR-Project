import tkinter as tk
import socket
import json
import base64
import cv2
import numpy as np
from PIL import Image, ImageTk

HOST = '192.168.1.5'
PORT = 8000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = 0


def recv_message(socket, chunk_length):
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

    return message

def send_message(socket, type, payload):

    packet = {
        "type" : type,
        "payload" : payload
    }
        
    json_packet = bytes(json.dumps(packet), 'utf-8')
    socket.send(json_packet)
    return packet


# Funzione per aggiornare il flusso video sul widget Label
def update_video():
    # Ricevi i dati dal server
    message = recv_message(client_socket, 32)
    message = json.loads(message)
    data = base64.b64decode(message["payload"])
    # Decodifica i dati come immagine JPEG
    img_np = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    if frame is None:
        print("No frame received.\n")
    # Converti il frame in un oggetto PhotoImage
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)
    # Aggiorna l'immagine sul widget Label
    video_label.config(image=img_tk)
    video_label.img = img_tk
    send_message(client_socket, "response", "OK")
    # Richiama la funzione di aggiornamento dopo 10 millisecondi
    if connected == 1:
        root.after(10, update_video)

def connect():
    global client_socket
    global HOST
    global PORT
    global connected

    if connected == 0:
        client_socket.connect((HOST, PORT))
        connected = 1
        update_video()

def disconnect():
    global client_socket
    global connected

    if connected == 1:
        client_socket.shutdown(socket.SHUT_RDWR)
        connected = 0


# Crea la finestra di tkinter
root = tk.Tk()
root.title("Flusso video dalla webcam")
root.geometry("900x900")

# Crea il widget Label per visualizzare l'immagine del video
video_label = tk.Label(root)
video_label.pack()

connect_button = tk.Button(text="Connect", command=connect)
connect_button.pack()

connect_button = tk.Button(text="Disconnect", command=disconnect)
connect_button.pack()
# Avvia la funzione di aggiornamento del flusso video

# Avvia la finestra di tkinter
root.mainloop()
