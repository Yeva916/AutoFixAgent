from fastapi import FastAPI,Query,HTTPException,Path
from fastapi.routing import APIRoute
from app.api.main import api_router

app = FastAPI()

@app.get("/")
def hello():
    return {"message":"the server is up and running"}

app.include_router(api_router)