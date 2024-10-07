import os, sys, re

sys.path.append("..")

from collections import defaultdict

from openai import AzureOpenAI

from utils.azure_utils import *

from utils.utils import *

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_KEY"),  
  api_version = "2023-03-15-preview",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

SYSTEM_PROMPT = """You are a helpful AI assistant designed to help users answer questions about
Southbend applications. Your goal is to provide helpful and accurate information to the user
to help them clarify their doubts and fill in their application. Be direct and concise in
your responses. Do not provide any information that is not relevant to the user's query,
or more than what's required. Assume the user's reading level is 8th grade. Answer in no more than 3-4 senteces
unless really necessary/appropriate to the query."""

def query_rag_system(vector_store, query, history, k):

    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})

    if not is_specific_query(query):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}]
        )

        answer = response.choices[0].message.content

        return answer, [], history

    print("Initalized Retriever...")
    
    retrieved_docs = retriever.get_relevant_documents(query, return_metadata=True)

    print("Retrieved Docs...")
    
    # Combine the content of the relevant documents for generation

    combined_content = "\n".join(
        [summarize_content(doc.page_content, max_words=1000) for doc in retrieved_docs]
        )
    
    # Create a prompt with the combined content and the query

    content = f"""
    Context: {combined_content}
    Query: {query}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )

    answer = response.choices[0].message.content

    print("Answered...")

    sources = [doc.metadata['source'] for doc in retrieved_docs]

    scores = [
        cosine_similarity(embed_query(query),
                          embed_query(doc.page_content)
                          ) for doc in retrieved_docs
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

    doc_metadata = sorted(doc_metadata, key=lambda x: x["score"], reverse=True)

    return answer, doc_metadata, history
  
def gen_resp(search_query, vs_dict, history, k=3):

    responses = []

    for key, vs in vs_dict.items():
        answer, doc_metadata, history = query_rag_system(vs, search_query, history, k)

        response = {
            "answer": answer,
            "sources": doc_metadata,
            "vs": key
        }

        responses.append(response)
    
    return responses, history