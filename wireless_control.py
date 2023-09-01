import pystray
from PIL import Image
import threading
import socket
import sys
import json
import pyautogui
import os
import signal

import qrcode

pyautogui.FAILSAFE = False

# Constants for server configuration
SERVER_PORT = 5555

# Flag to control the server loop
server_running = False

# Server thread
server_thread = None
server_socket = None


# Function to get the local IP address
def get_local_ip():
    try:
        # Create a socket object and connect to an external server (e.g., Google DNS)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except socket.error:
        return "127.0.0.1"  # Default to loopback address if there's an error

# Function to start the server
def start_server(icon, item):
    global server_running, server_thread, server_socket
    if not server_running:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", SERVER_PORT))
        server_socket.listen(1)
        local_ip = get_local_ip()
        
        # Create a QR code with the server address
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"tcp://{local_ip}:{SERVER_PORT}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        print(f"Server is listening on {local_ip}:{SERVER_PORT}")

        server_running = True

        # Show the QR code
        qr_img.show()

        server_thread = threading.Thread(target=server_loop)
        server_thread.start()
    

# Server loop
def server_loop():
    global server_socket
    while server_running:
        if not server_running:
            # If the server is not running, close the server socket and exit the loop
            server_socket.close()
            sys.exit()
            return

        # Accept incoming connections
        connection, address = server_socket.accept()
        print(f"Connected by {address}")
        while server_running:
            data = connection.recv(1024)
            if not data:
                continue

            received_data = data.decode()

            try:
                mouse_event = json.loads(received_data)
                button = mouse_event['click']

                # Check for a click event
                if 'click' in mouse_event and (mouse_event['click'] != None):
                    button = mouse_event['click']

                    if button == 'left':
                        pyautogui.click()
                    elif button == 'right':
                        pyautogui.rightClick()

                # Check for a move event
                elif 'dx' in mouse_event and 'dy' in mouse_event:
                    dx = mouse_event['dx'] * 0.5
                    dy = mouse_event['dy'] * 0.5
                    pyautogui.move(dx, dy)

                # Check for a text input event
                if 'text' in mouse_event:
                    text_to_type = mouse_event['text']
                    if text_to_type == "BACKSPACE":
                        current_x, current_y = pyautogui.position()
                        pyautogui.click(current_x, current_y)
                        pyautogui.press("space")
                    elif text_to_type:
                        current_x, current_y = pyautogui.position()
                        pyautogui.click(current_x, current_y)
                        pyautogui.typewrite(text_to_type, interval=0.1)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

# Function to stop the server
def stop_server():
    global server_running, server_socket
    if server_running:
        server_running = False
        server_socket.close()

# Function to quit the application
def quit_app(icon, item):
    stop_server()
    icon.stop()
    try:
        os.kill(os.getpid(), signal.SIGTERM)
        os.kill('24788', signal.SIGTERM)
        sys.exit()
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Create the tray menu
def create_tray_menu():
    menu = (
        pystray.MenuItem('Start Server', start_server),
        pystray.MenuItem('Stop Server', stop_server),
        pystray.MenuItem('Quit', quit_app)
    )

    # Get the path to the directory where the script or executable is located
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        # current_dir = sys._MEIPASS
        try:
            current_dir = sys._MEIPASS
        except Exception:
            current_dir = os.path.abspath(".")
    else:
        # Running as a script
        current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to 'logo.png'
    logo_path = os.path.join(current_dir, 'logo.png')

    # Check if the logo image file exists
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Could not find 'logo.png' at path: {logo_path}")

    # Use a default icon
    default_icon = Image.open(logo_path)

    # Create the system tray icon
    icon = pystray.Icon("name", default_icon, menu=menu)

    icon.run()

# Main function
if __name__ == "__main__":
    create_tray_menu()
