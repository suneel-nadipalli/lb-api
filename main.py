from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import logging, json, sys, os

sys.path.append("..")

from utils.rag_utils import *

from utils.utils import *

from utils.azure_utils import *

from utils.blob_utils import update_logs_txt, update_logs_csv

app = FastAPI()

origins = [

    "https://lightbend.get-starlight.com/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Item(BaseModel):
    name: str
    price: float

class UserMessage(BaseModel):
    message: str
    uuid: str

vs = prep_vs()

history = []

@app.get("/")
async def read_item():
    return {"message": f"Update: We back from break!"}

@app.post("/query")
async def query(userMessage: UserMessage):
    print(userMessage)
    global history

    answer, srcs, history = gen_resp(search_query = userMessage.message, vector_store = vs,
                                        history = history, k = 3)
            
    response = {
        "answer": answer,
        "sources": srcs
    }

    update_logs_txt(userMessage.uuid, "query", userMessage.message, answer)

    # update_logs_csv(userMessage.uuid, "query", userMessage.message, answer)

    return response

@app.post("/clear")
async def clear():
    global history

    history = []

    # update_logs_txt(, "clear", userMessage.message, answer)

    return {"message": "History cleared"}
