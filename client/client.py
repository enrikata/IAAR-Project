import tkinter as tk
import socket
import json
import base64
import cv2
import zmq
import numpy as np
from PIL import Image, ImageTk

host = '192.168.1.5'
comm_port = 8000
video_port = 5555
context = zmq.Context()
footage_socket = None
comm_socket = None
connected = 0

def recv_message(socket: socket.socket, chunk_length: int) -> dict:
    message = bytes()
    n = 0

    while True:
        content = socket.recv(chunk_length)
        if content is None:
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

def update_video():
    frame = footage_socket.recv_string()
    img = base64.b64decode(frame)
    npimg = np.frombuffer(img, dtype=np.uint8)
    source = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)
    video_label.config(image=img_tk)
    video_label.img = img_tk
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
    global connected
    global comm_socket

    if connected == 1:
        comm_socket.close()
        connected = 0

def start():
    if connected == 1:
        send_message(comm_socket, "message", "START")




root = tk.Tk()
root.title("Flusso video dalla webcam")
root.geometry("900x900")


connect_button = tk.Button(text="Connect", command=connect)
connect_button.pack()

disconnect_button = tk.Button(text="Disconnect", command=disconnect)
disconnect_button.pack()

start_button = tk.Button(text="Start", command=start)
start_button.pack()

video_label = tk.Label(root)
video_label.config(width=1280, height=720, bg='black')
video_label.pack()

root.mainloop()
