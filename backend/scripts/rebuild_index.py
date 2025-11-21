#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.vectorizer import Vectorizer
from backend.scripts.process_documents import process_all_documents


async def rebuild_index():
    print("Rebuilding vector index...")
    print("This will delete the existing index and rebuild it from scratch.")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    vectorizer = Vectorizer()
    print("Resetting vector database...")
    vectorizer.reset_collection()
    
    print("Processing all documents...")
    await process_all_documents()
    
    print("Index rebuild complete!")


if __name__ == "__main__":
    asyncio.run(rebuild_index())
