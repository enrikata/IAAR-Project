import json
import socket


def recv_message(socket: socket.socket, chunk_length: int) -> dict:
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


def send_message(socket: socket.socket, type: str, payload: str) -> dict:

    packet = {
        "type" : type,
        "payload" : payload
    }

    json_packet = bytes(json.dumps(packet), 'utf-8')
    socket.send(json_packet)
    return packet