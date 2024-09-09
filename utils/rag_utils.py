import os, sys

sys.path.append("..")

from dotenv import load_dotenv

load_dotenv()

import numpy as np

from collections import defaultdict

from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.schema import HumanMessage, AIMessage

from utils.azure_utils import *

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings()

SYSTEM_PROMPT = """You are a helpful AI assistant designed to help users answer questions about
Southbend applications. Your goal is to provide helpful and accurate information to the user
to help them clarify their doubts and fill in their application. Be direct and concise in
your responses. Do not provide any information that is not relevant to the user's query,
or more than what's required. Assume the user's reading level is 8th grade."""

import numpy as np
def cosine_similarity(vector, matrix):
    dot_product = np.dot(matrix, vector)
    matrix_norms = np.linalg.norm(matrix)
    vector_norm = np.linalg.norm(vector)
    similarities = dot_product / (matrix_norms * vector_norm)
    return round(similarities, 2)


# Step 3: Query the retriever and generate an answer

def query_rag_system(vector_store, query, history, k):
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
    
    retrieved_docs = retriever.get_relevant_documents(query, return_metadata=True)
   
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # Combine the content of the relevant documents for generation
    combined_content = "\n".join([doc.page_content for doc in retrieved_docs])
    
    # Create a prompt with the combined content and the query

    content = f"""
    System: {SYSTEM_PROMPT}
    Context: {combined_content}
    Query: {query}
    """

    history = [
        HumanMessage(content=combined_content + "\n\nQuery: " + query)
    ]
        
    answer = llm(history)

    # history.append(AIMessage(content=answer.content))

    sources = [doc.metadata['source'] for doc in retrieved_docs]

    scores = [
        cosine_similarity(embeddings.embed_query(query),
                          embeddings.embed_query(doc.page_content))
        for doc in retrieved_docs
    ]

    data = [
    {"source": source, "score": score} 
    for source, score in 
    zip(sources, scores)]

    total_scores = defaultdict(float)
    counts = defaultdict(int)

    # Iterate over the list and accumulate total scores and counts by source
    for item in data:
        total_scores[item["source"]] += item["score"]
        counts[item["source"]] += 1

    # Calculate the average and convert the results back to a list of dictionaries
    doc_metadata = [
        {
        "source": source, 
        "score": total_scores[source] / counts[source],
        "url": get_public_url(source)
        } for source in total_scores]

    return answer.content, doc_metadata, history
  
def gen_resp(search_query, vector_store, history, k=3):
    if vector_store is None:
        vector_store = prep_vs()

    answer, doc_metadata, history = query_rag_system(vector_store, search_query, history, k)
    
    return answer, doc_metadata, history