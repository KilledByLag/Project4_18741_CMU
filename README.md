# HTTP Content Server - Project 2 (Computer Networks)

## 18741 - Computer Networks  
**Project - 2: HTTP Content Server**  
**Author**: Premsai Peddi, CMU Alum (2024)  

---

## Description
This project implements a **multi-threaded HTTP Content Server** that can serve static files to HTTP clients. It supports essential HTTP features like:
- **GET Requests** to retrieve files.
- **HTTP Partial Content** for serving large files using the `Range` header.
- **Connection Persistence** with "keep-alive" support.
- **Error Handling**: 404 (Not Found) and 403 (Forbidden).

The server reads files from a **content directory**. Access to certain paths (e.g., "confidential") is restricted with a **403 Forbidden** error. Files larger than a specified buffer size are sent in chunks for efficient streaming.

---

## Features
- **Multi-threaded Architecture**: Handles multiple clients concurrently.
- **Static File Serving**: Serves files with appropriate MIME types:
  - Text, HTML, CSS, JavaScript
  - Images (JPEG, PNG, GIF)
  - Videos (MP4, WebM)
  - Binary/Other files
- **HTTP Partial Content Support**: Implements `Range` headers for streaming large files in chunks.
- **Connection Persistence**: Supports HTTP "keep-alive" connections for improved efficiency.
- **Error Responses**:
  - **404 Not Found**: When the requested file does not exist.
  - **403 Forbidden**: When accessing restricted directories like `confidential/`.

---

## Requirements
- **Python Version**: 3.9 or above
- **Libraries**: Built-in libraries only
  - `socket`, `threading`, `sys`, `re`, `os`, `datetime`
- **Directory Structure**:
    ```
    project_root/
        ├── content/              # Directory to serve files
        │   ├── example.txt       # Example file
        │   ├── example.jpg       # Example image
        │   └── confidential/     # Restricted directory
        ├── content_server.py     # The HTTP server script
        └── README.md             # This README file
    ```

---

## Usage
### Starting the Server
Run the server using the following command:
```bash
python3 content_server.py <port_number>
```
**Example**:
```bash
python3 content_server.py 8080
```

### Client Requests
The server listens for HTTP GET requests. You can use tools like a web browser, `curl`, or Postman to interact with the server.

**Examples**:
1. **Request a File**:
   ```bash
   GET /example.txt HTTP/1.1
   Host: localhost:8080
   ```
   
2. **Request Partial Content** (Streaming):
   ```bash
   GET /example.mp4 HTTP/1.1
   Host: localhost:8080
   Range: bytes=0-5242879
   ```

3. **Forbidden Request**:
   Accessing files in the `confidential/` folder will return a `403 Forbidden` response.

---

## Outputs
1. **Client-Side**:
   - HTTP responses with headers and file content.
   - 403 or 404 errors when applicable.

2. **Server-Side Console**:
   - Logs incoming HTTP requests for debugging.

---

## Example Directory Setup
To serve files correctly, the server expects a `content` directory as follows:
```
content/
    ├── index.html
    ├── image.jpg
    ├── video.mp4
    ├── confidential/
    │   └── secret.txt  # Access restricted
```

---

## Notes
- Make sure to create a `content` folder in the project root and populate it with files you want to serve.
- Restricted files must be placed in the `confidential/` directory.

---

## Known Limitations
- Only HTTP GET requests are supported.
- Basic error handling for 403 and 404 errors.

---

## Author
**Premsai Peddi**  
CMU Alum (2024)  

---

## ⚠️ Warning
**DO NOT PLAGIARIZE!**  
This implementation includes unique configurations and optimizations. Copying without understanding may result in failure in automated grading systems (e.g., Gradescope).

---

## License
This project is for educational purposes only. Unauthorized copying or distribution is prohibited.

