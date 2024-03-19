import argparse
import requests
import subprocess
import os
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def banner():
    # COLORES
    black = '\033[1;30m'
    red = '\033[1;31m'
    green = '\033[1;32m'
    yellow = '\033[1;33m'
    blue = '\033[1;34m'
    magenta = '\033[1;35m'
    cyan = '\033[1;36m'
    white = '\033[0m'

    # BANNER
    print(f"""
    {green}@@@@@@@@@@  @@@@@@@@ @@@@@@@  @@@@@@  {magenta} @@@@@@ @@@@@@@  @@@ @@@@@@@  @@@@@@@@ @@@ @@@ 
    {green}@@! @@! @@! @@!        @!!   @@!  @@@ {magenta}!@@     @@!  @@@ @@! @@!  @@@ @@!      @@! !@@ 
    {green}@!! !!@ @!@ @!!!:!     @!!   @!@!@!@! {magenta} !@@!!  @!@@!@!  !!@ @!@  !@! @!!!:!    !@!@!  
    {green}!!:     !!: !!:        !!:   !!:  !!! {magenta}    !:! !!:      !!: !!:  !!! !!:        !!:   
    {green} :      :   : :: ::     :     :   : : {magenta}::.: :   :       :   :: :  :  : :: ::    .:    
    {green}                                      {magenta}							 {white} v2.0
                          {green}.:.:.{blue} Script encoded by:{white} @pr0ff3 {magenta}.:.:.{white}
  {magenta}.:.:{blue} Description:{white} Brute force directory on URL, download the files and extract metadata {green}.:.:{white}
    """)

