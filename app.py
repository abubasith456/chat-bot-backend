from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import threading
from server.socket_server import ChatbotServer

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chatbot API", description="A FastAPI-based chatbot service", version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot server
chatbot_server = ChatbotServer()
socket_server_thread = None


class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    user_id: Optional[str] = None


class SocketServerResponse(BaseModel):
    status: str
    message: str
    host: str
    port: int


@app.get("/")
async def root():
    return {"message": "Chatbot API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        # Use LLM client directly for API calls
        response = chatbot_server.llm_client.generate_response(chat_message.message)
        if response is None:
            response = "I'm sorry, I couldn't generate a response at this time."
        return ChatResponse(response=response, user_id=chat_message.user_id)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/socket/start", response_model=SocketServerResponse)
async def start_socket_server():
    """Start the socket server in a separate thread"""
    global socket_server_thread

    try:
        if socket_server_thread and socket_server_thread.is_alive():
            return SocketServerResponse(
                status="already_running",
                message="Socket server is already running",
                host=chatbot_server.host,
                port=chatbot_server.port,
            )

        # Start socket server in a separate thread
        socket_server_thread = threading.Thread(target=chatbot_server.start_server)
        socket_server_thread.daemon = True
        socket_server_thread.start()

        logger.info(
            f"Socket server started on {chatbot_server.host}:{chatbot_server.port}"
        )

        return SocketServerResponse(
            status="started",
            message="Socket server started successfully",
            host=chatbot_server.host,
            port=chatbot_server.port,
        )

    except Exception as e:
        logger.error(f"Error starting socket server: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start socket server: {str(e)}"
        )


@app.post("/socket/stop")
async def stop_socket_server():
    """Stop the socket server"""
    try:
        if not chatbot_server.running:
            return {"status": "not_running", "message": "Socket server is not running"}

        chatbot_server.shutdown_server()
        logger.info("Socket server stopped")

        return {"status": "stopped", "message": "Socket server stopped successfully"}

    except Exception as e:
        logger.error(f"Error stopping socket server: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop socket server: {str(e)}"
        )


@app.get("/socket/status")
async def get_socket_server_status():
    """Get the current status of the socket server"""
    return {
        "running": chatbot_server.running,
        "host": chatbot_server.host,
        "port": chatbot_server.port,
        "active_clients": len(chatbot_server.clients),
    }


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown socket server when FastAPI shuts down
    if chatbot_server.running:
        chatbot_server.shutdown_server()
    logger.info("FastAPI application shutdown")
