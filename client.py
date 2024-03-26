import tkinter as tk
import socket
import threading
import yaml
import base64
import cv2
import imutils
import numpy as np
from PIL import Image, ImageTk
from Communication import send, receive

BUFF_SIZE = 65535

with open('conf/configuration.yml') as conf_file:
    params = yaml.safe_load(conf_file)

host = params["host_pc"]
comm_port = params["comm_port"]
video_port = params["video_port"]
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
    packet, _ = footage_socket.recvfrom(BUFF_SIZE)
    data = base64.b64decode(packet,' /')
    npdata = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(npdata,1)
    
    target_width, target_height = 320, 352  
    aspect_ratio = img.shape[1] / img.shape[0]
    if aspect_ratio > target_width / target_height:
        target_height = int(target_width / aspect_ratio)
    else:
        target_width = int(target_height * aspect_ratio)
    resized_frame = cv2.resize(img, (target_width, target_height))
    img_pil = Image.fromarray(resized_frame)
    img_tk = ImageTk.PhotoImage(img_pil)
    video_label.config(image=img_tk)
    video_label.img = img_tk

    if len(msg_list) != 0:
        msg = msg_list.pop(0)
        text_box.config(state = 'normal')
        text_box.insert('end', msg)
        text_box.config(state = 'disabled')
    if connected == 1:
        root.after(2, update_root)
    else:
        footage_socket.close()
        video_label.img = None



def connect():
    global footage_socket
    global AI_socket
    global comm_socket
    global connected

    if connected == 0:
        footage_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        footage_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,BUFF_SIZE)
        footage_socket.sendto(b'connect', (host, video_port))

        AI_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        AI_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,BUFF_SIZE)
        AI_socket.sendto(b'connect', (host, video_port))


        comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        comm_socket.connect((host, comm_port))

        connected = 1
        comm_thread = threading.Thread(target=socket_receiver, args=(comm_socket, msg_list))
        comm_thread.start()
        text_box.config(state = 'normal')
        text_box.insert('end', "Connected.\n")
        text_box.config(state = 'disabled')
        update_root()

def disconnect():
    global connected
    global comm_socket

    if connected == 1:
        comm_socket.close()
        connected = 0
        text_box.config(state = 'normal')
        text_box.insert('end', "Disconnected.\n")
        text_box.config(state = 'disabled')


def start():
    if connected == 1:
        send(comm_socket, "message", "START")

def stop():
    if connected == 1:
        send(comm_socket, "message", "STOP")

def on_closing():
    stop()
    disconnect()
    root.destroy() 



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
video_label.config(width=300, height=600, bg='black', anchor='nw')
video_label.pack(side=tk.LEFT)

video_label2 = tk.Label(root)
video_label2.config(width=300, height=600, bg='white',anchor='ne')
video_label2.pack(side=tk.RIGHT)



root.protocol("WM_DELETE_WINDOW", on_closing)  
root.mainloop()
