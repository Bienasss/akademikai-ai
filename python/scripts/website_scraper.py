#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from urllib.robotparser import RobotFileParser
import time
import re
from typing import Set, List, Dict, Tuple
from tqdm import tqdm
import mimetypes
from pathlib import Path
import logging
from datetime import datetime
import argparse


class WebsiteScraper:
    
    def __init__(self, base_url: str, output_dir: str = "scraped_files", max_documents: int = 100):
        self.base_url = base_url.rstrip('/')
        self.domain = urllib.parse.urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_documents = max_documents
        
        self.file_extensions = {
            'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'media': ['.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.flac'],
            'other': ['.xml', '.json', '.csv', '.sql', '.log']
        }
        
        self.visited_urls: Set[str] = set()
        self.found_files: List[Dict] = []
        self.downloaded_files: List[str] = []
        self.failed_downloads: List[str] = []
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.setup_logging()
        
    def setup_logging(self):
        log_file = self.output_dir / 'scraper.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_robots_txt(self) -> bool:
        try:
            robots_url = f"{self.base_url}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            can_fetch = rp.can_fetch('*', self.base_url)
            self.logger.info(f"Robots.txt check: {'Allowed' if can_fetch else 'Disallowed'}")
            return can_fetch
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt: {e}")
            return True
    
    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            return (parsed.netloc == self.domain or 
                   parsed.netloc == '' or 
                   parsed.netloc.endswith(f'.{self.domain}'))
        except:
            return False
    
    def normalize_url(self, url: str, base_url: str) -> str:
        return urllib.parse.urljoin(base_url, url)
    
    def get_file_info(self, url: str) -> Dict:
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)
        
        if not filename or '.' not in filename:
            if 'filename=' in url:
                filename = re.search(r'filename=([^&]+)', url)
                filename = filename.group(1) if filename else 'unknown_file'
            else:
                filename = f"file_{hash(url) % 10000}"
        
        ext = Path(filename).suffix.lower()
        category = 'other'
        for cat, extensions in self.file_extensions.items():
            if ext in extensions:
                category = cat
                break
        
        return {
            'url': url,
            'filename': filename,
            'extension': ext,
            'category': category,
            'size': None
        }
    
    def find_files_on_page(self, url: str) -> List[Dict]:
        try:
            self.logger.info(f"Scraping page: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            files = []
            
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                full_url = self.normalize_url(href, url)
                
                parsed = urllib.parse.urlparse(full_url)
                path = parsed.path.lower()
                
                has_file_ext = any(
                    path.endswith(ext) 
                    for exts in self.file_extensions.values() 
                    for ext in exts
                )
                
                is_download_link = (
                    'download' in href.lower() or 
                    'attachment' in href.lower() or
                    'file' in href.lower() or
                    link.get('download') is not None
                )
                
                if has_file_ext or is_download_link:
                    if self.is_valid_url(full_url):
                        file_info = self.get_file_info(full_url)
                        files.append(file_info)
                        self.logger.debug(f"Found file: {file_info['filename']}")
            
            return files
            
        except requests.RequestException as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
            return []
    
    def crawl_website(self, start_url: str, max_pages: int = 100) -> List[Dict]:
        self.logger.info(f"Starting website crawl from: {start_url}")
        self.logger.info(f"Document limit set to: {self.max_documents}")
        
        urls_to_visit = [start_url]
        all_files = []
        pages_crawled = 0
        
        with tqdm(desc="Crawling pages", unit="pages") as pbar:
            while urls_to_visit and pages_crawled < max_pages and len(all_files) < self.max_documents:
                current_url = urls_to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                self.visited_urls.add(current_url)
                pages_crawled += 1
                pbar.update(1)
                pbar.set_postfix({
                    'Files': len(all_files),
                    'Limit': self.max_documents,
                    'Page': current_url.split('/')[-1][:20]
                })
                
                try:
                    response = self.session.get(current_url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    page_files = self.find_files_on_page(current_url)
                    
                    for file_info in page_files:
                        if len(all_files) >= self.max_documents:
                            break
                        all_files.append(file_info)
                    
                    if len(all_files) >= self.max_documents:
                        self.logger.info(f"Reached document limit of {self.max_documents}")
                        break
                    
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        full_url = self.normalize_url(href, current_url)
                        
                        if (self.is_valid_url(full_url) and 
                            full_url not in self.visited_urls and
                            full_url not in urls_to_visit and
                            not any(full_url.lower().endswith(ext) 
                                   for exts in self.file_extensions.values() 
                                   for ext in exts)):
                            urls_to_visit.append(full_url)
                    
                    time.sleep(0.5)
                    
                except requests.RequestException as e:
                    self.logger.error(f"Error crawling {current_url}: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Unexpected error crawling {current_url}: {e}")
                    continue
        
        self.logger.info(f"Crawling completed. Found {len(all_files)} files across {pages_crawled} pages")
        return all_files
    
    def download_file(self, file_info: Dict) -> bool:
        url = file_info['url']
        filename = file_info['filename']
        category = file_info['category']
        
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        file_path = category_dir / filename
        counter = 1
        original_stem = file_path.stem
        original_suffix = file_path.suffix
        
        while file_path.exists():
            new_name = f"{original_stem}_{counter}{original_suffix}"
            file_path = category_dir / new_name
            counter += 1
        
        try:
            self.logger.debug(f"Downloading: {url}")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, 
                             desc=f"Downloading {filename[:20]}", leave=False) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            self.downloaded_files.append(str(file_path))
            self.logger.info(f"Downloaded: {filename}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Download failed for {filename}: {e}")
            self.failed_downloads.append(url)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {filename}: {e}")
            self.failed_downloads.append(url)
            return False
    
    def download_all_files(self, files: List[Dict]) -> None:
        if not files:
            self.logger.info("No files to download")
            return
        
        unique_files = []
        seen_urls = set()
        for file_info in files:
            if file_info['url'] not in seen_urls:
                unique_files.append(file_info)
                seen_urls.add(file_info['url'])
        
        files_to_download = unique_files[:self.max_documents]
        
        self.logger.info(f"Downloading {len(files_to_download)} files (limit: {self.max_documents})")
        
        with tqdm(files_to_download, desc="Downloading files", unit="files") as pbar:
            for file_info in pbar:
                pbar.set_postfix({'File': file_info['filename'][:20]})
                self.download_file(file_info)
                time.sleep(0.2)
    
    def generate_report(self) -> str:
        report_path = self.output_dir / 'scraping_report.txt'
        
        categories = {}
        for file_path in self.downloaded_files:
            category = Path(file_path).parent.name
            if category not in categories:
                categories[category] = []
            categories[category].append(Path(file_path).name)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Website Scraping Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Website: {self.base_url}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Document limit: {self.max_documents}\n")
            f.write(f"Pages crawled: {len(self.visited_urls)}\n")
            f.write(f"Files found: {len(self.found_files)}\n")
            f.write(f"Files downloaded: {len(self.downloaded_files)}\n")
            f.write(f"Failed downloads: {len(self.failed_downloads)}\n\n")
            
            f.write("Files by Category:\n")
            f.write("-" * 30 + "\n")
            for category, files in categories.items():
                f.write(f"\n{category.upper()} ({len(files)} files):\n")
                for filename in sorted(files):
                    f.write(f"  - {filename}\n")
            
            if self.failed_downloads:
                f.write(f"\nFailed Downloads ({len(self.failed_downloads)}):\n")
                f.write("-" * 30 + "\n")
                for url in self.failed_downloads:
                    f.write(f"  - {url}\n")
        
        return str(report_path)
    
    def scrape_website(self, max_pages: int = 100) -> Dict:
        print(f"Website Scraper for {self.base_url}")
        print("=" * 60)
        print(f"Document limit: {self.max_documents}")
        print(f"Output directory: {self.output_dir}")
        print(f"Max pages to crawl: {max_pages}")
        print()
        
        if not self.check_robots_txt():
            print("Warning: robots.txt suggests scraping may not be allowed")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return {'status': 'cancelled'}
        
        start_time = time.time()
        
        try:
            self.found_files = self.crawl_website(self.base_url, max_pages)
            
            if not self.found_files:
                print("No files found on the website")
                return {'status': 'no_files_found'}
            
            print(f"\nFound {len(self.found_files)} files:")
            categories = {}
            for file_info in self.found_files:
                cat = file_info['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in categories.items():
                print(f"  - {category}: {count} files")
            
            files_to_download = min(len(self.found_files), self.max_documents)
            print(f"\nReady to download {files_to_download} files to '{self.output_dir}'")
            response = input("Proceed with download? (Y/n): ")
            if response.lower() == 'n':
                return {'status': 'download_cancelled'}
            
            self.download_all_files(self.found_files)
            
            report_path = self.generate_report()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\nScraping completed!")
            print(f"Duration: {duration:.1f} seconds")
            print(f"Files saved to: {self.output_dir}")
            print(f"Report saved to: {report_path}")
            print(f"Successfully downloaded: {len(self.downloaded_files)} files")
            if self.failed_downloads:
                print(f"Failed downloads: {len(self.failed_downloads)} files")
            
            return {
                'status': 'completed',
                'files_found': len(self.found_files),
                'files_downloaded': len(self.downloaded_files),
                'failed_downloads': len(self.failed_downloads),
                'duration': duration,
                'output_dir': str(self.output_dir),
                'report_path': report_path
            }
            
        except KeyboardInterrupt:
            print("\nScraping interrupted by user")
            return {'status': 'interrupted'}
        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {e}")
            return {'status': 'error', 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Website File Scraper with configurable document limit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python website_scraper.py https://example.com --limit 50
  python website_scraper.py https://example.com --output downloads --pages 500 --limit 200
        """
    )
    
    parser.add_argument('url', help='Website URL to scrape')
    parser.add_argument('--limit', '-l', type=int, default=100,
                       help='Maximum number of documents to download (default: 100)')
    parser.add_argument('--output', '-o', default='scraped_files',
                       help='Output directory (default: scraped_files)')
    parser.add_argument('--pages', '-p', type=int, default=200,
                       help='Maximum pages to crawl (default: 200)')
    
    args = parser.parse_args()
    
    print(f"Website File Scraper")
    print("=" * 40)
    print(f"Target website: {args.url}")
    print(f"Document limit: {args.limit}")
    print(f"Output directory: {args.output}")
    print(f"Max pages to crawl: {args.pages}")
    print()
    
    scraper = WebsiteScraper(args.url, args.output, args.limit)
    
    results = scraper.scrape_website(args.pages)
    
    if results['status'] == 'completed':
        print(f"\nScraping successful!")
        print(f"Summary:")
        print(f"  - Files found: {results['files_found']}")
        print(f"  - Files downloaded: {results['files_downloaded']}")
        print(f"  - Duration: {results['duration']:.1f}s")
    else:
        print(f"\nScraping ended with status: {results['status']}")


if __name__ == "__main__":
    main()