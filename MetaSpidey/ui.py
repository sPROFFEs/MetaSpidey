import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QComboBox, QSpinBox, QFileDialog,
    QTabWidget, QFrame, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QCoreApplication
from threads import CrawlerThread, BruteForceThread, DownloadThread, DownloadWordlistThread
from metadata import MetadataExtractor

class DepthFrame(QFrame):
    """Custom frame for depth selection with explanations"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        self.title = QLabel(self.tr("Crawl Depth"))
        self.title.setStyleSheet("font-weight: bold;")
        desc = QLabel(self.tr("Controls how many levels of links the crawler will follow:"))
        desc.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(desc)

        depth_layout = QHBoxLayout()
        self.depth_combo = QComboBox()

        self.depth_levels = {
            self.tr("1 - Main page only"): self.tr("Crawls only the links found on the initial URL"),
            self.tr("2 - Main sections"): self.tr("Crawls the main page and one layer of internal links"),
            self.tr("3 - Subsections"): self.tr("Includes main sections and their subsections"),
            self.tr("4 - Deep content"): self.tr("Crawls down to more specific content and files"),
            self.tr("5 - Full crawl"): self.tr("Exhaustive crawl (can take a long time)")
        }

        self.depth_combo.addItems(self.depth_levels.keys())
        self.depth_combo.setCurrentIndex(1)

        depth_layout.addWidget(QLabel(self.tr("Level:")))
        depth_layout.addWidget(self.depth_combo)
        layout.addLayout(depth_layout)

        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.detail_label)

        self.depth_combo.currentTextChanged.connect(self.update_description)
        self.update_description(self.depth_combo.currentText())

    def update_description(self, selected_level):
        self.detail_label.setText(self.depth_levels[selected_level])

    def get_depth(self):
        # This is a bit fragile, relies on the first character being the number.
        return int(self.depth_combo.currentText().split(' ')[0])

    def tr(self, text):
        return self.main_window.tr(text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.translations = {
            "en": {
                "MetaSpidey - Advanced Web Crawler": "MetaSpidey - Advanced Web Crawler",
                "Crawl a website to discover URLs and files": "Crawl a website to discover URLs and files",
                "Start Crawling": "Start Crawling",
                "Stop": "Stop",
                "Save Results": "Save Results",
                "Crawler": "Crawler",
                "Discover URLs by brute force using a wordlist": "Discover URLs by brute force using a wordlist",
                "Download Wordlists (SecLists)": "Download Wordlists (SecLists)",
                "Start Fuzzing": "Start Fuzzing",
                "Brute Force": "Brute Force",
                "Download files from a list of URLs": "Download files from a list of URLs",
                "Start Download": "Start Download",
                "Downloader": "Downloader",
                "Extract metadata from downloaded files": "Extract metadata from downloaded files",
                "Extract Metadata": "Extract Metadata",
                "Metadata": "Metadata",
                "Crawl Depth": "Crawl Depth",
                "Language": "Language"
            },
            "es": {
                "MetaSpidey - Advanced Web Crawler": "MetaSpidey - Crawler Web Avanzado",
                "Crawl a website to discover URLs and files": "Rastrea un sitio web para descubrir URLs y archivos",
                "Start Crawling": "Iniciar Rastreo",
                "Stop": "Detener",
                "Save Results": "Guardar Resultados",
                "Crawler": "Rastreador",
                "Discover URLs by brute force using a wordlist": "Descubre URLs por fuerza bruta usando una lista de palabras",
                "Download Wordlists (SecLists)": "Descargar Listas de Palabras (SecLists)",
                "Start Fuzzing": "Iniciar Fuzzing",
                "Brute Force": "Fuerza Bruta",
                "Download files from a list of URLs": "Descargar archivos desde una lista de URLs",
                "Start Download": "Iniciar Descarga",
                "Downloader": "Descargador",
                "Extract metadata from downloaded files": "Extraer metadatos de archivos descargados",
                "Extract Metadata": "Extraer Metadatos",
                "Metadata": "Metadatos",
                "Crawl Depth": "Profundidad de Rastreo",
                "Language": "Idioma"
            }
        }
        self.current_lang = "en"


        self.setWindowTitle(self.tr("MetaSpidey - Advanced Web Crawler"))
        self.setMinimumSize(900, 700)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Language switcher
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.tr("Language"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Español"])
        self.lang_combo.currentTextChanged.connect(self.change_language)
        lang_layout.addStretch()
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)


        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.force_repaint) # Connect signal to fix rendering glitch

        # Add all tabs
        self.setup_crawler_tab()
        self.setup_brute_force_tab()
        self.setup_download_tab()
        self.setup_metadata_tab()

        self.crawler_thread = None
        self.brute_force_thread = None
        self.download_thread = None
        self.results = []

    def setup_crawler_tab(self):
        """Setup the crawler tab"""
        crawler_tab = QWidget()
        crawler_layout = QVBoxLayout(crawler_tab)

        desc = QLabel(self.tr("Crawl a website to discover URLs and files"))
        desc.setWordWrap(True)
        crawler_layout.addWidget(desc)

        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        crawler_layout.addLayout(url_layout)

        settings_layout = QHBoxLayout()
        self.depth_frame = DepthFrame(self)
        settings_layout.addWidget(self.depth_frame)

        delay_frame = QFrame()
        delay_layout = QVBoxLayout(delay_frame)
        delay_title = QLabel(self.tr("Request Delay"))
        delay_title.setStyleSheet("font-weight: bold;")
        delay_layout.addWidget(delay_title)

        delay_input_layout = QHBoxLayout()
        delay_label = QLabel(self.tr("Seconds:"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 5)
        self.delay_spin.setValue(2)
        delay_input_layout.addWidget(delay_label)
        delay_input_layout.addWidget(self.delay_spin)
        delay_layout.addLayout(delay_input_layout)
        settings_layout.addWidget(delay_frame)

        filter_frame = QFrame()
        filter_layout = QVBoxLayout(filter_frame)
        filter_title = QLabel(self.tr("File Filter"))
        filter_title.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(filter_title)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(self.tr(".pdf,.doc,.txt (empty = all)"))
        filter_layout.addWidget(self.filter_input)
        settings_layout.addWidget(filter_frame)

        # Threads control
        threads_frame = QFrame()
        threads_layout = QVBoxLayout(threads_frame)
        threads_title = QLabel(self.tr("Concurrency"))
        threads_title.setStyleSheet("font-weight: bold;")
        threads_layout.addWidget(threads_title)

        threads_input_layout = QHBoxLayout()
        threads_label = QLabel(self.tr("Threads:"))
        self.crawler_threads_spin = QSpinBox()
        self.crawler_threads_spin.setRange(1, 50)
        self.crawler_threads_spin.setValue(10)
        threads_input_layout.addWidget(threads_label)
        threads_input_layout.addWidget(self.crawler_threads_spin)
        threads_layout.addLayout(threads_input_layout)
        settings_layout.addWidget(threads_frame)

        crawler_layout.addLayout(settings_layout)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        crawler_layout.addWidget(self.progress_text)

        self.progress_bar = QProgressBar()
        crawler_layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton(self.tr("Start Crawling"))
        self.start_button.clicked.connect(self.start_crawling)
        self.stop_button = QPushButton(self.tr("Stop"))
        self.stop_button.clicked.connect(self.stop_crawling)
        self.stop_button.setEnabled(False)
        self.save_button = QPushButton(self.tr("Save Results"))
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        crawler_layout.addLayout(button_layout)

        self.tabs.addTab(crawler_tab, self.tr("Crawler"))

    def setup_brute_force_tab(self):
        """Setup the brute force discovery tab"""
        brute_tab = QWidget()
        brute_layout = QVBoxLayout(brute_tab)

        desc = QLabel(self.tr("Discover URLs by brute force using a wordlist"))
        desc.setWordWrap(True)
        brute_layout.addWidget(desc)

        url_layout = QHBoxLayout()
        url_label = QLabel(self.tr("Fuzzing Target (use FUZZ):"))
        self.brute_url_input = QLineEdit()
        self.brute_url_input.setPlaceholderText("https://example.com/FUZZ or https://FUZZ.example.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.brute_url_input)
        brute_layout.addLayout(url_layout)

        dict_layout = QHBoxLayout()
        dict_label = QLabel(self.tr("Wordlist:"))
        self.dict_path_input = QLineEdit()
        self.dict_path_input.setPlaceholderText(self.tr("Select wordlist file..."))
        dict_button = QPushButton(self.tr("Browse..."))
        dict_button.clicked.connect(self.select_dictionary)
        dict_layout.addWidget(dict_label)
        dict_layout.addWidget(self.dict_path_input)
        dict_layout.addWidget(dict_button)
        brute_layout.addLayout(dict_layout)

        # --- FFUF Settings Group (Refactored) ---
        ffuf_settings_group = QGroupBox(self.tr("FFUF Settings"))
        ffuf_settings_layout = QVBoxLayout()

        top_settings_layout = QHBoxLayout()
        threads_label = QLabel(self.tr("Threads:"))
        self.brute_threads_spin = QSpinBox()
        self.brute_threads_spin.setRange(1, 200)
        self.brute_threads_spin.setValue(40)
        top_settings_layout.addWidget(threads_label)
        top_settings_layout.addWidget(self.brute_threads_spin)
        top_settings_layout.addStretch()

        self.status_codes_group = QGroupBox(self.tr("Status Codes (-mc)"))
        status_codes_layout = QHBoxLayout()
        self.status_code_boxes = {
            '200': QCheckBox("200"), '204': QCheckBox("204"), '301': QCheckBox("301"),
            '302': QCheckBox("302"), '307': QCheckBox("307"), '401': QCheckBox("401"),
            '403': QCheckBox("403"), '500': QCheckBox("500"),
        }
        self.status_code_boxes['200'].setChecked(True)
        # Check a few common ones by default
        self.status_code_boxes['301'].setChecked(True)
        self.status_code_boxes['302'].setChecked(True)
        self.status_code_boxes['307'].setChecked(True)
        self.status_code_boxes['403'].setChecked(True)
        for box in self.status_code_boxes.values():
            status_codes_layout.addWidget(box)
        self.status_codes_group.setLayout(status_codes_layout)
        top_settings_layout.addWidget(self.status_codes_group)
        ffuf_settings_layout.addLayout(top_settings_layout)

        ffuf_options_group = QGroupBox(self.tr("FFUF Options"))
        ffuf_options_layout = QHBoxLayout()
        self.recursion_check = QCheckBox(self.tr("-recursion"))
        self.recursion_check.setToolTip(self.tr("Enable recursion. Ffuf will find new directories and start fuzzing them."))
        ffuf_options_layout.addWidget(self.recursion_check)
        recursion_depth_label = QLabel(self.tr("-recursion-depth:"))
        self.recursion_depth_spin = QSpinBox()
        self.recursion_depth_spin.setRange(1, 10)
        self.recursion_depth_spin.setValue(2)
        self.recursion_depth_spin.setToolTip(self.tr("Maximum recursion depth."))
        ffuf_options_layout.addWidget(recursion_depth_label)
        ffuf_options_layout.addWidget(self.recursion_depth_spin)
        ffuf_options_group.setLayout(ffuf_options_layout)
        ffuf_settings_layout.addWidget(ffuf_options_group)

        self.download_wordlist_button = QPushButton(self.tr("Download Wordlists (SecLists)"))
        self.download_wordlist_button.setToolTip(self.tr("Downloads the SecLists wordlist collection (~400MB)."))
        self.download_wordlist_button.clicked.connect(self.start_wordlist_download)
        ffuf_settings_layout.addWidget(self.download_wordlist_button)
        
        ffuf_settings_group.setLayout(ffuf_settings_layout)
        brute_layout.addWidget(ffuf_settings_group)

        urls_group = QGroupBox(self.tr("Found URLs"))
        urls_layout = QVBoxLayout()
        self.urls_list = QTextEdit()
        self.urls_list.setReadOnly(True)
        self.urls_list.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #00ff00; font-family: monospace; }")
        urls_layout.addWidget(self.urls_list)
        urls_group.setLayout(urls_layout)
        brute_layout.addWidget(urls_group)

        progress_group = QGroupBox(self.tr("Process Status"))
        progress_layout = QVBoxLayout()
        self.brute_progress_text = QTextEdit()
        self.brute_progress_text.setReadOnly(True)
        self.brute_progress_text.setMaximumHeight(100)
        progress_layout.addWidget(self.brute_progress_text)

        self.brute_progress_bar = QProgressBar()
        self.brute_progress_bar.setTextVisible(True)
        self.brute_progress_bar.setFormat(self.tr("%p% Complete"))
        progress_layout.addWidget(self.brute_progress_bar)
        progress_group.setLayout(progress_layout)
        brute_layout.addWidget(progress_group)

        button_layout = QHBoxLayout()
        self.brute_start_button = QPushButton(self.tr("Start Fuzzing"))
        self.brute_start_button.clicked.connect(self.start_brute_force)
        self.brute_stop_button = QPushButton(self.tr("Stop"))
        self.brute_stop_button.clicked.connect(self.stop_brute_force)
        self.brute_stop_button.setEnabled(False)
        self.brute_save_button = QPushButton(self.tr("Save Results"))
        self.brute_save_button.clicked.connect(self.save_brute_results)
        self.brute_save_button.setEnabled(False)

        button_layout.addWidget(self.brute_start_button)
        button_layout.addWidget(self.brute_stop_button)
        button_layout.addWidget(self.brute_save_button)
        brute_layout.addLayout(button_layout)

        self.tabs.addTab(brute_tab, self.tr("Brute Force"))

    def force_repaint(self):
        """Force the window to repaint to fix rendering glitches."""
        self.repaint()

    def start_brute_force(self):
        fuzz_template = self.brute_url_input.text().strip()
        dictionary = self.dict_path_input.text().strip()
        if not fuzz_template or not dictionary:
            self.brute_progress_text.append(self.tr("Please complete all fields"))
            return
        if "FUZZ" not in fuzz_template:
            self.brute_progress_text.append(self.tr("Fuzzing target must contain the 'FUZZ' keyword"))
            return
        status_codes = [int(code) for code, box in self.status_code_boxes.items() if box.isChecked()]
        options = {
            'fuzz_template': fuzz_template, 'dictionary': dictionary, 'threads': self.brute_threads_spin.value(),
            'status_codes': status_codes, 'recursion': self.recursion_check.isChecked(),
            'recursion_depth': self.recursion_depth_spin.value() if self.recursion_check.isChecked() else None,
        }
        self.brute_progress_text.clear()
        self.urls_list.clear()
        self.brute_progress_bar.setValue(0)
        self.brute_start_button.setEnabled(False)
        self.brute_stop_button.setEnabled(True)
        self.brute_save_button.setEnabled(False)
        self.brute_force_thread = BruteForceThread(options)
        self.brute_force_thread.progress.connect(self.update_brute_progress)
        self.brute_force_thread.url_found.connect(self.add_found_url)
        self.brute_force_thread.status.connect(self.update_brute_status)
        self.brute_force_thread.finished.connect(self.brute_force_finished)
        self.brute_force_thread.start()

    def start_wordlist_download(self):
        self.download_wordlist_button.setEnabled(False)
        self.brute_progress_text.append(self.tr("Starting SecLists download..."))
        self.wordlist_download_thread = DownloadWordlistThread()
        self.wordlist_download_thread.progress.connect(self.update_brute_progress)
        self.wordlist_download_thread.progress_percentage.connect(self.brute_progress_bar.setValue)
        self.wordlist_download_thread.finished.connect(self.wordlist_download_finished)
        self.wordlist_download_thread.start()

    def wordlist_download_finished(self):
        self.download_wordlist_button.setEnabled(True)
        self.brute_progress_text.append(self.tr("Wordlist download process finished."))
        self.brute_progress_bar.setValue(0) # Reset bar

    def setup_download_tab(self):
        """Setup the file download tab"""
        download_tab = QWidget()
        download_layout = QVBoxLayout(download_tab)

        desc = QLabel(self.tr("Download files from a list of URLs"))
        desc.setWordWrap(True)
        download_layout.addWidget(desc)

        url_file_layout = QHBoxLayout()
        url_file_label = QLabel(self.tr("URL File:"))
        self.url_file_input = QLineEdit()
        self.url_file_input.setPlaceholderText(self.tr("Select file with URLs..."))
        url_file_button = QPushButton(self.tr("Browse..."))
        url_file_button.clicked.connect(self.select_url_file)
        url_file_layout.addWidget(url_file_label)
        url_file_layout.addWidget(self.url_file_input)
        url_file_layout.addWidget(url_file_button)
        download_layout.addLayout(url_file_layout)

        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel(self.tr("Output Directory:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(self.tr("Select output directory..."))
        output_dir_button = QPushButton(self.tr("Browse..."))
        output_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_button)
        download_layout.addLayout(output_dir_layout)

        self.download_progress_text = QTextEdit()
        self.download_progress_text.setReadOnly(True)
        download_layout.addWidget(self.download_progress_text)

        self.download_progress_bar = QProgressBar()
        download_layout.addWidget(self.download_progress_bar)

        button_layout = QHBoxLayout()
        self.download_start_button = QPushButton(self.tr("Start Download"))
        self.download_start_button.clicked.connect(self.start_download)
        self.download_stop_button = QPushButton(self.tr("Stop"))
        self.download_stop_button.clicked.connect(self.stop_download)
        self.download_stop_button.setEnabled(False)

        button_layout.addWidget(self.download_start_button)
        button_layout.addWidget(self.download_stop_button)
        download_layout.addLayout(button_layout)

        self.tabs.addTab(download_tab, self.tr("Downloader"))

    def setup_metadata_tab(self):
        """Setup the metadata extraction tab"""
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)

        desc = QLabel(self.tr("Extract metadata from downloaded files"))
        desc.setWordWrap(True)
        metadata_layout.addWidget(desc)

        input_dir_layout = QHBoxLayout()
        input_dir_label = QLabel(self.tr("Input Directory:"))
        self.metadata_input_dir = QLineEdit()
        self.metadata_input_dir.setPlaceholderText(self.tr("Select directory with files..."))
        input_dir_button = QPushButton(self.tr("Browse..."))
        input_dir_button.clicked.connect(self.select_metadata_input_dir)
        input_dir_layout.addWidget(input_dir_label)
        input_dir_layout.addWidget(self.metadata_input_dir)
        input_dir_layout.addWidget(input_dir_button)
        metadata_layout.addLayout(input_dir_layout)

        output_file_layout = QHBoxLayout()
        output_file_label = QLabel(self.tr("Output File:"))
        self.metadata_output_file = QLineEdit()
        self.metadata_output_file.setPlaceholderText(self.tr("Output file for metadata..."))
        output_file_button = QPushButton(self.tr("Save As..."))
        output_file_button.clicked.connect(self.select_metadata_output_file)
        output_file_layout.addWidget(output_file_label)
        output_file_layout.addWidget(self.metadata_output_file)
        output_file_layout.addWidget(output_file_button)
        metadata_layout.addLayout(output_file_layout)

        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        metadata_layout.addWidget(self.metadata_text)

        self.extract_button = QPushButton(self.tr("Extract Metadata"))
        self.extract_button.clicked.connect(self.extract_metadata)
        metadata_layout.addWidget(self.extract_button)

        self.tabs.addTab(metadata_tab, self.tr("Metadata"))

    # File dialogs
    def select_dictionary(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Wordlist"), "", self.tr("Text files (*.txt);;All files (*)"))
        if filename:
            self.dict_path_input.setText(filename)

    def select_url_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select URL File"), "", self.tr("Text files (*.txt);;All files (*)"))
        if filename:
            self.url_file_input.setText(filename)

    def select_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"))
        if dirname:
            self.output_dir_input.setText(dirname)

    def select_metadata_input_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, self.tr("Select Input Directory"))
        if dirname:
            self.metadata_input_dir.setText(dirname)

    def select_metadata_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Metadata"), "", self.tr("JSON files (*.json);;All files (*)"))
        if filename:
            self.metadata_output_file.setText(filename)

    # Crawler methods
    def start_crawling(self):
        url = self.url_input.text().strip()
        if not url:
            self.progress_text.append(self.tr("Please enter a URL"))
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        extensions = [ext.strip() for ext in self.filter_input.text().split(',') if ext.strip()]

        self.progress_text.clear()
        self.progress_bar.setRange(0, 0)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)

        self.crawler_thread = CrawlerThread(
            url,
            self.depth_frame.get_depth(),
            self.delay_spin.value(),
            extensions,
            self.crawler_threads_spin.value()
        )
        self.crawler_thread.progress.connect(self.update_progress)
        self.crawler_thread.url_found.connect(self.update_progress) # Connect the new signal
        self.crawler_thread.finished.connect(self.crawling_finished)
        self.crawler_thread.start()

    def stop_crawling(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.crawler_thread.wait()
            self.progress_text.append(self.tr("Crawling stopped by user"))
            self.crawling_finished([])

    def update_progress(self, message):
        self.progress_text.append(message)

    def crawling_finished(self, results):
        self.results = results
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)

        self.progress_text.append(self.tr("\nCrawling finished. Found {n} URLs").format(n=len(results)))

    def save_results(self):
        if not self.results:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Results"), "", self.tr("Text files (*.txt);;All files (*)"))

        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for url in self.results:
                        f.write(f"{url}\n")
                self.progress_text.append(self.tr("Results saved to {file_name}").format(file_name=file_name))
            except Exception as e:
                self.progress_text.append(self.tr("Error saving results: {error}").format(error=str(e)))

    # Brute force methods
    def stop_brute_force(self):
        if self.brute_force_thread and self.brute_force_thread.isRunning():
            self.brute_force_thread.stop()
            self.brute_force_thread.wait()
            self.brute_progress_text.append(self.tr("Fuzzing stopped by user"))
            self.brute_force_finished([])

    def update_brute_progress(self, message):
        self.brute_progress_text.append(message)

    def add_found_url(self, url):
        """Add found URL to the list"""
        self.urls_list.append(url)
        self.urls_list.verticalScrollBar().setValue(
            self.urls_list.verticalScrollBar().maximum()
        )
    
    def update_brute_status(self, status):
        """Update progress bar and status text"""
        # The progress bar is not updated from status text anymore to prevent crashes.
        # It could be updated by a separate signal if more granular progress is needed.
        self.brute_progress_text.setText(status)

    def brute_force_finished(self, results):
        self.brute_results = results
        self.brute_progress_bar.setValue(100)
        self.brute_start_button.setEnabled(True)
        self.brute_stop_button.setEnabled(False)
        self.brute_save_button.setEnabled(True)
        
        total_found = len(results)
        self.brute_progress_text.append(
            self.tr("\nFuzzing finished. Found {n} URLs").format(n=total_found)
        )
        
        if total_found > 0:
            self.urls_list.append(self.tr("\nSummary of found URLs:"))
            for url in results:
                self.urls_list.append(f"[*] {url}")

    def save_brute_results(self):
        if not hasattr(self, 'brute_results'):
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Results"), "", self.tr("Text files (*.txt);;All files (*)"))
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for url in self.brute_results:
                        f.write(f"{url}\n")
                self.brute_progress_text.append(self.tr("Results saved to {file_name}").format(file_name=file_name))
            except Exception as e:
                self.brute_progress_text.append(self.tr("Error saving results: {error}").format(error=str(e)))

    # Download methods
    def start_download(self):
        url_file = self.url_file_input.text().strip()
        output_dir = self.output_dir_input.text().strip()

        if not url_file or not output_dir:
            self.progress_text.append(self.tr("Please complete all fields"))
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.download_progress_text.append(self.tr("Error creating output directory: {error}").format(error=str(e)))
                return

        try:
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.download_progress_text.append(self.tr("Error reading URL file: {error}").format(error=str(e)))
            return

        self.download_progress_text.clear()
        self.download_progress_bar.setRange(0, len(urls))
        self.download_start_button.setEnabled(False)
        self.download_stop_button.setEnabled(True)

        self.download_thread = DownloadThread(urls, output_dir)
        self.download_thread.progress.connect(self.update_download_progress)
        self.download_thread.file_downloaded.connect(self.file_downloaded)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def stop_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
            self.download_progress_text.append(self.tr("Download stopped by user"))
            self.download_finished([])

    def update_download_progress(self, message):
        self.download_progress_text.append(message)

    def file_downloaded(self, filepath):
        self.download_progress_bar.setValue(self.download_progress_bar.value() + 1)

    def download_finished(self, downloaded_files):
        self.download_start_button.setEnabled(True)
        self.download_stop_button.setEnabled(False)
        self.download_progress_text.append(
            self.tr("\nDownload finished. {n} files downloaded").format(n=len(downloaded_files))
        )

    def extract_metadata(self):
        input_dir = self.metadata_input_dir.text().strip()
        output_file = self.metadata_output_file.text().strip()

        if not input_dir or not output_file:
            self.metadata_text.append(self.tr("Please complete all fields"))
            return

        if not os.path.exists(input_dir):
            self.metadata_text.append(self.tr("Input directory does not exist"))
            return

        self.metadata_text.clear()
        self.metadata_text.append(self.tr("Starting metadata extraction..."))
        
        try:
            metadata_extractor = MetadataExtractor()
            all_metadata = {}
            
            total_files = sum([len(files) for _, _, files in os.walk(input_dir)])
            processed = 0

            for root, _, files in os.walk(input_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    self.metadata_text.append(self.tr("Processing: {filename}").format(filename=filename))
                    
                    metadata = metadata_extractor.extract_metadata(filepath)
                    if metadata:
                        all_metadata[filepath] = metadata
                        
                    processed += 1
                    self.metadata_text.append(self.tr("Progress: {processed}/{total_files}").format(processed=processed, total_files=total_files))

            if all_metadata:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_metadata, f, indent=2, ensure_ascii=False)

                self.metadata_text.append(self.tr("\nMetadata saved to: {output_file}").format(output_file=output_file))
                self.metadata_text.append(self.tr("\nSummary of found metadata:"))
                
                for filepath, metadata in all_metadata.items():
                    self.metadata_text.append(self.tr("\nFile: {filename}").format(filename=os.path.basename(filepath)))
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float)):
                            self.metadata_text.append(f"  {key}: {value}")
            else:
                self.metadata_text.append(self.tr("\nNo metadata found in files"))

        except Exception as e:
            self.metadata_text.append(self.tr("Error extracting metadata: {error}").format(error=str(e)))

    def change_language(self, lang_text):
        self.current_lang = "es" if lang_text == "Español" else "en"
        self.retranslate_ui()

    def retranslate_ui(self):
        # Window Title
        self.setWindowTitle(self.tr("MetaSpidey - Advanced Web Crawler"))

        # Language switcher
        self.lang_label.setText(self.tr("Language"))

        # --- Crawler Tab ---
        self.tabs.setTabText(0, self.tr("Crawler"))
        self.start_button.setText(self.tr("Start Crawling"))
        self.stop_button.setText(self.tr("Stop"))
        self.save_button.setText(self.tr("Save Results"))
        
        # --- Brute Force Tab ---
        self.tabs.setTabText(1, self.tr("Brute Force"))
        self.download_wordlist_button.setText(self.tr("Download Wordlists (SecLists)"))
        self.brute_start_button.setText(self.tr("Start Fuzzing"))
        self.brute_stop_button.setText(self.tr("Stop"))
        self.brute_save_button.setText(self.tr("Save Results"))
        
        # --- Downloader Tab ---
        self.tabs.setTabText(2, self.tr("Downloader"))
        self.download_start_button.setText(self.tr("Start Download"))
        self.download_stop_button.setText(self.tr("Stop"))

        # --- Metadata Tab ---
        self.tabs.setTabText(3, self.tr("Metadata"))
        self.extract_button.setText(self.tr("Extract Metadata"))
        
        # --- Depth Frame ---
        self.depth_frame.title.setText(self.tr("Crawl Depth"))


    def tr(self, text):
        return self.translations[self.current_lang].get(text, text)