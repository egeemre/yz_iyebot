import os
import re
import hashlib

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# =========================================================
# PROJE YOLLARI
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# =========================================================
# EMBEDDING MODEL (QWEN)
# =========================================================

EMBEDDING_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
print("Embedding modeli yükleniyor... (ilk sefer 2-4 dk sürebilir)")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# =========================================================
# CHUNK AYARLARI
# =========================================================

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)

# =========================================================
# CHROMA DB
# =========================================================

db = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings
)

# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def make_id(source_path: str, page: int, chunk_i: int, text: str) -> str:
    """Duplicate engellemek için benzersiz ID üretir"""
    raw = f"{source_path}|{page}|{chunk_i}|{text[:200]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def guess_source_type(filename: str) -> str:
    """Dosya adına göre belge türünü tahmin eder"""
    f = filename.lower()

    if "takvim" in f or "surec" in f or "akış" in f or "akis" in f:
        return "takvim"
    if "sss" in f:
        return "sss"
    if "duyuru" in f or "classroom" in f or "toplanti" in f:
        return "duyuru"
    if "ek" in f:
        return "ek_form"
    if "yonerge" in f or "yönerge" in f:
        return "yonerge"

    return "diger"


# =========================================================
# INGEST FONKSİYONU
# =========================================================

def ingest_document(file_path, source_type="diger", audience="ogrenci", section="Genel"):
    doc_name = os.path.basename(file_path)
    print(f"\n➡️ İşleniyor: {doc_name}")

    # Dosyayı yükle
    if file_path.endswith(".pdf"):
        pages = PyPDFLoader(file_path).load()
    elif file_path.endswith(".docx"):
        pages = Docx2txtLoader(file_path).load()
    else:
        print("⏭️ Desteklenmeyen format, atlandı.")
        return 0

    documents = []
    ids = []

    # Sayfa bazlı chunking
    for p_i, page in enumerate(pages):
        text = page.page_content.strip()
        text = re.sub(r"\n\s*\n", "\n\n", text)

        chunks = text_splitter.split_text(text)

        for c_i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source_type": source_type,
                        "doc_name": doc_name,
                        "source_path": file_path,
                        "section": section,
                        "audience": audience,
                        "page": p_i,
                        "chunk_index": c_i
                    }
                )
            )
            ids.append(make_id(file_path, p_i, c_i, chunk))

    db.add_documents(documents=documents, ids=ids)
    db.persist()

    print(f"✅ {doc_name}: {len(documents)} chunk eklendi.")
    return len(documents)


# =========================================================
# TÜM DOCUMENTS KLASÖRÜNÜ TARAYAN MAIN
# =========================================================

def ingest_all_documents():
    if not os.path.exists(DOCUMENTS_DIR):
        print("documents klasörü bulunamadı!")
        return

    total_files = 0
    total_chunks = 0

    for filename in sorted(os.listdir(DOCUMENTS_DIR)):
        if filename.lower().endswith((".pdf", ".docx")):
            total_files += 1
            path = os.path.join(DOCUMENTS_DIR, filename)

            source_type = guess_source_type(filename)

            total_chunks += ingest_document(
                file_path=path,
                source_type=source_type,
                audience="ogrenci",
                section="Genel"
            )

    print("\n==============================")
    print("📊 İndeksleme tamamlandı")
    print("Toplam dosya:", total_files)
    print("Toplam chunk:", total_chunks)
    print("Chroma yolu:", CHROMA_PATH)
    print("==============================\n")


# =========================================================
# SCRIPT OLARAK ÇALIŞTIRILIRSA
# =========================================================

if __name__ == "__main__":
    print("=== RAG Ingestion Başladı ===")
    ingest_all_documents()