# import pandas as pd
from io import BytesIO

import os, sys

sys.path.append("..")

from dotenv import load_dotenv

load_dotenv()

from azure.storage.blob import BlobServiceClient

# from utils.utils import get_time_csv, get_time_txt

def prep_client(container, blob):
    conn_string = os.getenv('AZURE_BS_URL')

    blob_service_client = BlobServiceClient.from_connection_string(conn_string)

    blob_client = blob_service_client.get_blob_client(container=container, blob=blob)

    return blob_client

def update_logs_txt(uuid, function_call, message, answer):

    if function_call == "clear":
        
        log_entry = f"""[LOG ENTRY {get_time_txt()}]: User {uuid} cleared memory"""
    
    else:   
        log_entry = f"""[LOG ENTRY {get_time_txt()}]: User {uuid} asked a question:\nMessage: {message}\nAnswer: {answer}""" 
      
    blob_client = prep_client(container="lightbend-logs", blob="rag-logs.txt")
    
    content = blob_client.download_blob().readall().decode('utf-8').strip()

    content = f"""
            {content}

            {log_entry}

            {'--'*100}\n
            """

    blob_client.upload_blob(content, overwrite=True)

def update_logs_csv(uuid, function_call, message, answer):
     
    blob_client = prep_client(container="lightbend-logs", blob="rag-logs.csv")
    
    stream = blob_client.download_blob()  
    with BytesIO() as buf:
        stream.readinto(buf)

        # needed to reset the buffer, otherwise, panda won't read from the start
        buf.seek(0)

        data = pd.read_csv(buf)

    logs_dict = data.to_dict(orient='records')

    logs_dict.append(
        {
            "time": get_time_csv(),
            "uuid": uuid,
            "function": function_call,
            "message": message,
            "answer": answer,
            "time-str": get_time_txt()
        }
    )

    df = pd.DataFrame(logs_dict)

    df['time'] = pd.to_datetime(df['time'])

    output = df.to_csv(index=False, encoding="utf-8")

    blob_client.upload_blob(output, blob_type="BlockBlob", overwrite=True)