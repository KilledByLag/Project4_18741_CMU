import socket as st
import sys
import threading
import re
import os
from datetime import datetime, timezone


"""
--------------------------------------------------------------------------------------------------
18741 - Computer Networks  
Project - 2: HTTP Content Server  
Author: Premsai Peddi, CMU Alum (2024)  

Description:  
This project implements a multi-threaded HTTP Content Server capable of handling client requests  
for static files, including large files served using HTTP partial content ranges. The server supports:  
- HTTP GET requests  
- 404 (Not Found) and 403 (Forbidden) error handling  
- Range-based partial content delivery (useful for streaming large files)  
- Connection persistence with "keep-alive"  

The server serves files stored in a "content" directory. Files in restricted paths (e.g., "confidential")  
are blocked with a 403 Forbidden error. Large files are sent in chunks using the `Range` header,  
allowing partial content delivery for efficient transport of large media files.

--------------------------------------------------------------------------------------------------
Requirements:  
- Libraries: socket, threading, sys, re, os, datetime  
- Python Version: Python 3.9 or above  
- Directory Structure:  
    - Ensure a "content" directory exists in the same path as the server script.  
    - Place all files to be served in the "content" directory.  

Usage:  
1. Run the server from CLI:  
   `python3 content_server.py <port_number>`  
   Example: `python3 content_server.py 8080`  

2. Client Request Example:  
   - Requesting a file: 'localhost:18741/video.mp4"'

--------------------------------------------------------------------------------------------------
Features:  
- **Multi-threaded**: Handles multiple client connections concurrently (Can handle > 1000 clients)
- **File Serving**: Serves files with MIME types like text, images, videos, etc.  
- **Error Handling**:  
    - 404 Not Found for missing files.  
    - 403 Forbidden for restricted files or directories.  
- **Range Support**: Implements HTTP partial content responses for efficient file streaming.  
- **Connection Persistence**: Supports "keep-alive" connections for improved performance.  

Outputs:  
- **Client Console**: Responses include appropriate HTTP headers and content.  
- **Server Console**: Displays incoming HTTP requests and processes responses.

--------------------------------------------------------------------------------------------------
Directory Structure Example:  
project_root/  
    ├── content/  
    │   ├── example.txt  
    │   ├── example.jpg  
    │   └── confidential/       # Access to this folder is restricted (403 Forbidden)  
    ├── content_server.py       # This server script  


"""

# Constants for buffer size and chunked file transfer
BUFSIZE = 5242880  # 5 MB buffer size
CHUNK_SIZE = 5242880  # 5 MB chunk size

def send_403_error(connection_socket):
    """
    Sends a 403 Forbidden HTTP error response to the client.
    
    Args:
        connection_socket: The client's connection socket.
    """
    current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    error_page = """
    <html>
        <head><title>403 Forbidden</title></head>
        <body>
            <h1>403 Forbidden</h1>
            <p>You don't have permission to access the requested URL on this server.</p>
        </body>
    </html>
    """

    headers = [
        "HTTP/1.1 403 Forbidden",
        "Connection: Keep-Alive",
        f"Content-Length: {len(error_page)}",
        "Content-Type: text/html",
        f"Date: {current_date}",
    ]

    header_str = "\r\n".join(headers) + "\r\n\r\n"
    connection_socket.send(header_str.encode())
    connection_socket.send(error_page.encode())

def send_404_error(connection_socket):
    """
    Sends a 404 Not Found HTTP error response to the client.
    
    Args:
        connection_socket: The client's connection socket.
    """
    current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    error_page = """
    <html>
        <head><title>404 Not Found</title></head>
        <body>
            <h1>404 Not Found</h1>
            <p>The requested URL was not found on this server.</p>
        </body>
    </html>
    """

    headers = [
        "HTTP/1.1 404 Not Found",
        "Connection: Keep-Alive",
        f"Content-Length: {len(error_page)}",
        "Content-Type: text/html",
        f"Date: {current_date}",
    ]

    header_str = "\r\n".join(headers) + "\r\n\r\n"
    connection_socket.send(header_str.encode())
    connection_socket.send(error_page.encode())

