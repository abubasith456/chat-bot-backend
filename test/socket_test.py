import socket
import json
import time


def test_socket():
    """Simple socket connection test"""
    HOST = "localhost"
    PORT = 8888

    print(f"Testing socket connection to {HOST}:{PORT}")

    try:
        # Connect to socket server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("✅ Connected successfully!")

        # Receive welcome message
        welcome = sock.recv(1024).decode("utf-8")
        print(f"📨 {json.loads(welcome.strip())['message']}")

        # Send test message
        test_msg = {"message": "Hello, bot!"}
        sock.send(json.dumps(test_msg).encode("utf-8"))
        print("📤 Sent: Hello, bot!")

        # Receive response
        response = sock.recv(1024).decode("utf-8")
        bot_reply = json.loads(response.strip())
        print(f"📥 Bot: {bot_reply['message']}")

        # Send quit message
        quit_msg = {"message": "quit"}
        sock.send(json.dumps(quit_msg).encode("utf-8"))
        print("📤 Sent: quit")

        # Receive goodbye
        goodbye = sock.recv(1024).decode("utf-8")
        print(f"📨 {json.loads(goodbye.strip())['message']}")

        sock.close()
        print("✅ Test completed successfully!")

    except ConnectionRefusedError:
        print("❌ Connection refused. Start socket server first:")
        print("   curl -X POST http://localhost:8000/socket/start")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_socket()
