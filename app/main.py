from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.db.database import init_db

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow requests from Angular app
origins = [
    "http://localhost:4200",  # Angular dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # origins allowed to access
    allow_credentials=True,
    allow_methods=["*"],              # allow all HTTP methods
    allow_headers=["*"],              # allow all headers
)

app.include_router(router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