def send_data(connection_socket):
    """
    Handles HTTP GET requests, including partial content and chunked transfer.
    
    Args:
        connection_socket: The client's connection socket.
    """
    while True:
        # Receive the client's HTTP request
        msg_string = connection_socket.recv(BUFSIZE).decode()
        if not msg_string:
            break

        print(msg_string)

        # Parse the Range header if present
        range_header = re.search(r'Range:\s+bytes=(\d+)-(\d+)?', msg_string)
        start_byte = int(range_header.group(1)) if range_header else 0
        end_byte = int(range_header.group(2)) if range_header and range_header.group(2) else None

        # Check if connection should stay alive
        connection_header = re.search(r'Connection:\s*(\S+)', msg_string)
        connection_keep_alive = connection_header.group(1).lower() == 'keep-alive' if connection_header else False

        # Extract the requested file path
        pattern = re.compile(r'GET\s+\/(\S+)', re.IGNORECASE)
        match = pattern.search(msg_string)
        full_path = match.group(1)
        filename = os.path.basename(full_path)
        path_1 = rf"content/{full_path}"

        # Handle file existence and access restrictions
        if not os.path.exists(path_1):
            send_404_error(connection_socket)
            return
        if "confidential" in path_1:
            send_403_error(connection_socket)
            return

        # Open and serve the file
        with open(path_1, 'rb') as file:
            size = os.path.getsize(path_1)
            current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            last_modified_timestamp = os.path.getmtime(path_1)
            last_modified_date = datetime.utcfromtimestamp(last_modified_timestamp).strftime('%a, %d %b %Y %H:%M:%S GMT')

            file_extension = os.path.splitext(filename)[1]
            mime_types = {
                ".txt": "text/plain", ".html": "text/html", ".css": "text/css", ".gif": "image/gif",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".mp4": "video/mp4", ".webm": "video/webm", ".js": "application/javascript"
            }
            content_type = mime_types.get(file_extension, "application/octet-stream")

            if size > CHUNK_SIZE:
                end_byte = min(start_byte + CHUNK_SIZE, size)
                headers = [
                    "HTTP/1.1 206 Partial Content",
                    f"Connection: {'keep-alive' if connection_keep_alive else 'close'}",
                    "Accept-Ranges: bytes",
                    f"Content-Length: {end_byte - start_byte}",
                    f"Content-Type: {content_type}",
                    f"Content-Range: bytes {start_byte}-{end_byte}/{size}",
                    f"Date: {current_date}",
                    f"Last-Modified: {last_modified_date}",
                ]
                header_str = "\r\n".join(headers) + "\r\n\r\n"
                connection_socket.send(header_str.encode())
                file.seek(start_byte)
                response = file.read(CHUNK_SIZE)
                connection_socket.send(response)
            else:
                headers = [
                    "HTTP/1.1 200 OK",
                    f"Content-Length: {size}",
                    f"Content-Type: {content_type}",
                    f"Date: {current_date}",
                    f"Last-Modified: {last_modified_date}",
                ]
                connection_socket.send(("\r\n".join(headers) + "\r\n\r\n").encode())
                while (chunk := file.read(BUFSIZE)):
                    connection_socket.send(chunk)

        if not connection_keep_alive:
            break

def listen_for_connections(server):
    """
    Listens for incoming client connections and handles each connection in a separate thread.
    
    Args:
        server: The server socket object.
    """
    server.listen(1000)
    try:
        while True:
            connection_socket, client_addr = server.accept()
            send_thread = threading.Thread(target=send_data, args=(connection_socket,))
            send_thread.start()
    except Exception as e:
        print(f"Error Handling: {e}")

def run_server(port_num):
    """
    Creates and binds a server socket to the specified port.
    
    Args:
        port_num: The port number to bind the server.
    
    Returns:
        The server socket object.
    """
    HOST = 'localhost'
    PORT = int(port_num)
    server_socket = st.socket(st.AF_INET, st.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    return server_socket

if __name__ == '__main__':
    """
    Entry point: Starts the HTTP server on the specified port.
    """
    if len(sys.argv) == 2:
        port_num = sys.argv[1]
        server = run_server(port_num)
        listen_for_connections(server)
