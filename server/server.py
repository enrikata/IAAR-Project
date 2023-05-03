import socket
import cv2
import json
import threading


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
        send_message(socket, "video_frame", data)
        response = recv_message(socket, 32)
        response = json.loads(response)
        response = response["payload"]
        if response != "OK":
            raise Exception("Wrong response received. Closing connection.\n")
    


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
cam_thread.join()
