import os, sys, docx

from io import BytesIO

import pandas as pd

sys.path.append("..")

from utils.blob_utils import prep_client

SYSTEM_PROMPT_BASE = """You are a helpful AI assistant designed to help users answer questions about
Southbend applications. Your goal is to provide helpful and accurate information to the user
to help them clarify their doubts and fill in their application. Be direct and concise in
your responses. Do not provide any information that is not relevant to the user's query,
or more than what's required. Assume the user's reading level is 8th grade. Answer in no more than 3-4 senteces
unless really necessary/appropriate to the query.

Key Areas for Human Escalation/Human Intervention:
Immigration Status: Both non-citizen questions will require human assistance to provide clear guidance based on residency and legal status.
Personal Challenges: Variable income, lack of traditional documentation, and disability-related accommodations are all too complex for automated responses, necessitating human intervention.
Fraud Detection: Any attempts to manipulate the system, including fraud-related inquiries or inconsistent information, should be escalated for human review.
Appeals Process: Denied applications require a formal appeals process, which should involve human agents to ensure users follow the correct procedures.

"""

DEFAULT_FALLBACK = "Please contact the Southbend office for more information."

FEW_SHOT_PROMPTS = []


def get_prompts():
    blob_client = prep_client(container="guardrail-qas", blob="qa-v1.csv")

    stream = blob_client.download_blob()

    with BytesIO() as buf:
        stream.readinto(buf)

        # needed to reset the buffer, otherwise, panda won't read from the start
        buf.seek(0)

        data = pd.read_csv(buf)
    
    blob_client = prep_client(container="misc", blob="app-checklist.docx")

    stream = BytesIO()
    blob_client.download_blob().readinto(stream)
    stream.seek(0)

    doc = docx.Document(stream)
    system_prompt_append = ""
    for paragraph in doc.paragraphs:
        system_prompt_append += paragraph.text + "\n"


    for idx, row in data.iterrows():
        
        FEW_SHOT_PROMPTS.append({
            "role": "user",
            "content": f"{row['query']} (Explanation: {row['explanation']})" 
        })
        FEW_SHOT_PROMPTS.append({
            "role": "assistant",
            "content": row["response"] # or if all responses are the same, can set to DEFAULT_FALLBACK
        })

    SYSTEM_PROMPT = f"""
    {SYSTEM_PROMPT_BASE}

    Use the following checklist to further inform your responses:
    {system_prompt_append}
    """

    return SYSTEM_PROMPT, FEW_SHOT_PROMPTS