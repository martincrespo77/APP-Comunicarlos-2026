import pytest
from httpx import AsyncClient

# Marca todos los tests en este archivo para correr asíncronamente
pytestmark = pytest.mark.asyncio

async def test_create_user(async_client: AsyncClient, clean_db, db_client):
    payload = {
        "name": "Juan Perez",
        "email": "juan@example.com",
        "role": "admin"
    }
    
    # Simula la petición POST que Bruno enviaría
    response = await async_client.post("/users/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Juan Perez"
    assert data["email"] == "juan@example.com"
    assert "id" in data
    assert "created_at" in data

async def test_get_users(async_client: AsyncClient, clean_db, db_client):
    # Primero creamos un usuario
    await async_client.post("/users/", json={
        "name": "Maria Lopez",
        "email": "maria@example.com"
    })
    
    # Luego verificamos que podemos listarlo
    response = await async_client.get("/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Maria Lopez"
