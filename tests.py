from pinecone import Pinecone, ServerlessSpec
import openai 
import os
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

pc = Pinecone(api_key=os.getenv("MY_PINECONE_API_KEY"))

index_name = "607ff03a7b6428eee08802b8"

index = pc.Index(index_name)

def embed(docs: list[str]) -> list[list[float]]:
    res = openai.Embedding.create(
        input=docs,
        model="text-embedding-ada-002"
    )
    doc_embeds = [r.embedding for r in res.data] 
    return doc_embeds 


### Query
query = "Deputy Minister of Tourism and Sports phone number"

x = embed([query])

results = index.query(
    namespace=index_name,
    vector=x[0],
    top_k=2,
    include_values=False,
    include_metadata=True
)

print(results)