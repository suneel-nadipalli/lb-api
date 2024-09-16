import pandas as pd
from io import BytesIO
import os, sys

sys.path.append("..")

from utils.rag_utils import *

from utils.utils import *

from utils.azure_utils import *

from dotenv import load_dotenv

load_dotenv()

from azure.storage.blob import BlobServiceClient

containers = ["training", "raw", "training-raw"]

vs_dict = prep_vs(containers)

def prep_client(blob):
    conn_string = os.getenv('AZURE_BS_URL')

    blob_service_client = BlobServiceClient.from_connection_string(conn_string)

    blob_client = blob_service_client.get_blob_client(container="lightbend-logs", blob=blob)

    return blob_client

def prep_questions():
    file = "../eval/questions.txt"

    with open(file) as file:
        lines = [line.rstrip() for line in file]

    return lines

def log_answers():

    questions = prep_questions()

    records = []

    history = []

    for question in questions:
            
        try:
            
            responses, history = gen_resp(search_query = question, vs_dict = vs_dict,
                                            history = history, k = 3)

            for response in responses:

                records.append({
                    "question": question,
                    "answer": response["answer"],
                    "source": response["vs"]
                })
        except:
            pass
    
    df = pd.DataFrame(records)

    output = df.to_csv("../eval/answers.csv", index=False, encoding="utf-8")

    blob_client = prep_client(blob="answers.csv")

    blob_client.upload_blob(output, blob_type="BlockBlob", overwrite=True)
            
log_answers()