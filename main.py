from fastapi import FastAPI
from pydantic import BaseModel

import sys

sys.path.append('..')

from utils.utils import *

class Item(BaseModel):
    name: str
    price: float


app = FastAPI()


@app.get("/")
async def read_item():
    return {"message": f"Welcome to our app again! {get_env()}"}


@app.get("/hello/{name}")
async def read_item(name):
    return {"message": f"Hello {name}, how are you?"}


@app.post("/items/")
async def create_item(item: Item):
    return {"message": f"{item.name} is priced at £{item.price}"}