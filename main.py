from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import logging, json, sys, os

sys.path.append("..")

from utils.rag_utils import *

from utils.azure_utils import *

from utils.blob_utils import *

app = FastAPI()

origins = [

    "https://lightbend.get-starlight.com/",
    "http://localhost:3000"
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

# containers = ["training", "raw", "training-raw"]

containers = ["train-2025-only", "training"]

vs_dict = prep_vs(containers)

history = []

@app.get("/api")
async def read_item():
    return {"message": f"Update: Lowered threshold score to .68 , switched out GPT model with one that has 120k token limit and set max_words to 1000 again - changed"}

@app.post("/api/query")
async def query(userMessage: UserMessage):
    
    print(userMessage)
    
    global history
    
    responses, history = gen_resp(search_query = userMessage.message, vs_dict = vs_dict,
                                        history = history, k = 3)

    update_logs_txt(userMessage.uuid, "query", userMessage.message, responses[0]["answer"])

    update_logs_csv(userMessage.uuid, "query", userMessage.message, responses[0]["answer"])

    return responses

@app.post("/api/clear")
async def clear(userMessage: UserMessage):
    global history

    history = []

    update_logs_txt(userMessage.uuid, "clear", userMessage.message, "answer")

    return {"message": "History cleared"}
