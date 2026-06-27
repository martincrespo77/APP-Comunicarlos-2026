from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List

from app.database import init_db
from app.models import User, Message
from app.schemas import UserCreate, UserResponse, MessageCreate, MessageResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa la conexión a MongoDB al arrancar
    await init_db()
    yield

app = FastAPI(title="Comunicarlos API", lifespan=lifespan)

# Habilitar CORS para permitir que el frontend de AdminLTE se comunique
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir todos para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Comunicarlos"}

# --- Endpoints de Users ---

@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user_in: UserCreate):
    # Se crea la instancia de Beanie a partir del DTO Pydantic
    user = User(**user_in.model_dump())
    await user.insert()
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at
    )

@app.get("/users/", response_model=List[UserResponse])
async def get_users():
    users = await User.find_all().to_list()
    return [
        UserResponse(
            id=str(u.id),
            name=u.name,
            email=u.email,
            role=u.role,
            created_at=u.created_at
        ) for u in users
    ]

# --- Endpoints de Messages ---

@app.post("/messages/", response_model=MessageResponse, status_code=201)
async def create_message(msg_in: MessageCreate):
    msg = Message(**msg_in.model_dump())
    await msg.insert()
    return MessageResponse(
        id=str(msg.id),
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        created_at=msg.created_at,
        read=msg.read
    )

@app.get("/messages/", response_model=List[MessageResponse])
async def get_messages():
    messages = await Message.find_all().to_list()
    return [
        MessageResponse(
            id=str(m.id),
            sender_id=m.sender_id,
            receiver_id=m.receiver_id,
            content=m.content,
            created_at=m.created_at,
            read=m.read
        ) for m in messages
    ]
