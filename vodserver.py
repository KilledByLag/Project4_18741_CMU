import socket as st
import sys
import threading
import re
import os
from datetime import datetime, timezone
import time

BUFSIZE = 5242880  # Adjust this buffer size as needed
CHUNK_SIZE = 5242880

def send_403_error(connection_socket):
    current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    error_page = """
    <html>
        <head>
            <title>403 Forbidden</title>
        </head>
        <body>
            <h1>403 Forbidden</h1>
            <p>You don't have permission to access the requested URL on this server.</p>
        </body>
    </html>
    """

    headers = [
        "HTTP/1.1 403 Forbidden",
        "Connection: Keep-Alive",
        "Content-Length: " + str(len(error_page)),
        "Content-Type: text/html",
        "Date: " + current_date,
    ]

    header_str = "\r\n".join(headers) + "\r\n\r\n"
    connection_socket.send(header_str.encode())
    connection_socket.send(error_page.encode())

def send_404_error(connection_socket):
    current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    error_page = """
    <html>
        <head>
            <title>404 Not Found</title>
        </head>
        <body>
            <h1>404 Not Found</h1>
            <p>The requested URL was not found on this server.</p>
        </body>
    </html>
    """

    headers = [
        "HTTP/1.1 404 Not Found",
        "Connection: Keep-Alive",
        "Content-Length: " + str(len(error_page)),
        "Content-Type: text/html",
        "Date: " + current_date,
    ]

    header_str = "\r\n".join(headers) + "\r\n\r\n"
    connection_socket.send(header_str.encode())
    connection_socket.send(error_page.encode())



def send_data(connection_socket):
    while True:
        msg_string = connection_socket.recv(BUFSIZE).decode()
        if not msg_string:
            break  # Break the loop if there is no more data

        print(msg_string)

        range_header = re.search(r'Range:\s+bytes=(\d+)-(\d+)?', msg_string)

        if range_header:
            start_byte = int(range_header.group(1))
            end_byte = int(range_header.group(2)) if range_header.group(2) else None
        else:
            start_byte = 0
            end_byte = None

        connection_header = re.search(r'Connection:\s*(\S+)', msg_string)
        connection_keep_alive = connection_header.group(1).lower() == 'keep-alive' if connection_header else False
        pattern = re.compile(r'GET\s+\/(\S+)', re.IGNORECASE)
        match = pattern.search(msg_string)
        full_path = match.group(1)
        filename = os.path.basename(full_path)

        path_1 = rf"content/{full_path}"
        # path_2 = rf"content\confidential\{filename}"

        if not os.path.exists(path_1):
            send_404_error(connection_socket)
            return

        if "confidential" in path_1:
            send_403_error(connection_socket)
            # print("Content is confidential")
            return

        with open(path_1, 'rb') as file:
            size = os.path.getsize(path_1)

            current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            last_modified_timestamp = os.path.getmtime(path_1)
            last_modified_date = datetime.utcfromtimestamp(last_modified_timestamp).strftime(
                '%a, %d %b %Y %H:%M:%S GMT')

            types = ["text/plain", "text/css", "text/html", "image/gif", "image/jpeg", "image/png", "video/mp4",
                     "video/webm", "application/javascript", "application/octet-stream"]
            file_extension = os.path.splitext(filename)[1]
            type_of_file = types[-1]  # Default to binary/octet-stream

            if file_extension in {".txt", ".css", ".htm", ".html", ".js"}:
                type_of_file = types[types.index("text/plain")]

            if file_extension == ".gif":
                type_of_file = types[types.index("image/gif")]

            if file_extension in {".jpg", ".jpeg", ".png"}:
                type_of_file = types[types.index("image/jpeg")]

            if file_extension == ".mp4":
                type_of_file = types[types.index("video/mp4")]

            if file_extension in {".webm", ".ogg"}:
                type_of_file = types[types.index("video/webm")]

            if size > CHUNK_SIZE:
                # while start_byte < size:
                    end_byte = min(start_byte + CHUNK_SIZE, size)

                    headers = [
                        "HTTP/1.1 206 Partial Content",
                        f"Connection: {'keep-alive' if connection_keep_alive else 'close'}",
                        "Accept-Ranges: bytes",
                        f"Content-Length: {end_byte - start_byte}",
                        f"Content-Type: {type_of_file}",
                        f"Date: {current_date}",
                        f"Last-Modified: {last_modified_date}",
                        f"Content-Range: bytes {start_byte}-{end_byte}/{size}"
                    ]

                    header_str = "\r\n".join(headers) + "\r\n\r\n"
                    connection_socket.send(header_str.encode())
                    # print(f"headers of big file block {headers}")
                    # print("Sent Headers")
                    file.seek(start_byte)
                    response = file.read(CHUNK_SIZE)
                    connection_socket.send(response)

                    # start_byte += CHUNK_SIZE
            else:
                headers = [
                    "HTTP/1.1 200 OK",
                    f"Connection: {'keep-alive' if connection_keep_alive else 'close'}",
                    "Accept-Ranges: bytes",
                    f"Content-Length: {size}",
                    f"Content-Type: {type_of_file}",
                    f"Date: {current_date}",
                    f"Last-Modified: {last_modified_date}",
                ]
                # print(headers)
                header_str = "\r\n".join(headers) + "\r\n\r\n"
                connection_socket.send(header_str.encode())
                # print("sent headers")
                response = file.read(BUFSIZE)
                while response:
                    connection_socket.send(response)
                    response = file.read(BUFSIZE)

        if not connection_keep_alive:
            break  # Break the loop if the connection is not keep-alive



def listen_for_connections(server):
    # print("listening for connections")
    server.listen(1000)
    try:
        while True:

            connection_socket,client_addr = server.accept()
            send_thread = threading.Thread(target=send_data,args=(connection_socket,))
            send_thread.start()
            
    except Exception as e:
        pass
        # print(f"Error Handling : {e}")

def run_server(port_num):
    HOST = 'localhost'
    PORT = int(port_num)
    s = st.socket(st.AF_INET,st.SOCK_STREAM)
    s.bind((HOST, PORT))
    return s

if __name__ == '__main__':
    if len(sys.argv) == 2:
        port_num = sys.argv[1]
        # print(port_num)
        server = run_server(port_num)
        listen_for_connections(server)