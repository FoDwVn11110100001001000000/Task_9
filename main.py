from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from mimetypes import guess_type
from pathlib import Path
import socket
from threading import Thread
from datetime import datetime
import json


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        else:
            if Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def send_static(self):
        self.send_response(200)
        mt = guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self) -> dict:
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.write_to_json(data)
        self.send_data_to_socket(data.decode())
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_data_to_socket(self, message):
        host = socket.gethostname()
        port = 5000

        client_socket = socket.socket()
        client_socket.connect((host, port))

        while message.lower():
            client_socket.send(message.encode())
            data = client_socket.recv(1024).decode()
            print(f'Received message: {data}')

        client_socket.close()
    
    def write_to_json(self, data_qs):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        parse = parse_qs(data_qs)
        parsed_data = {key.decode(): value[0].decode() for key, value in parse.items()}
        username = parsed_data.get('username')
        message = parsed_data.get('message')

        entry = {
        "username": username,
        "message": message
        }

        with open('storage/data.json', 'a') as json_file:
            json.dump({current_datetime: entry}, json_file, indent=4)


def server_socket():
    print('Server socket start listening')
    server_socket = socket.socket()
    server_socket.bind((socket.gethostname(), 5000))
    server_socket.listen(2)
    conn, address = server_socket.accept()
    print(f'Connection from {address}')
    while True:
        data = conn.recv(100).decode()

        if not data:
            break
        print(f'Received message: {data}')
    conn.close()

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        print('Server is running')
        socket_server = Thread(target=server_socket)
        socket_server.start()
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run()