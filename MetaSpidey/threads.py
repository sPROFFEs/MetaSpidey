from PyQt6.QtCore import QThread, pyqtSignal
from crawlers import Crawler, BruteForcer, FileDownloader
from urllib.parse import urljoin  # Añadida esta importación
import time

import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class CrawlerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, url, max_depth, delay, extensions, threads):
        super().__init__()
        self.initial_url = url
        self.max_depth = max_depth
        self.delay = delay
        self.extensions = extensions
        self.threads = threads
        self.crawler = Crawler()
        self.visited_urls = set()
        self.lock = threading.Lock()

    def run(self):
        urls_to_crawl = queue.Queue()
        urls_to_crawl.put((self.initial_url, 0))
        self.visited_urls.add(self.initial_url)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {}
            while not urls_to_crawl.empty() or futures:
                while not urls_to_crawl.empty():
                    url, depth = urls_to_crawl.get()
                    if depth < self.max_depth and not self.crawler.should_stop:
                        future = executor.submit(self.crawler.get_links, url, self.extensions)
                        futures[future] = (url, depth)

                for future in as_completed(list(futures)):
                    url, depth = futures.pop(future)
                    try:
                        links = future.result()
                        self.progress.emit(f"Crawled: {url} | Found {len(links)} links")
                        for link in links:
                            with self.lock:
                                if link not in self.visited_urls:
                                    self.visited_urls.add(link)
                                    if depth + 1 < self.max_depth:
                                        urls_to_crawl.put((link, depth + 1))
                        if self.delay > 0:
                            time.sleep(self.delay)
                    except Exception as e:
                        self.progress.emit(f"Error crawling {url}: {e}")

                    if self.crawler.should_stop:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
                if self.crawler.should_stop:
                    break

        self.finished.emit(list(self.visited_urls))

    def stop(self):
        self.crawler.should_stop = True

from concurrent.futures import ThreadPoolExecutor, as_completed

class BruteForceThread(QThread):
    progress = pyqtSignal(str)
    url_found = pyqtSignal(str)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, fuzz_template, dictionary_file, threads, status_codes):
        super().__init__()
        self.brute_forcer = BruteForcer(fuzz_template, dictionary_file, threads, status_codes)
        self.total_lines = 0
        try:
            with open(dictionary_file, 'r') as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
            self.total_lines = len(self.wordlist)
        except Exception as e:
            self.progress.emit(f"Error al leer el diccionario: {e}")
            self.wordlist = []

    def stop(self):
        self.brute_forcer.stop()
        self.progress.emit("Deteniendo el proceso de fuerza bruta...")

    def run(self):
        if not self.wordlist:
            self.finished.emit([])
            return

        discovered_urls = []
        processed_count = 0

        with ThreadPoolExecutor(max_workers=self.brute_forcer.threads) as executor:
            futures = {executor.submit(self.brute_forcer.check_path, path): path for path in self.wordlist}

            for future in as_completed(futures):
                if self.brute_forcer.should_stop:
                    break

                result = future.result()
                processed_count += 1

                if result:
                    url, status_code = result
                    discovered_urls.append(url)
                    self.url_found.emit(f"[+] URL encontrada: {url} (Código: {status_code})")

                progress_percent = (processed_count / self.total_lines) * 100
                self.status.emit(f"Progreso: {progress_percent:.1f}% ({processed_count}/{self.total_lines})")

        self.finished.emit(discovered_urls)

class DownloadThread(QThread):
    progress = pyqtSignal(str)
    file_downloaded = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, urls, output_dir):
        super().__init__()
        self.downloader = FileDownloader(urls, output_dir)

    def run(self):
        downloaded_files = []
        for url in self.downloader.urls:
            if self.downloader.should_stop:
                break
            
            self.progress.emit(f"Descargando {url}")
            filepath = self.downloader.download_file(url)
            if filepath:
                downloaded_files.append(filepath)
                self.file_downloaded.emit(filepath)

        self.finished.emit(downloaded_files)

    def stop(self):
        self.downloader.should_stop = True
