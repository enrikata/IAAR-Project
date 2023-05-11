import tkinter as tk
import socket
import base64
import cv2
import zmq
import numpy as np
from PIL import Image, ImageTk
from communication import recv_message, send_message


host = '192.168.90.212'
comm_port = 8000
video_port = 5555
context = zmq.Context()
footage_socket = None
comm_socket = None
connected = 0

# Funzione per aggiornare il flusso video sul widget Label
def update_video():
    # Ricevi i dati dal server
    frame = footage_socket.recv_string()
    img = base64.b64decode(frame)
    npimg = np.frombuffer(img, dtype=np.uint8)
    source = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    # Converti il frame in un oggetto PhotoImage
    img = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)
    # Aggiorna l'immagine sul widget Label
    video_label.config(image=img_tk)
    video_label.img = img_tk
    # Richiama la funzione di aggiornamento dopo 10 millisecondi
    if connected == 1:
        root.after(4, update_video)
    else:
        footage_socket.disconnect(f'tcp://{host}:{video_port}')
        video_label.img = None


def connect():
    global context
    global footage_socket
    global comm_socket
    global connected

    if connected == 0:
        footage_socket = context.socket(zmq.SUB)
        comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        footage_socket.connect(f'tcp://{host}:{video_port}')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, b''.decode('utf-8'))
        comm_socket.connect((host, comm_port))
        connected = 1
        update_video()

def disconnect():
    global footage_socket
    global connected
    global comm_socket

    if connected == 1:
        comm_socket.close()
        connected = 0

def start():
    global connected

    if connected == 1:
        send_message(comm_socket, "message", "START")




# Crea la finestra di tkinter
root = tk.Tk()
root.title("Flusso video dalla webcam")
root.geometry("900x900")

# Crea il widget Label per visualizzare l'immagine del video

connect_button = tk.Button(text="Connect", command=connect)
connect_button.pack()

disconnect_button = tk.Button(text="Disconnect", command=disconnect)
disconnect_button.pack()

start_button = tk.Button(text="Start", command=start)
start_button.pack()
# Avvia la funzione di aggiornamento del flusso video

video_label = tk.Label(root)
video_label.config(width=1280, height=720, bg='black')
video_label.pack()

# Avvia la finestra di tkinter
root.mainloop()
