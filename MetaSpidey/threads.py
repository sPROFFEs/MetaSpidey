from PyQt6.QtCore import QThread, pyqtSignal
from crawlers import Crawler, BruteForcer, FileDownloader
from urllib.parse import urljoin  # Añadida esta importación
import time

class CrawlerThread(QThread):
    progress = pyqtSignal(str)
    url_found = pyqtSignal(str, int)
    finished = pyqtSignal(list)

    def __init__(self, url, max_depth, delay, extensions):
        super().__init__()
        self.url = url
        self.max_depth = max_depth
        self.delay = delay
        self.extensions = extensions
        self.crawler = Crawler()

    def crawl(self, url, depth=0):
        if (url in self.crawler.visited_urls or
                depth >= self.max_depth or
                self.crawler.should_stop):
            return

        self.progress.emit(f"Nivel {depth + 1}: Rastreando {url}")
        self.url_found.emit(url, depth)
        self.crawler.visited_urls.add(url)

        links = self.crawler.get_links(url, self.extensions)
        time.sleep(self.delay)

        for link in links:
            self.crawl(link, depth + 1)

    def run(self):
        try:
            self.crawl(self.url)
            self.finished.emit(list(self.crawler.visited_urls))
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.finished.emit([])

    def stop(self):
        self.crawler.should_stop = True

class BruteForceThread(QThread):
    progress = pyqtSignal(str)
    url_found = pyqtSignal(str)  # Señal para cada URL encontrada
    status = pyqtSignal(str)     # Señal para actualizaciones de estado
    finished = pyqtSignal(list)

    def __init__(self, url, dictionary_file):
        super().__init__()
        self.brute_forcer = BruteForcer(url, dictionary_file)
        self.total_lines = self.count_dictionary_lines(dictionary_file)
        self.processed_lines = 0

    def count_dictionary_lines(self, dictionary_file):
        """Contar el número total de líneas en el diccionario"""
        try:
            with open(dictionary_file, 'r') as f:
                return sum(1 for line in f)
        except Exception:
            return 0

    def stop(self):
        """Detener el proceso de fuerza bruta"""
        if self.brute_forcer:
            self.brute_forcer.should_stop = True
        self.progress.emit("Deteniendo el proceso de fuerza bruta...")

    def run(self):
        try:
            discovered_urls = []
            with open(self.brute_forcer.dictionary_file, 'r') as f:
                for line in f:
                    if self.brute_forcer.should_stop:
                        break
                    
                    self.processed_lines += 1
                    path = line.strip()
                    if not path:
                        continue
                    
                    url = urljoin(self.brute_forcer.base_url, path)
                    try:
                        # Emitir el progreso actual
                        progress_percent = (self.processed_lines / self.total_lines) * 100
                        self.status.emit(f"Progreso: {progress_percent:.1f}% ({self.processed_lines}/{self.total_lines})")
                        
                        response = self.brute_forcer.session.head(url, allow_redirects=True, timeout=5)
                        if response.status_code == 200:
                            discovered_urls.append(url)
                            # Emitir la URL encontrada
                            self.url_found.emit(f"[+] URL encontrada: {url} (Código: {response.status_code})")
                    except Exception as e:
                        self.progress.emit(f"Error al probar {url}: {str(e)}")
                    
                    time.sleep(0.1)  # Ser amable con el servidor
            
            self.finished.emit(discovered_urls)
            
        except Exception as e:
            self.progress.emit(f"Error en fuerza bruta: {str(e)}")
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
            
            self.progress.emit(f"Descargando {url}")
            filepath = self.downloader.download_file(url)
            if filepath:
                downloaded_files.append(filepath)
                self.file_downloaded.emit(filepath)

        self.finished.emit(downloaded_files)

    def stop(self):
        self.downloader.should_stop = True
