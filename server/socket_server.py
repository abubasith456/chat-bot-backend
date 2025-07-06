import socket
import threading
import json
import logging
from typing import Dict, Any, Optional
from llm import NvidiaLLMClient
from config import settings

logger = logging.getLogger(__name__)


class ChatbotServer:
    def __init__(self):
        self.host = settings.HOST
        self.port = settings.PORT
        self.clients = {}
        self.llm_client = NvidiaLLMClient()
        self.server_socket = None
        self.running = False

    def start_server(self):
        """Start the socket server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            logger.info(f"Chatbot server started on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    logger.info(f"New connection from {address}")

                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except OSError:
                    if self.running:
                        logger.error("Error accepting connections")
                    break

        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.shutdown_server()

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual client connections"""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = client_socket

        try:
            # Send welcome message
            welcome_msg = {
                "type": "system",
                "message": "Welcome to the chatbot! Type your message to start chatting.",
            }
            self.send_message(client_socket, welcome_msg)

            while self.running:
                try:
                    data = client_socket.recv(1024).decode("utf-8")
                    if not data:
                        break

                    # Parse client message
                    try:
                        client_message = json.loads(data)
                        user_input = client_message.get("message", "").strip()

                        if user_input.lower() in ["quit", "exit", "bye"]:
                            goodbye_msg = {
                                "type": "system",
                                "message": "Goodbye! Thanks for chatting.",
                            }
                            self.send_message(client_socket, goodbye_msg)
                            break

                        if user_input:
                            logger.info(f"Received from {client_id}: {user_input}")

                            # Generate response using LLM
                            bot_response = self.llm_client.generate_response(user_input)

                            response_msg = {"type": "bot", "message": bot_response}
                            self.send_message(client_socket, response_msg)

                    except json.JSONDecodeError:
                        error_msg = {
                            "type": "error",
                            "message": "Invalid message format. Please send valid JSON.",
                        }
                        self.send_message(client_socket, error_msg)

                except ConnectionResetError:
                    logger.info(f"Client {client_id} disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {client_id}: {e}")
                    break

        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
            logger.info(f"Client {client_id} connection closed")

    def send_message(self, client_socket: socket.socket, message: Dict[str, Any]):
        """Send JSON message to client"""
        try:
            json_message = json.dumps(message) + "\n"
            client_socket.send(json_message.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def process_message_direct(self, message: str, user_id: Optional[str] = None) -> str:
        """Process a message directly without socket connection (for API use)"""
        try:
            response = self.llm_client.generate_response(message)
            logger.info(f"Direct message processed for user {user_id}: {message}")
            return response if response is not None else "I'm sorry, I couldn't generate a response."
        except Exception as e:
            logger.error(f"Error processing direct message: {e}")
            return "I'm sorry, I encountered an error processing your message."

    def shutdown_server(self):
        """Shutdown the server gracefully"""
        logger.info("Shutting down server...")
        self.running = False

        # Close all client connections
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        logger.info("Server shutdown complete")
