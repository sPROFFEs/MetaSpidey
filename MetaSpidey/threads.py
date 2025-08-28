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

import json
from crawlers import Crawler, FfufRunner, FileDownloader

class BruteForceThread(QThread):
    progress = pyqtSignal(str)
    url_found = pyqtSignal(str)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, options):
        super().__init__()
        self.ffuf_runner = FfufRunner(options)
        self.total_lines = 0
        try:
            with open(options['dictionary'], 'r') as f:
                self.total_lines = sum(1 for _ in f)
        except Exception as e:
            self.progress.emit(f"Error al contar líneas del diccionario: {e}")

    def stop(self):
        self.progress.emit("Deteniendo el proceso de ffuf...")
        self.ffuf_runner.stop()

    def run(self):
        try:
            process = self.ffuf_runner.run()
            discovered_urls = []
            processed_count = 0

            # Read ffuf's stdout line by line
            for line in iter(process.stdout.readline, ''):
                try:
                    result = json.loads(line)

                    # ffuf outputs results as JSON objects
                    if 'url' in result and 'status' in result:
                        url = result['url']
                        status = result['status']
                        discovered_urls.append(url)
                        self.url_found.emit(f"[+] {url} (Status: {status})")

                    processed_count += 1
                    if self.total_lines > 0:
                        progress_percent = (processed_count / self.total_lines) * 100
                        self.status.emit(f"Progreso: {progress_percent:.1f}% ({processed_count}/{self.total_lines})")

                except json.JSONDecodeError:
                    # Ignore lines that are not valid JSON (e.g., ffuf's header/footer)
                    self.progress.emit(line.strip())

            process.stdout.close()
            return_code = process.wait()
            if return_code != 0:
                stderr_output = process.stderr.read()
                self.progress.emit(f"ffuf terminó con error (código {return_code}):")
                self.progress.emit(stderr_output)

            self.finished.emit(discovered_urls)

        except FileNotFoundError:
            self.progress.emit("Error: 'ffuf' no encontrado. Asegúrese de que esté instalado y en su PATH o en el directorio del proyecto.")
            self.finished.emit([])
        except Exception as e:
            self.progress.emit(f"Error al ejecutar ffuf: {str(e)}")
            self.finished.emit([])

import zipfile
import requests

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

class DownloadWordlistThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.seclists_url = "https://github.com/danielmiessler/SecLists/archive/master.zip"
        self.output_dir = "wordlists"
        self.zip_path = os.path.join(self.output_dir, "seclists.zip")

    def run(self):
        try:
            self.progress.emit("Creando directorio de wordlists...")
            os.makedirs(self.output_dir, exist_ok=True)

            self.progress.emit(f"Descargando SecLists desde {self.seclists_url}...")
            response = requests.get(self.seclists_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(self.zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            self.progress.emit(f"Descargando... {percent:.1f}%")

            self.progress.emit("Descarga completa. Extrayendo archivos...")
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir)

            self.progress.emit("Extracción completa. Limpiando...")
            os.remove(self.zip_path)

            self.progress.emit("SecLists ha sido instalado en el directorio 'wordlists'.")
            self.finished.emit()

        except Exception as e:
            self.progress.emit(f"Error al descargar SecLists: {str(e)}")
            self.finished.emit()
