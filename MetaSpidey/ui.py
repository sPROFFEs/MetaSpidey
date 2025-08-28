import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QComboBox, QSpinBox, QFileDialog,
    QTabWidget, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from threads import CrawlerThread, BruteForceThread, DownloadThread, DownloadWordlistThread
from metadata import MetadataExtractor

class DepthFrame(QFrame):
    """Custom frame for depth selection with explanations"""
    selectionChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Profundidad de Rastreo")
        title.setStyleSheet("font-weight: bold;")
        desc = QLabel("Controla cuántos niveles de enlaces seguirá el crawler:")
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(desc)

        depth_layout = QHBoxLayout()
        self.depth_combo = QComboBox()

        self.depth_levels = {
            "1 - Solo página principal": "Rastrea solo los enlaces encontrados en la URL inicial",
            "2 - Secciones principales": "Rastrea la página principal y una capa de enlaces internos",
            "3 - Subsecciones": "Incluye secciones principales y sus subsecciones",
            "4 - Contenido profundo": "Rastrea hasta contenido más específico y archivos",
            "5 - Rastreo completo": "Rastreo exhaustivo (puede llevar mucho tiempo)"
        }

        self.depth_combo.addItems(self.depth_levels.keys())
        self.depth_combo.setCurrentIndex(1)

        depth_layout.addWidget(QLabel("Nivel:"))
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
        self.selectionChanged.emit()

    def get_depth(self):
        return int(self.depth_combo.currentText()[0])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetaSpidey - Advanced Web Crawler")
        self.setMinimumSize(900, 700)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

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

        # Description
        desc = QLabel("Rastrear un sitio web para descubrir URLs y archivos")
        desc.setWordWrap(True)
        crawler_layout.addWidget(desc)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://ejemplo.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        crawler_layout.addLayout(url_layout)

        # Settings
        settings_layout = QHBoxLayout()
        self.depth_frame = DepthFrame()
        self.depth_frame.selectionChanged.connect(self.force_repaint)
        settings_layout.addWidget(self.depth_frame)

        # Delay control
        delay_frame = QFrame()
        delay_layout = QVBoxLayout(delay_frame)
        delay_title = QLabel("Retardo entre solicitudes")
        delay_title.setStyleSheet("font-weight: bold;")
        delay_layout.addWidget(delay_title)

        delay_input_layout = QHBoxLayout()
        delay_label = QLabel("Segundos:")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 5)
        self.delay_spin.setValue(2)
        delay_input_layout.addWidget(delay_label)
        delay_input_layout.addWidget(self.delay_spin)
        delay_layout.addLayout(delay_input_layout)
        settings_layout.addWidget(delay_frame)

        # File filter
        filter_frame = QFrame()
        filter_layout = QVBoxLayout(filter_frame)
        filter_title = QLabel("Filtro de archivos")
        filter_title.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(filter_title)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(".pdf,.doc,.txt (vacío = todos)")
        filter_layout.addWidget(self.filter_input)
        settings_layout.addWidget(filter_frame)

        crawler_layout.addLayout(settings_layout)

        # Progress display
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        crawler_layout.addWidget(self.progress_text)

        self.progress_bar = QProgressBar()
        crawler_layout.addWidget(self.progress_bar)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Rastreo")
        self.start_button.clicked.connect(self.start_crawling)
        self.stop_button = QPushButton("Detener")
        self.stop_button.clicked.connect(self.stop_crawling)
        self.stop_button.setEnabled(False)
        self.save_button = QPushButton("Guardar Resultados")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        crawler_layout.addLayout(button_layout)

        self.tabs.addTab(crawler_tab, "Rastreo")

    def setup_brute_force_tab(self):
        """Setup the brute force discovery tab"""
        brute_tab = QWidget()
        brute_layout = QVBoxLayout(brute_tab)

        # Description
        desc = QLabel("Descubrir URLs mediante fuerza bruta usando un diccionario")
        desc.setWordWrap(True)
        brute_layout.addWidget(desc)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL Base:")
        self.brute_url_input = QLineEdit()
        self.brute_url_input.setPlaceholderText("https://ejemplo.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.brute_url_input)
        brute_layout.addLayout(url_layout)

        # Dictionary file selection
        dict_layout = QHBoxLayout()
        dict_label = QLabel("Diccionario:")
        self.dict_path_input = QLineEdit()
        self.dict_path_input.setPlaceholderText("Seleccione archivo de diccionario...")
        dict_button = QPushButton("Examinar")
        dict_button.clicked.connect(self.select_dictionary)
        dict_layout.addWidget(dict_label)
        dict_layout.addWidget(self.dict_path_input)
        dict_layout.addWidget(dict_button)
        brute_layout.addLayout(dict_layout)

        # URLs encontradas
        urls_group = QGroupBox("URLs Encontradas")
        urls_layout = QVBoxLayout()
        
        # Lista de URLs encontradas
        self.urls_list = QTextEdit()
        self.urls_list.setReadOnly(True)
        self.urls_list.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: monospace;
            }
        """)
        urls_layout.addWidget(self.urls_list)
        urls_group.setLayout(urls_layout)
        brute_layout.addWidget(urls_group)

        # Progress display
        progress_group = QGroupBox("Estado del Proceso")
        progress_layout = QVBoxLayout()
        
        self.brute_progress_text = QTextEdit()
        self.brute_progress_text.setReadOnly(True)
        self.brute_progress_text.setMaximumHeight(100)
        progress_layout.addWidget(self.brute_progress_text)

        self.brute_progress_bar = QProgressBar()
        self.brute_progress_bar.setTextVisible(True)
        self.brute_progress_bar.setFormat("%p% Completado")
        progress_layout.addWidget(self.brute_progress_bar)
        
        progress_group.setLayout(progress_layout)
        brute_layout.addWidget(progress_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.brute_start_button = QPushButton("Iniciar Búsqueda")
        self.brute_start_button.clicked.connect(self.start_brute_force)
        self.brute_stop_button = QPushButton("Detener")
        self.brute_stop_button.clicked.connect(self.stop_brute_force)
        self.brute_stop_button.setEnabled(False)
        self.brute_save_button = QPushButton("Guardar Resultados")
        self.brute_save_button.clicked.connect(self.save_brute_results)
        self.brute_save_button.setEnabled(False)

        button_layout.addWidget(self.brute_start_button)
        button_layout.addWidget(self.brute_stop_button)
        button_layout.addWidget(self.brute_save_button)
        brute_layout.addLayout(button_layout)

        self.download_wordlist_button = QPushButton("Descargar Wordlists (SecLists)")
        self.download_wordlist_button.setToolTip("Descarga la colección de wordlists de SecLists (~400MB).")
        self.download_wordlist_button.clicked.connect(self.start_wordlist_download)
        brute_layout.addWidget(self.download_wordlist_button)

        self.tabs.addTab(brute_tab, "Fuerza Bruta")

    def setup_download_tab(self):
        """Setup the file download tab"""
        download_tab = QWidget()
        download_layout = QVBoxLayout(download_tab)

        # Description
        desc = QLabel("Descargar archivos desde una lista de URLs")
        desc.setWordWrap(True)
        download_layout.addWidget(desc)

        # URL list file selection
        url_file_layout = QHBoxLayout()
        url_file_label = QLabel("Archivo de URLs:")
        self.url_file_input = QLineEdit()
        self.url_file_input.setPlaceholderText("Seleccione archivo con URLs...")
        url_file_button = QPushButton("Examinar")
        url_file_button.clicked.connect(self.select_url_file)
        url_file_layout.addWidget(url_file_label)
        url_file_layout.addWidget(self.url_file_input)
        url_file_layout.addWidget(url_file_button)
        download_layout.addLayout(url_file_layout)

        # Output directory selection
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("Directorio de salida:")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Seleccione directorio de salida...")
        output_dir_button = QPushButton("Examinar")
        output_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_button)
        download_layout.addLayout(output_dir_layout)

        # Progress display
        self.download_progress_text = QTextEdit()
        self.download_progress_text.setReadOnly(True)
        download_layout.addWidget(self.download_progress_text)

        self.download_progress_bar = QProgressBar()
        download_layout.addWidget(self.download_progress_bar)

        # Control buttons
        button_layout = QHBoxLayout()
        self.download_start_button = QPushButton("Iniciar Descarga")
        self.download_start_button.clicked.connect(self.start_download)
        self.download_stop_button = QPushButton("Detener")
        self.download_stop_button.clicked.connect(self.stop_download)
        self.download_stop_button.setEnabled(False)

        button_layout.addWidget(self.download_start_button)
        button_layout.addWidget(self.download_stop_button)
        download_layout.addLayout(button_layout)

        self.tabs.addTab(download_tab, "Descargas")

    def setup_metadata_tab(self):
        """Setup the metadata extraction tab"""
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)

        # Description
        desc = QLabel("Extraer metadatos de archivos descargados")
        desc.setWordWrap(True)
        metadata_layout.addWidget(desc)

        # Input directory selection
        input_dir_layout = QHBoxLayout()
        input_dir_label = QLabel("Directorio de entrada:")
        self.metadata_input_dir = QLineEdit()
        self.metadata_input_dir.setPlaceholderText("Seleccione directorio con archivos...")
        input_dir_button = QPushButton("Examinar")
        input_dir_button.clicked.connect(self.select_metadata_input_dir)
        input_dir_layout.addWidget(input_dir_label)
        input_dir_layout.addWidget(self.metadata_input_dir)
        input_dir_layout.addWidget(input_dir_button)
        metadata_layout.addLayout(input_dir_layout)

        # Output file selection
        output_file_layout = QHBoxLayout()
        output_file_label = QLabel("Archivo de salida:")
        self.metadata_output_file = QLineEdit()
        self.metadata_output_file.setPlaceholderText("Archivo de salida para metadatos...")
        output_file_button = QPushButton("Guardar Como")
        output_file_button.clicked.connect(self.select_metadata_output_file)
        output_file_layout.addWidget(output_file_label)
        output_file_layout.addWidget(self.metadata_output_file)
        output_file_layout.addWidget(output_file_button)
        metadata_layout.addLayout(output_file_layout)

        # Results display
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        metadata_layout.addWidget(self.metadata_text)

        # Extract button
        self.extract_button = QPushButton("Extraer Metadatos")
        self.extract_button.clicked.connect(self.extract_metadata)
        metadata_layout.addWidget(self.extract_button)

        self.tabs.addTab(metadata_tab, "Metadatos")

    # File dialogs
    def select_dictionary(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Diccionario", "", "Archivos de texto (*.txt);;Todos los archivos (*)")
        if filename:
            self.dict_path_input.setText(filename)

    def select_url_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de URLs", "", "Archivos de texto (*.txt);;Todos los archivos (*)")
        if filename:
            self.url_file_input.setText(filename)

    def select_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Salida")
        if dirname:
            self.output_dir_input.setText(dirname)

    def select_metadata_input_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Entrada")
        if dirname:
            self.metadata_input_dir.setText(dirname)

    def select_metadata_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Metadatos", "", "Archivos JSON (*.json);;Todos los archivos (*)")
        if filename:
            self.metadata_output_file.setText(filename)

    # Crawler methods
    def start_crawling(self):
        url = self.url_input.text().strip()
        if not url:
            self.progress_text.append("Por favor, ingrese una URL")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        extensions = [ext.strip() for ext in self.filter_input.text().split(',') if ext.strip()]

        self.progress_text.clear()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)

        self.crawler_thread = CrawlerThread(
            url,
            self.depth_frame.get_depth(),
            self.delay_spin.value(),
            extensions
        )
        self.crawler_thread.progress.connect(self.update_progress)
        self.crawler_thread.finished.connect(self.crawling_finished)
        self.crawler_thread.start()

    def stop_crawling(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.crawler_thread.wait()
            self.progress_text.append("Rastreo detenido por el usuario")
            self.crawling_finished([])

    def update_progress(self, message):
        self.progress_text.append(message)

    def force_repaint(self):
        """Force the window to repaint to fix rendering glitches."""
        self.repaint()

    def crawling_finished(self, results):
        self.results = results
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)

        self.progress_text.append(f"\nRastreo finalizado. Se encontraron {len(results)} URLs")

    def save_results(self):
        if not self.results:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Resultados",
            "",
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )

        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for url in self.results:
                        f.write(f"{url}\n")
                self.progress_text.append(f"Resultados guardados en {file_name}")
            except Exception as e:
                self.progress_text.append(f"Error al guardar resultados: {str(e)}")

    # Brute force methods
    def start_brute_force(self):
        url = self.brute_url_input.text().strip()
        dictionary = self.dict_path_input.text().strip()

        if not url or not dictionary:
            self.brute_progress_text.append("Por favor, complete todos los campos")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.brute_progress_text.clear()
        self.urls_list.clear()
        self.brute_progress_bar.setValue(0)
        self.brute_start_button.setEnabled(False)
        self.brute_stop_button.setEnabled(True)
        self.brute_save_button.setEnabled(False)

        self.brute_force_thread = BruteForceThread(url, dictionary)
        self.brute_force_thread.progress.connect(self.update_brute_progress)
        self.brute_force_thread.url_found.connect(self.add_found_url)
        self.brute_force_thread.status.connect(self.update_brute_status)
        self.brute_force_thread.finished.connect(self.brute_force_finished)
        self.brute_force_thread.start()

    def stop_brute_force(self):
        if self.brute_force_thread and self.brute_force_thread.isRunning():
            self.brute_force_thread.stop()
            self.brute_force_thread.wait()
            self.brute_progress_text.append("Búsqueda detenida por el usuario")
            self.brute_force_finished([])

    def update_brute_progress(self, message):
        self.brute_progress_text.append(message)

    def add_found_url(self, url):
        """Añadir URL encontrada a la lista"""
        self.urls_list.append(url)
        # Desplazar automáticamente hacia abajo
        self.urls_list.verticalScrollBar().setValue(
            self.urls_list.verticalScrollBar().maximum()
        )
    

    def update_brute_status(self, status):
        """Actualizar la barra de progreso y el estado"""
        try:
            # Extraer el porcentaje del mensaje de estado
            percent = float(status.split('%')[0].split(':')[1].strip())
            self.brute_progress_bar.setValue(int(percent))
        except:
            pass
        self.brute_progress_text.setText(status)

    def brute_force_finished(self, results):
        self.brute_results = results
        self.brute_progress_bar.setValue(100)
        self.brute_start_button.setEnabled(True)
        self.brute_stop_button.setEnabled(False)
        self.brute_save_button.setEnabled(True)
        
        # Mostrar resumen final
        total_found = len(results)
        self.brute_progress_text.append(
            f"\nBúsqueda finalizada. Se encontraron {total_found} URLs"
        )
        
        if total_found > 0:
            self.urls_list.append("\nResumen de URLs encontradas:")
            for url in results:
                self.urls_list.append(f"[*] {url}")

    def save_brute_results(self):
        if not hasattr(self, 'brute_results'):
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Guardar Resultados", "", "Archivos de texto (*.txt);;Todos los archivos (*)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for url in self.brute_results:
                        f.write(f"{url}\n")
                self.brute_progress_text.append(f"Resultados guardados en {file_name}")
            except Exception as e:
                self.brute_progress_text.append(f"Error al guardar resultados: {str(e)}")

    def start_wordlist_download(self):
        self.download_wordlist_button.setEnabled(False)
        self.brute_progress_text.append("Iniciando descarga de SecLists...")
        self.wordlist_download_thread = DownloadWordlistThread()
        self.wordlist_download_thread.progress.connect(self.update_brute_progress)
        self.wordlist_download_thread.finished.connect(self.wordlist_download_finished)
        self.wordlist_download_thread.start()

    def wordlist_download_finished(self):
        self.download_wordlist_button.setEnabled(True)
        self.brute_progress_text.append("Proceso de descarga de wordlist finalizado.")

    # Download methods
    def start_download(self):
        url_file = self.url_file_input.text().strip()
        output_dir = self.output_dir_input.text().strip()

        if not url_file or not output_dir:
            self.download_progress_text.append("Por favor, complete todos los campos")
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.download_progress_text.append(f"Error al crear directorio de salida: {str(e)}")
                return

        try:
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.download_progress_text.append(f"Error al leer archivo de URLs: {str(e)}")
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
            self.download_progress_text.append("Descarga detenida por el usuario")
            self.download_finished([])

    def update_download_progress(self, message):
        self.download_progress_text.append(message)

    def file_downloaded(self, filepath):
        self.download_progress_bar.setValue(self.download_progress_bar.value() + 1)

    def download_finished(self, downloaded_files):
        self.download_start_button.setEnabled(True)
        self.download_stop_button.setEnabled(False)
        self.download_progress_text.append(
            f"\nDescarga finalizada. Se descargaron {len(downloaded_files)} archivos"
        )

    def extract_metadata(self):
        input_dir = self.metadata_input_dir.text().strip()
        output_file = self.metadata_output_file.text().strip()

        if not input_dir or not output_file:
            self.metadata_text.append("Por favor, complete todos los campos")
            return

        if not os.path.exists(input_dir):
            self.metadata_text.append("El directorio de entrada no existe")
            return

        self.metadata_text.clear()
        self.metadata_text.append("Iniciando extracción de metadatos...")
        
        try:
            metadata_extractor = MetadataExtractor()
            all_metadata = {}
            
            total_files = sum([len(files) for _, _, files in os.walk(input_dir)])
            processed = 0

            for root, _, files in os.walk(input_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    self.metadata_text.append(f"Procesando: {filename}")
                    
                    metadata = metadata_extractor.extract_metadata(filepath)
                    if metadata:
                        all_metadata[filepath] = metadata
                        
                    processed += 1
                    self.metadata_text.append(f"Progreso: {processed}/{total_files}")

            if all_metadata:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_metadata, f, indent=2, ensure_ascii=False)

                self.metadata_text.append(f"\nMetadatos guardados en: {output_file}")
                self.metadata_text.append("\nResumen de metadatos encontrados:")
                
                for filepath, metadata in all_metadata.items():
                    self.metadata_text.append(f"\nArchivo: {os.path.basename(filepath)}")
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float)):
                            self.metadata_text.append(f"  {key}: {value}")
            else:
                self.metadata_text.append("\nNo se encontraron metadatos en los archivos")

        except Exception as e:
            self.metadata_text.append(f"Error al extraer metadatos: {str(e)}")