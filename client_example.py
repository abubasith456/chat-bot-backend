import socket
import json
import threading
import sys


class ChatbotClient:
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False

    def connect(self):
        """Connect to the chatbot server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True

            # Start listening for messages
            listen_thread = threading.Thread(target=self.listen_for_messages)
            listen_thread.daemon = True
            listen_thread.start()

            print(f"Connected to chatbot server at {self.host}:{self.port}")
            print("Type your messages (or 'quit' to exit):")

            # Handle user input
            while self.running:
                try:
                    user_input = input("> ")
                    if user_input.strip():
                        self.send_message(user_input)

                        if user_input.lower() in ["quit", "exit", "bye"]:
                            break
                except KeyboardInterrupt:
                    break

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.disconnect()

    def send_message(self, message):
        """Send message to server"""
        try:
            if self.socket is None:
                print("Not connected to server")
                return
            msg = {"message": message}
            json_msg = json.dumps(msg)
            self.socket.send(json_msg.encode("utf-8"))
        except Exception as e:
            print(f"Error sending message: {e}")

    def listen_for_messages(self):
        """Listen for messages from server"""
        buffer = ""
        while self.running:
            try:
                if self.socket is None:
                    break
                data = self.socket.recv(1024).decode("utf-8")
                if not data:
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        try:
                            message = json.loads(line.strip())
                            msg_type = message.get("type", "unknown")
                            content = message.get("message", "")

                            if msg_type == "system":
                                print(f"[SYSTEM] {content}")
                            elif msg_type == "bot":
                                print(f"[BOT] {content}")
                            elif msg_type == "error":
                                print(f"[ERROR] {content}")
                            else:
                                print(f"[{msg_type.upper()}] {content}")

                        except json.JSONDecodeError:
                            print(f"Received invalid JSON: {line}")

            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                break

    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("Disconnected from server")


def main():
    client = ChatbotClient()
    client.connect()


if __name__ == "__main__":
    main()
