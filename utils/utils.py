from datetime import datetime

import pytz, sys, re, os

sys.path.append("..")

from dotenv import load_dotenv

from openai import AzureOpenAI

load_dotenv()

import numpy as np

edt = pytz.timezone('America/New_York')

emb_client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_KEY"),
    api_version = "2023-05-15",
    azure_endpoint = os.getenv("AZURE_OPENAI_EMB_ENDPOINT")
)

import numpy as np
def cosine_similarity(vector, matrix):
    dot_product = np.dot(matrix, vector)
    matrix_norms = np.linalg.norm(matrix)
    vector_norm = np.linalg.norm(vector)
    similarities = dot_product / (matrix_norms * vector_norm)
    return round(similarities, 2)

# Step 3: Query the retriever and generate an answer

def summarize_content(content, max_words=1000):
    # Summarize content to stay within the word limit
    words = content.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return content

def embed_query(query):
    emd = emb_client.embeddings.create(
        input = query,
        model = "text-embedding-ada-002"
    )

    return emd.data[0].embedding

def is_specific_query(query):
    # Define a list of common greetings or general questions
    general_patterns = [
        r"\bhi\b", r"\bhello\b", r"\bhow are you\b", r"\bwhat's up\b"
    ]
    
    for pattern in general_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    return True

def get_time_txt():
    now = datetime.now(edt)

    formatted_date = now.strftime('%d %B %Y %I:%M %p').lstrip('0').replace(' 0', ' ')

    return formatted_date

def get_time_csv():
    now = datetime.now(edt)

    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    
    return formatted_date

def format_rag_resp(res_json):
    try:    

        answer = re.sub(r'\[doc\d+\]', '', res_json['reply'])

        src_dict = {}
        
        for doc in res_json['documents']:
            try:
                src_dict[doc['url']] += doc['score']
            except:
                src_dict[doc['url']] = doc['score']

        src_dict = {
            k.replace(".pdf", ""): round(v,2) 
            for k, v in sorted(src_dict.items(), 
            key=lambda item: item[1], 
            reverse=True)}
        
        srcs = []
        
        for k, v in src_dict.items():
            srcs.append(
                {
                    "source": k,
                    "score": v
                }
            )
        
        return answer, srcs
    except Exception as error:
        
        answer = error.read().decode("utf8", 'ignore')
        
        print("The request failed with status code: " + str(error.code))
        
        print(error.info())
        
        print(error.read().decode("utf8", 'ignore')) 

        return answer, []