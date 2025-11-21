#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.services.pdf_processor import PDFProcessor
from backend.services.vectorizer import Vectorizer
from backend.config import settings
from tqdm import tqdm


async def process_all_documents():
    print("Starting document processing...")
    print(f"Data directory: {settings.DATA_DIR}")
    print(f"Scraped files directory: {settings.SCRAPED_FILES_DIR}")
    
    pdf_processor = PDFProcessor()
    vectorizer = Vectorizer()
    
    all_chunks = []
    
    data_dir = Path(settings.DATA_DIR)
    scraped_dir = Path(settings.SCRAPED_FILES_DIR)
    
    print("\nProcessing data directory...")
    if data_dir.exists():
        data_chunks = await pdf_processor.process_directory(str(data_dir))
        if data_chunks:
            all_chunks.extend(data_chunks)
            print(f"Processed {len(data_chunks)} chunks from data directory")
    else:
        print(f"Data directory not found: {data_dir}")
    
    print("\nProcessing scraped files directory...")
    if scraped_dir.exists():
        scraped_chunks = await pdf_processor.process_directory(str(scraped_dir))
        if scraped_chunks:
            all_chunks.extend(scraped_chunks)
            print(f"Processed {len(scraped_chunks)} chunks from scraped files directory")
    else:
        print(f"Scraped files directory not found: {scraped_dir}")
    
    if not all_chunks:
        print("No chunks to vectorize. Exiting.")
        return
    
    print(f"\nTotal chunks to vectorize: {len(all_chunks)}")
    print("Generating embeddings and storing in vector database...")
    
    batch_size = 100
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Vectorizing chunks"):
        batch = all_chunks[i:i + batch_size]
        await vectorizer.add_documents(batch)
    
    print(f"\nCompleted! Vectorized {len(all_chunks)} chunks")
    print(f"Vector database location: {settings.CHROMA_DB_PATH}")
    print(f"Total documents in collection: {vectorizer.get_collection_count()}")


if __name__ == "__main__":
    asyncio.run(process_all_documents())
