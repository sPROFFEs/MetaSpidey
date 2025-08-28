from PyQt6.QtCore import QThread, pyqtSignal
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import zipfile
import requests
import shutil
import sys

from crawlers import Crawler, FfufRunner, FileDownloader

class CrawlerThread(QThread):
    progress = pyqtSignal(str)
    url_found = pyqtSignal(str) # Signal for real-time UI updates
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
                        if links is not None:
                            self.progress.emit(f"Crawled: {url} | Found {len(links)} links")
                            for link in links:
                                with self.lock:
                                    if link not in self.visited_urls:
                                        self.visited_urls.add(link)
                                        self.url_found.emit(link) # Emit signal for each new URL
                                        if depth + 1 < self.max_depth:
                                            urls_to_crawl.put((link, depth + 1))
                            if self.delay > 0:
                                time.sleep(self.delay)
                    except requests.exceptions.RequestException as e:
                        # Catch specific request-related errors (like LocationParseError)
                        self.progress.emit(f"Could not crawl {url}: Invalid URL or connection error.")
                        self.progress.emit(f"  Details: {e}")
                    except Exception as e:
                        # Catch any other unexpected errors during crawling
                        self.progress.emit(f"An unexpected error occurred while crawling {url}: {e}")

                    if self.crawler.should_stop:
                        for f in futures:
                            f.cancel()
                        break
                if self.crawler.should_stop:
                    break

        self.finished.emit(list(self.visited_urls))

    def stop(self):
        self.crawler.should_stop = True

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
            with open(options['dictionary'], 'r', encoding='utf-8', errors='ignore') as f:
                self.total_lines = sum(1 for _ in f)
        except Exception as e:
            self.progress.emit(f"Error counting dictionary lines: {e}")

    def stop(self):
        self.progress.emit("Stopping ffuf process...")
        self.ffuf_runner.stop()

    def run(self):
        try:
            process = self.ffuf_runner.run()
            discovered_urls = []

            for line in iter(process.stdout.readline, ''):
                try:
                    result = json.loads(line)
                    if 'url' in result and 'status' in result:
                        url = result['url']
                        status = result['status']
                        discovered_urls.append(url)
                        self.url_found.emit(f"[+] {url} (Status: {status})")

                        self.status.emit(f"Found: {len(discovered_urls)} | Last found: {url}")

                except json.JSONDecodeError:
                    self.progress.emit(line.strip())

            process.stdout.close()
            return_code = process.wait()
            if return_code != 0:
                stderr_output = process.stderr.read()
                if stderr_output:
                    self.progress.emit(f"ffuf exited with error (code {return_code}):")
                    self.progress.emit(stderr_output)

            self.finished.emit(discovered_urls)

        except FileNotFoundError:
            self.progress.emit("Error: 'ffuf' executable not found. Please run 'python launch.py install'.")
            self.finished.emit([])
        except Exception as e:
            self.progress.emit(f"Error running ffuf: {str(e)}")
            self.finished.emit([])

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
            
            self.progress.emit(f"Downloading {url}")
            filepath = self.downloader.download_file(url)
            if filepath:
                downloaded_files.append(filepath)
                self.file_downloaded.emit(filepath)

        self.finished.emit(downloaded_files)

    def stop(self):
        self.downloader.should_stop = True

class DownloadWordlistThread(QThread):
    progress = pyqtSignal(str)
    progress_percentage = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, test_mode=False):
        super().__init__()
        self.seclists_url = "https://github.com/danielmiessler/SecLists/archive/master.zip"
        self.output_dir = "wordlists"
        self.zip_path = os.path.join(self.output_dir, "seclists.zip")
        self.final_path = os.path.join(self.output_dir, "seclists")
        self.test_mode = test_mode

    def run(self):
        if self.test_mode:
            self.progress.emit("Running in test mode.")
            for i in range(101):
                self.progress_percentage.emit(i)
                time.sleep(0.005) # Small delay to allow UI to update
            self.finished.emit()
            return
            
        try:
            if os.path.exists(self.final_path):
                self.progress.emit("SecLists is already installed.")
                self.finished.emit()
                return

            self.progress.emit("Creating wordlists directory...")
            os.makedirs(self.output_dir, exist_ok=True)

            self.progress.emit(f"Downloading SecLists from {self.seclists_url}...")
            response = requests.get(self.seclists_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            self.progress_percentage.emit(0)

            with open(self.zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded_size / total_size) * 100)
                            self.progress_percentage.emit(percent)

            self.progress_percentage.emit(100)
            self.progress.emit("Download complete. Extracting files...")
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                temp_extract_dir = os.path.join(self.output_dir, "_temp_extract")
                zip_ref.extractall(temp_extract_dir)

            extracted_folder = os.path.join(temp_extract_dir, os.listdir(temp_extract_dir)[0])

            self.progress.emit("Organizing files...")
            shutil.move(extracted_folder, self.final_path)

            self.progress.emit("Extraction complete. Cleaning up...")
            shutil.rmtree(temp_extract_dir)
            os.remove(self.zip_path)

            self.progress.emit(f"SecLists has been installed in: {self.final_path}")
            self.finished.emit()

        except Exception as e:
            self.progress.emit(f"Error downloading SecLists: {str(e)}")
            if os.path.exists(self.zip_path):
                os.remove(self.zip_path)
            if 'temp_extract_dir' in locals() and os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            self.finished.emit()
