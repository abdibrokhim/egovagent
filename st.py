import streamlit as st
import os
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import openai
from pinecone import Pinecone
from langchain.vectorstores import Pinecone as PineconeVectorStore
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.callbacks import get_openai_callback
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("rag_application.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class RAGApplication:
    def __init__(self):
        """Initialize the RAG application with necessary configurations."""
        try:
            self.load_environment()
            self.initialize_clients()
            self.setup_prompts()
            self.setup_pipeline()
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise

    def load_environment(self):
        """Load and validate environment variables."""
        load_dotenv()

        # Use Streamlit secrets or environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("MY_PINECONE_API_KEY")

        if not self.openai_api_key or not self.pinecone_api_key:
            raise EnvironmentError("Missing required API keys")

        self.index_name = "607ff4227b6428eee08802c0"
        self.pinecone_environment = "us-east-1"

    def initialize_clients(self):
        """Initialize OpenAI and Pinecone clients."""
        try:
            openai.api_key = self.openai_api_key
            self.pc = Pinecone(api_key=self.pinecone_api_key)

            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            self.index = self.pc.Index(self.index_name)

            self.vector_store = PineconeVectorStore(
                index=self.index, embedding=self.embeddings, text_key="text"
            )

            logger.info("Successfully initialized all clients and connections")

        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            raise

    def setup_prompts(self):
        """Configure the prompt templates."""
        self.default_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
You are a knowledgeable assistant fluent in English. Use the provided context to answer questions accurately and helpfully.

Context:
{context}

Question:
{question}

Please provide a straightforward answer. If the context doesn't contain enough information to give answer, acknowledge this and provide the best possible answer based on available information.


Answer:
""",
        )

    def setup_pipeline(self):
        """Set up the RAG pipeline with configured components."""
        try:
            self.llm = OpenAI(
                api_key=self.openai_api_key, temperature=0.7, max_tokens=500
            )

            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 2}),
                chain_type="stuff",
                chain_type_kwargs={"prompt": self.default_prompt, "verbose": True},
                return_source_documents=True,
            )

            logger.info("Successfully set up RAG pipeline")

        except Exception as e:
            logger.error(f"Error setting up pipeline: {str(e)}")
            raise

#         "path_id": "6386e863ee4af88f66e5ae78"
# mp = "data.egov.uz"
#         var = "{mp}/eng/data{path_id}"
# [2](var)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG pipeline."""
        try:
            start_time = datetime.now()

            with get_openai_callback() as cb:
                result = self.qa_chain({"query": question})

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            return {
                "answer": result["result"],
                "source_documents": [
                    doc.page_content for doc in result["source_documents"]
                ],
                "metadata": {
                    "processing_time": processing_time,
                    "total_tokens": cb.total_tokens,
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_cost": cb.total_cost,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise


def initialize_session_state():
    """Initialize session state variables."""
    if "rag_app" not in st.session_state:
        try:
            st.session_state.rag_app = RAGApplication()
        except Exception as e:
            st.error(f"Error initializing application: {str(e)}")
            st.stop()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def main():
    st.set_page_config(
        page_title="Uzbek/English RAG Assistant", page_icon="🤖", layout="wide"
    )

    st.title("🤖 Uzbek/English RAG Assistant")
    st.markdown(
        """
    This application uses RAG (Retrieval-Augmented Generation) to answer questions in Uzbek and English.
    The answers are based on the information stored in the Pinecone vector database.
    """
    )

    # Initialize session state
    initialize_session_state()

    # Create two columns for the layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # Chat interface
        st.subheader("Chat Interface")

        # Question input
        user_question = st.text_input(
            "Enter your question in Uzbek or English:",
            key="user_input",
            placeholder="Type your question here...",
        )

        # Submit button
        if st.button("Submit Question", key="submit"):
            if user_question:
                with st.spinner("Processing your question..."):
                    try:
                        # Get response from RAG
                        response = st.session_state.rag_app.query(user_question)

                        # Add to chat history
                        st.session_state.chat_history.append(
                            {"question": user_question, "response": response}
                        )

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Display chat history
        if st.session_state.chat_history:
            for chat in reversed(st.session_state.chat_history):
                with st.expander(f"Q: {chat['question']}", expanded=True):
                    st.markdown("**Answer:**")
                    st.write(chat["response"]["answer"])

                    st.markdown("**Sources:**")
                    for idx, source in enumerate(
                        chat["response"]["source_documents"], 1
                    ):
                        st.markdown(f"Source {idx}:")
                        st.text(source[:200] + "..." if len(source) > 200 else source)

    with col2:
        # Metrics and information
        st.subheader("Session Metrics")

        if st.session_state.chat_history:
            latest = st.session_state.chat_history[-1]["response"]["metadata"]

            st.metric(
                label="Processing Time",
                value=f"{latest['processing_time']:.2f} seconds",
            )

            st.metric(label="Total Tokens Used", value=latest["total_tokens"])

            st.metric(label="Cost", value=f"${latest['total_cost']:.4f}")

            # Display cumulative statistics
            st.subheader("Cumulative Statistics")
            total_tokens = sum(
                chat["response"]["metadata"]["total_tokens"]
                for chat in st.session_state.chat_history
            )
            total_cost = sum(
                chat["response"]["metadata"]["total_cost"]
                for chat in st.session_state.chat_history
            )

            st.metric(label="Total Session Tokens", value=total_tokens)

            st.metric(label="Total Session Cost", value=f"${total_cost:.4f}")

        # Clear chat history button
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.experimental_rerun()


if __name__ == "__main__":
    main()
