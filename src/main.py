from webbrowser import get
from fastapi import FastAPI
from pymongo import MongoClient
from contextlib import asynccontextmanager
from current_router import router

from config import HOSTNAME, PORT, DATABASE
from fastapi.middleware.cors import CORSMiddleware
from routes.analysis import router as analysis_router
from routes.data import router as data_router


@asynccontextmanager
async def get_db(app: FastAPI):
    app.client = MongoClient(HOSTNAME, PORT)
    app.db = app.client[DATABASE]
    print("Connected to the database")
    yield
    app.client.close()


app = FastAPI(lifespan=get_db)

origins = [
    "http://localhost:3000",  # React app
    # add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router, tags=["data"], prefix="/data")
app.include_router(analysis_router, tags=["analysis"], prefix="/analysis")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
