import time
import requests
import os
import subprocess
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import mimetypes

class Crawler:
    """Base crawler class with common functionality"""
    def __init__(self):
        self.session = requests.Session()
        self.robots_parser = RobotFileParser()
        self.should_stop = False

    def is_allowed(self, url):
        """Check if URL is allowed by robots.txt"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            return self.robots_parser.can_fetch("*", url)
        except:
            return True

    def is_valid_file(self, url, allowed_extensions):
        """Check if URL points to allowed file type"""
        if not allowed_extensions:
            return True
        return any(url.lower().endswith(ext.lower()) for ext in allowed_extensions)

    def get_links(self, url, allowed_extensions=None):
        """Get all valid links from a page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = []

            for link in soup.find_all(['a', 'link', 'script', 'img']):
                href = link.get('href') or link.get('src')
                if href:
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)
                    if (parsed.netloc == urlparse(url).netloc and
                            self.is_allowed(full_url) and
                            self.is_valid_file(full_url, allowed_extensions)):
                        links.append(full_url)

            return links
        except Exception as e:
            print(f"Error getting links from {url}: {e}")
            return []

class FfufRunner:
    """Class for building and managing an ffuf process."""
    def __init__(self, options):
        self.options = options
        self.process = None

    def _build_command(self):
        """Build the ffuf command from the options dictionary."""
        command = ["./ffuf"]

        # URL and wordlist are mandatory
        command.extend(["-u", self.options['fuzz_template']])
        command.extend(["-w", self.options['dictionary']])

        # Add threads
        command.extend(["-t", str(self.options['threads'])])

        # Add status codes
        if self.options.get('status_codes'):
            mc = ",".join(map(str, self.options['status_codes']))
            command.extend(["-mc", mc])

        # Add other boolean flags from UI (will be implemented later)
        if self.options.get('recursion'):
            command.append("-recursion")

        # Add flags with values (will be implemented later)
        if self.options.get('recursion_depth'):
            command.extend(["-recursion-depth", str(self.options['recursion_depth'])])

        # Always use JSON output for parsing
        command.extend(["-o", "/dev/stdout", "-of", "json"])

        return command

    def run(self):
        """Runs the ffuf command and returns the process."""
        command = self._build_command()
        # Use Popen to run the command as a non-blocking subprocess
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return self.process

    def stop(self):
        """Stops the ffuf process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

class FileDownloader:
    """Class for handling file downloads"""
    def __init__(self, urls, output_dir):
        self.urls = urls
        self.output_dir = output_dir
        self.session = requests.Session()
        self.should_stop = False

    def download_file(self, url):
        """Download a single file"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = 'downloaded_file'
                
            content_type = response.headers.get('content-type', '').split(';')[0]
            ext = mimetypes.guess_extension(content_type)
            if ext:
                filename = f"{filename}{ext}"
                
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_stop:
                        return None
                    if chunk:
                        f.write(chunk)
                        
            return filepath
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None