import os, sys, re

sys.path.append("..")

from collections import defaultdict

from openai import AzureOpenAI

from utils.azure_utils import *

from utils.utils import *

from utils.few_shot import *

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_KEY"),  
  api_version = "2023-03-15-preview",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)


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

    sources = [doc.metadata['source'] for doc in retrieved_docs]

    scores = [
        cosine_similarity(embed_query(query),
                          embed_query(doc.page_content)
                          ) for doc in retrieved_docs
    ]

    if max(scores) <= 0.75:
        return "I'm sorry, I don't have an answer to that question. Please try rephrasing your question.", [], history
    
    # Combine the content of the relevant documents for generation

    combined_content = "\n".join(
        [summarize_content(doc.page_content, max_words=1000) for doc in retrieved_docs]
        )
    
    # Create a prompt with the combined content and the query

    content = f"""
    Context: {combined_content}
    Query: {query}
    """

    SYSTEM_PROMPT, FEW_SHOT_PROMPTS = get_prompts()

    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }

    response = client.chat.completions.create(
        model="gpt-4",
        messages=
        [system_message] +
        FEW_SHOT_PROMPTS +
        [{"role": "user", "content": content}]
    )

    answer = response.choices[0].message.content

    print("Answered...")

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

    return answer, [], history
  
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