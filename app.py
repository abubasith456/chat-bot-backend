from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal
import logging, json
from core.connection_manager import manager, ResponseData
from llm import NvidiaLLMClient, nvidia_service

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


class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    user_id: Optional[str] = None


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
        response = nvidia_service.generate_response(chat_message.message)
        if response is None:
            response = "I'm sorry, I couldn't generate a response at this time."
        return ChatResponse(response=response, user_id=chat_message.user_id)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class WSMessageReceive(BaseModel):
    type: Literal["model", "message", "translate", "languages"]
    text: str
    text_from: Optional[str] = None
    text_to: Optional[str] = None


@app.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await manager.connect(ws)

    await manager.send_message(
        ws,
        ResponseData(
            type="response",
            message="Welcome to the chatbot! Type your message to start chatting.",
        ),
    )

    try:
        while True:
            text = await ws.receive_text()
            logger.info(f"Received WS: {text}")
            wb_message = WSMessageReceive(**json.loads(text))

            if wb_message.type == "model":
                manager.state.model_name = wb_message.text
                nvidia_service.model_name = wb_message.text
            elif wb_message.type == "message":
                if wb_message.text.lower() in ["quit", "bye"]:
                    await manager.send_message(
                        ws,
                        ResponseData(
                            type="response", message="Goodbye! Thanks for chatting."
                        ),
                    )
                    break
                logger.info(f"Received message: {wb_message.text}")
                response = await nvidia_service.async_generate_response(wb_message.text)
                if response is None:
                    response = "I'm sorry, I couldn't generate a response at this time."
                logger.info(f"Bot response: {response}")
                await manager.send_personal(
                    ws,
                    ResponseData(type="response", message=response).model_dump_json(),
                )
            elif wb_message.type == "languages":

                print("Languages response: ", wb_message.model_dump_json())

                if wb_message.text_from:
                    nvidia_service.text_from = wb_message.text_from

                if wb_message.text_to:
                    nvidia_service.text_to = wb_message.text_to

            elif wb_message.type == "translate":
                translated_text = await nvidia_service.translate_text(
                    wb_message.text, nvidia_service.text_from, nvidia_service.text_to
                )
                await manager.send_personal(
                    ws,
                    ResponseData(
                        type="response", message=translated_text
                    ).model_dump_json(),
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        await manager.send_message(
            ws, ResponseData(type="error", message=f"An error occurred: {str(e)}")
        )
    finally:
        manager.disconnect(ws)


@app.get("/languages")
async def get_languages():
    """Get supported languages for translation"""
    languages = await nvidia_service.get_languages()

    if languages == {}:
        raise HTTPException(status_code=400, detail="Failed to retrieve languages")

    logger.info(f"Supported languages: {languages}")

    return languages


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown socket server when FastAPI shuts down
    logger.info("FastAPI application shutdown")
