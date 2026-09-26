from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import  RecursiveCharacterTextSplitter
from pathlib import Path

from backend.app.rag.embeddings import get_embedding_model

KNOWLEDGE_PATH=Path("data/knowledge")


def load_documents():
    documents = []
    for file_path in KNOWLEDGE_PATH.iterdir():
        if file_path.suffix.lower() == ".txt":
           loader= TextLoader(str(file_path), encoding="utf-8")
        elif file_path.suffix.lower() == ".pdf":
           loader= PyPDFLoader(str(file_path))
        else:
            continue
        documents.extend(loader.load())
    return documents

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    return splitter.split_documents(documents)

def generate_embeddings(chunks):
    embedding_model = get_embedding_model()

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    return embedding_model.embed_documents(texts)
