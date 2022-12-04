"""FastAPI web server for hosting the bot."""

from fastapi import FastAPI
from bot import start_bot

app = FastAPI()

start_bot()


@app.get("/")
def read_root():
    return {"Hello": "World"}
