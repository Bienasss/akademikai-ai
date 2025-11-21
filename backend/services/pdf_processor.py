import pdfplumber
import PyPDF2
from pathlib import Path
from typing import List, Dict, Optional
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from backend.config import settings


class PDFProcessor:
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[Dict]:
        try:
            text_content = []
            pages_info = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        cleaned_text = self.clean_text(text)
                        text_content.append(cleaned_text)
                        pages_info.append({
                            'page': page_num,
                            'text': cleaned_text,
                            'char_count': len(cleaned_text)
                        })
            
            if not text_content:
                return None
            
            full_text = '\n\n'.join(text_content)
            
            return {
                'file_path': str(file_path),
                'filename': Path(file_path).name,
                'full_text': full_text,
                'pages': pages_info,
                'total_pages': len(pages_info),
                'total_chars': len(full_text)
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict]:
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunk_text = text[start:]
            else:
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                
                if last_period > start and last_period > last_newline:
                    end = last_period + 1
                elif last_newline > start:
                    end = last_newline + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start': start,
                    'end': end,
                    'chunk_index': chunk_index,
                    'char_count': len(chunk_text)
                })
                chunk_index += 1
            
            start = end - overlap
            if start < 0:
                start = end
        
        return chunks
    
    def process_document(self, file_path: str) -> Optional[List[Dict]]:
        doc_data = self.extract_text_from_pdf(file_path)
        if not doc_data:
            return None
        
        chunks = self.chunk_text(doc_data['full_text'])
        
        processed_chunks = []
        for chunk in chunks:
            processed_chunks.append({
                'text': chunk['text'],
                'metadata': {
                    'source': doc_data['filename'],
                    'file_path': doc_data['file_path'],
                    'page': self._get_page_for_position(chunk['start'], doc_data['pages']),
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': len(chunks),
                    'char_count': chunk['char_count']
                }
            })
        
        return processed_chunks
    
    def _get_page_for_position(self, position: int, pages: List[Dict]) -> int:
        current_pos = 0
        for page_info in pages:
            current_pos += page_info['char_count'] + 2
            if position < current_pos:
                return page_info['page']
        return pages[-1]['page'] if pages else 1
    
    async def process_file(self, file_path: str) -> Optional[List[Dict]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.process_document, file_path)
    
    async def process_directory(self, directory: str) -> List[Dict]:
        directory_path = Path(directory)
        pdf_files = list(directory_path.rglob("*.pdf"))
        
        if not pdf_files:
            return []
        
        all_chunks = []
        
        tasks = [self.process_file(str(pdf_file)) for pdf_file in pdf_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                all_chunks.extend(result)
        
        return all_chunks
    
    def find_pdf_files(self, directory: str) -> List[str]:
        directory_path = Path(directory)
        pdf_files = list(directory_path.rglob("*.pdf"))
        return [str(f) for f in pdf_files]
