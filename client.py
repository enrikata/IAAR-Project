import tkinter as tk
import socket
import threading
import yaml
import base64
import cv2
import zmq
import numpy as np
from PIL import Image, ImageTk
from Communication import send, receive

with open('conf/configuration.yml') as conf_file:
    params = yaml.safe_load(conf_file)

host = params["host_pc"]
comm_port = params["comm_port"]
video_port = params["video_port"]
context = zmq.Context()
footage_socket = None
comm_socket = None
connected = 0
msg_list = []

def socket_receiver(s, list):
    while True:
        msg = receive(s)
        if msg is not None:
            list.append(msg["payload"])
        else:
            list = []
            return
        

def update_root():
    frame = footage_socket.recv_string()
    img = base64.b64decode(frame)
    npimg = np.frombuffer(img, dtype=np.uint8)
    source = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
    #img = img.resize((600,600))
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)
    video_label.config(image=img_tk)
    video_label.img = img_tk

    if len(msg_list) != 0:
        msg = msg_list.pop(0)
        text_box.state = 'normal'
        text_box.insert('end', msg)
        text_box.state = 'disabled'
    if connected == 1:
        root.after(4, update_root)
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
        comm_thread = threading.Thread(socket_receiver, (comm_socket, msg_list))
        update_root()

def disconnect():
    global connected
    global comm_socket

    if connected == 1:
        comm_socket.close()
        connected = 0

def start():
    if connected == 1:
        send(comm_socket, "message", "START")

def stop():
    if connected == 1:
        send(comm_socket, "message", "STOP")




root = tk.Tk()
root.title("Robot Control Interface")
root.geometry("900x900")


connect_button = tk.Button(text="Connect", command=connect)
connect_button.pack()

disconnect_button = tk.Button(text="Disconnect", command=disconnect)
disconnect_button.pack()

start_button = tk.Button(text="Start", command=start)
start_button.pack()

stop_button = tk.Button(text="Stop", command=stop)
stop_button.pack()

text_box = tk.Text(root, height=10, width=70, state = 'disabled')
text_box.pack()

video_label = tk.Label(root)
video_label.config(width=600, height=600, bg='black')
video_label.pack()

root.mainloop()
