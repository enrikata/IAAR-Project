import tkinter as tk
import socket
import json
import base64
import cv2
import zmq
import numpy as np
from PIL import Image, ImageTk
from communication import recv_message

context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
connected = 0

# Funzione per aggiornare il flusso video sul widget Label
def update_video():
    # Ricevi i dati dal server
    frame = footage_socket.recv_string()
    img = base64.b64decode(frame)
    npimg = np.frombuffer(img, dtype=np.uint8)
    source = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if source is None:
        print("No frame received.\n")
    # Converti il frame in un oggetto PhotoImage
    img = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)
    # Aggiorna l'immagine sul widget Label
    video_label.config(image=img_tk)
    video_label.img = img_tk
    # Richiama la funzione di aggiornamento dopo 10 millisecondi
    if connected == 1:
        root.after(10, update_video)

def connect():
    global footage_socket
    global connected

    if connected == 0:
        footage_socket.connect('tcp://192.168.1.5:5555')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
        connected = 1
        update_video()

def disconnect():
    global footage_socket
    global connected

    if connected == 1:
        footage_socket.disconnect()
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
