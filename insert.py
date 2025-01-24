import os
import json
import openai
import tqdm
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import logging

# Set up logging
logging.basicConfig(filename='process.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_pinecone():
    """Initialize Pinecone client and create index if it doesn't exist."""
    load_dotenv()

    openai.api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("MY_PINECONE_API_KEY")
    if not pinecone_api_key:
        logging.error("Pinecone API key is not set.")
        raise ValueError("Pinecone API key is not set.")

    # Initialize Pinecone
    logging.info("Initializing Pinecone client...")
    pc = Pinecone(api_key=pinecone_api_key)

    # Index name
    index_name = "607ff4227b6428eee08802c0"
    logging.info(f"Using index name: {index_name}")

    # If index does not exist, create it
    if index_name not in pc.list_indexes():
        logging.info(f"Index '{index_name}' does not exist. Creating it...")
        pc.create_index(
            name=index_name,
            dimension=1536,  # dimension for text-embedding-ada-002
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        logging.info(f"Index '{index_name}' created successfully.")
    else:
        logging.info(f"Index '{index_name}' already exists.")

    return pc.Index(index_name)

def chunk_text_by_tokens(text, tokens_per_chunk=500):
    """Splits text into smaller chunks of tokens_per_chunk using the approximate count of whitespace-separated tokens."""
    words = text.split()
    logging.info(f"Chunking text into smaller pieces of {tokens_per_chunk} tokens each.")
    for i in range(0, len(words), tokens_per_chunk):
        yield " ".join(words[i : i + tokens_per_chunk])

def embed_and_upsert(index, texts, metadata_list, batch_size=32):
    """Takes a list of texts and corresponding metadata, creates embeddings in batches, and upserts to Pinecone."""
    logging.info("Starting embedding and upserting process...")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_metadata = metadata_list[i : i + batch_size]
        logging.info(f"Processing batch {i // batch_size + 1} with {len(batch_texts)} texts.")

        # Create embeddings (batch call)
        try:
            logging.info("Creating embeddings...")
            response = openai.Embedding.create(
                input=batch_texts, 
                model="text-embedding-ada-002"
            )
            logging.info("Embeddings created successfully.")
        except Exception as e:
            logging.error(f"OpenAI embedding error: {e}")
            continue
        
        # Prepare upsert data for Pinecone
        vectors = []
        for j, emb_data in enumerate(response["data"]):
            embedding = emb_data["embedding"]
            text = batch_texts[j]
            meta = batch_metadata[j]
            vector_id = meta["id"]

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": meta
            })

        # Upsert the batch
        try:
            logging.info(f"Upserting {len(vectors)} vectors to Pinecone...")
            index.upsert(
                vectors=vectors,
                namespace="agriculture_607ff4227b6428eee08802c0"
            )
            logging.info("Upsert successful.")
        except Exception as e:
            logging.error(f"Pinecone upsert error: {e}")

def process_json_files(index):
    """Process JSON files in the specified directory and embed their contents."""
    json_directory = "607ff4227b6428eee08802c0"
    logging.info(f"Processing JSON files in directory: {json_directory}")

    if not os.path.isdir(json_directory):
        logging.error(f"The directory '{json_directory}' does not exist.")
        raise FileNotFoundError(f"The directory '{json_directory}' does not exist.")

    for filename in tqdm.tqdm(os.listdir(json_directory)):
        if not filename.endswith(".json"):
            logging.info(f"Skipping non-JSON file: {filename}")
            continue

        filepath = os.path.join(json_directory, filename)
        logging.info(f"Loading JSON file: {filepath}")

        # Load JSON file
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logging.info(f"Loaded JSON file '{filename}' successfully.")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON file '{filename}': {e}")
            continue

        texts_to_embed = []
        metadata_list = []

        # Extract text based on the structure of your JSON
        if isinstance(data, dict):
            logging.info(f"Extracting data from JSON dictionary...")
            for k, v in data.items():
                item_text = f"{k}: {v}"
                for chunk in chunk_text_by_tokens(item_text):
                    texts_to_embed.append(chunk)
                    text_hash = hash(chunk)
                    metadata_list.append({
                        "id": f"{filename}-{k}-{text_hash}",
                        "filename": filename,
                        "key": k,
                        "value": str(v),
                    })

        elif isinstance(data, list):
            logging.info(f"Extracting data from JSON list...")
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    flat_str = "; ".join(f"{k}: {v}" for k, v in item.items())
                    for chunk in chunk_text_by_tokens(flat_str):
                        texts_to_embed.append(chunk)
                        text_hash = hash(chunk)
                        metadata_list.append({
                            "id": f"{filename}-{idx}-{text_hash}",
                            "filename": filename,
                            "item_index": idx,
                            **item
                        })
                else:
                    for chunk in chunk_text_by_tokens(str(item)):
                        texts_to_embed.append(chunk)
                        text_hash = hash(chunk)
                        metadata_list.append({
                            "id": f"{filename}-{idx}-{text_hash}",
                            "filename": filename,
                            "item_index": idx,
                            "content": str(item)
                        })
        else:
            logging.warning(f"Unexpected JSON structure in file {filename}. Skipping.")
            continue

        # Embed & upsert
        if texts_to_embed:
            logging.info(f"Embedding and upserting {len(texts_to_embed)} texts...")
            embed_and_upsert(index, texts_to_embed, metadata_list, batch_size=32)

if __name__ == "__main__":
    logging.info("Starting the Pinecone process...")
    index = initialize_pinecone()
    process_json_files(index)
    logging.info("All JSON files have been processed and embeddings stored in Pinecone.")