def spider_website(url, output_file):
    # Lista para almacenar las URLs visitadas
    visited_urls = set()
    
    # Función para obtener todos los enlaces de una página
    def get_links(page_url):
        response = requests.get(page_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(page_url, href)
                if urlparse(full_url).netloc == urlparse(url).netloc:  # Comprobar si el enlace está dentro del mismo dominio
                    links.append(full_url)
        return links
    
    # Función recursiva para seguir los enlaces
    def crawl(url):
        if url in visited_urls:
            return
        print("Found:", url)
        visited_urls.add(url)
        links = get_links(url)
        for link in links:
            crawl(link)
    
    # Comenzar el crawling desde la URL proporcionada
    try:
        crawl(url)
    except KeyboardInterrupt:
        pass  # Manejar la interrupción del teclado sin mostrar el rastreo de la pila
    finally:
        # Guardar las URLs visitadas en un archivo de texto
        with open(output_file, 'w') as f:
            for url in visited_urls:
                f.write(f"{url}\n")

def brute(url, dictionary_file, output_file):
    # Lista para almacenar las URLs descubiertas
    discovered_urls = set()

    # Cargar el diccionario de palabras
    with open(dictionary_file, 'r') as f:
        words = f.readlines()
    
    # Función para realizar el descubrimiento mediante fuerza bruta
    def brute_force(url, words):
        for word in words:
            word = word.strip()  # Eliminar caracteres de espacio en blanco al inicio y al final
            full_url = urljoin(url, word)
            try:
                response = requests.get(full_url)
                print(f"Testing {full_url} - Response code: {response.status_code}")
                if response.status_code == 200:  # Comprobar si la URL es válida (código de respuesta 200)
                    discovered_urls.add(full_url)
            except KeyboardInterrupt:
                break  # Salir del bucle al presionar Ctrl+C

    # Realizar el descubrimiento mediante fuerza bruta
    try:
        brute_force(url, words)
    except KeyboardInterrupt:
        pass  # Manejar la interrupción del teclado sin mostrar el rastreo de la pila
    finally:
        # Guardar las URLs descubiertas en un archivo de texto
        with open(output_file, 'w') as f:
            for url in discovered_urls:
                f.write(f"{url}\n")

def download_files(file_urls, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for url in file_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                content_type = response.headers.get('content-type')
                # Obtener la extensión del archivo desde la URL
                filename = os.path.basename(urlsplit(url).path)
                _, file_extension = os.path.splitext(filename)
                if file_extension == '':
                    # Si la URL no tiene una extensión, intentamos obtenerla del tipo de contenido
                    if content_type:
                        file_extension = mimetypes.guess_extension(content_type.split(';')[0])
                        if not file_extension:
                            file_extension = '.html'  # Si no se puede determinar la extensión, se asume que es HTML
                    else:
                        file_extension = '.html'  # Si no hay tipo de contenido, se asume que es HTML
                # Guardar el archivo con la extensión correcta
                filepath = os.path.join(output_dir, filename)
                print(f"Downloading {url} to {filepath}")
                with open(filepath, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Failed to download {url}: {e}")


def extract_metadata(file_dir, output_file):
    try:
        print(f"Extracting metadata from files in {file_dir}")
        metadata = subprocess.check_output(['exiftool', file_dir])
        with open(output_file, 'wb') as f:
            f.write(metadata)
    except Exception as e:
        print(f"Failed to extract metadata: {e}")

def create_html_metadata(metadata_file, output_html):
    # Leer los datos del archivo de metadatos
    with open(metadata_file, 'r') as f:
        metadata_lines = f.readlines()

    # Preparar el contenido HTML
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Metadata</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 20px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #fff;
                border: 1px solid #ddd;
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
            }
            li a {
                color: #337ab7;
                text-decoration: none;
            }
            li a:hover {
                text-decoration: underline;
            }
            .metadata {
                display: none;
            }
            .visible {
                display: block;
            }
        </style>
    </head>
    <body>
        <h1>Metadata</h1>
        <ul>
    """

    # Agregar cada nombre de archivo como un elemento de lista
    file_metadata = {}
    current_file = None
    for line in metadata_lines:
        if line.strip():
            if line.startswith('========'):
                current_file = line.strip().replace('=', '')
                file_metadata[current_file] = []
            else:
                file_metadata[current_file].append(line.strip())

    for filename, metadata in file_metadata.items():
        html_content += f'<li><a href="#" onclick="toggleMetadata(\'{filename}\')">{filename}</a></li>\n'
        html_content += f'<div id="{filename}" class="metadata">\n'
        html_content += '<ul>\n'
        for data in metadata:
            html_content += f'<li>{data}</li>\n'
        html_content += '</ul>\n</div>\n'

    # Finalizar el contenido HTML
    html_content += """
        </ul>
        <script>
            function toggleMetadata(filename) {
                var metadata = document.getElementById(filename);
                if (metadata.classList.contains("visible")) {
                    metadata.classList.remove("visible");
                } else {
                    metadata.classList.add("visible");
                }
            }
        </script>
    </body>
    </html>
    """


    # Escribir el contenido HTML en el archivo de salida
    with open(output_html, 'w') as f:
        f.write(html_content)        
  
def main():
    banner()
    
    parser = argparse.ArgumentParser(description='Tool for silent/brute spidering, downloading files and extracting metadata from domains')
    parser.add_argument('-u', '--url', required=False, help='URL of the website to spider or brute-force (https://example.com)')
    parser.add_argument('-s', '--spider', action='store_true', help='Spider the website')
    parser.add_argument('-b', '--brute', action='store_true', help='Perform brute-force discovery')
    parser.add_argument('-d', '--dictionary', required=False, help='Dictionary file for brute-force discovery')
    parser.add_argument('-o', '--output', required=False, default='output.txt', help='Output file for discovered URLs')
    parser.add_argument('-g', '--get', action='store_true', help='Download files from URLs specified in a text file')
    parser.add_argument('-f', '--from', required=False, dest='from_file', help='Text file containing URLs')
    parser.add_argument('-od', '--output-dir', required=False, default='downloads', help='Output directory for downloaded files')
    parser.add_argument('-mo', '--metadata-output', required=False, default='metadata.txt', help='Output file for metadata')
    args = parser.parse_args()

    if args.spider:
        spider_website(args.url, args.output)
    elif args.brute:
        if not args.dictionary:
            print("Error: You must specify a dictionary file for brute-force discovery.")
            return
        brute(args.url, args.dictionary, args.output)
    elif args.get:
        if not args.from_file:
            print("Error: You must specify a file containing URLs with the --from option.")
            return
        with open(args.from_file, 'r') as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
        download_files(urls, args.output_dir)
        extract_metadata(args.output_dir, args.metadata_output)
        create_html_metadata(args.metadata_output, 'metadata.html')
    else:
        print("Error: You must specify either spidering (-s), brute-force discovery (-b), or file downloading (-g).")

if __name__ == "__main__":
    main()
