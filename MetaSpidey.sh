#!/bin/bash

#[*] Name of the script: MetaSpidey
#[*] Description: "Brute force directory on URL, download the files and extract metadat"
#[*] Version: 1.0
#[*] Author: pr0ff3
#[*] Date of creation: 16/03/2024
#[*] Date of last update: 16/03/2024

# COLORES
black='\033[1;30m'
red='\033[1;31m'
green='\033[1;32m'
yellow='\033[1;33m'
blue='\033[1;34m'
magenta='\033[1;35m'
cyan='\033[1;36m'
white='\033[0m'

# BANNER
function banner {
    printf "
    	${green}@@@@@@@@@@  @@@@@@@@ @@@@@@@  @@@@@@  ${magenta} @@@@@@ @@@@@@@  @@@ @@@@@@@  @@@@@@@@ @@@ @@@ 
        ${green}@@! @@! @@! @@!        @!!   @@!  @@@ ${magenta}!@@     @@!  @@@ @@! @@!  @@@ @@!      @@! !@@ 
        ${green}@!! !!@ @!@ @!!!:!     @!!   @!@!@!@! ${magenta} !@@!!  @!@@!@!  !!@ @!@  !@! @!!!:!    !@!@!  
        ${green}!!:     !!: !!:        !!:   !!:  !!! ${magenta}    !:! !!:      !!: !!:  !!! !!:        !!:   
        ${green} :      :   : :: ::     :     :   : : ${magenta}::.: :   :       :   :: :  :  : :: ::    .:    
        ${green}                                      ${magenta}							 ${white} v1.0
                              ${green}.:.:.$blue Script encoded by:$white @pr0ff3 ${magenta}.:.:.$white
      ${magenta}.:.:.$blue Description:$white Brute force directory on URL, download the files and extract metadata ${green}.:.:.$white


    "    
}

# Función para mostrar la ayuda
show_help() {

    banner


    echo "Usage: $0 <URL> <output_folder> <file_types> <dictionary> <max_requests>"
    echo "Download files and extract metadata from a website."
    echo ""
    echo "Arguments:"
    echo "  URL               The URL of the website to spider."
    echo "  OUTPUT_FOLDER     The folder where downloaded files and metadata will be saved."
    echo "  FILE_TYPES        The file types to download (e.g., jpg,png,pdf)."
    echo "  DICTIONARY        The file containing directory names for brute forcing."
    echo "  MAX_REQUESTS      Set the maximum number of requests to make. Set to 0 for complete the dictonary"
    echo "  Please clean all comments on your dictonary"
    exit 0
}

# Función para descargar archivos de una URL
download_files() {
    local url="$1"
    local output_folder="$2"
    local file_types="$3"
    local timeout="$4"

    # Asegurarse de que la URL tenga el formato correcto
    if [[ ! "$url" =~ ^https?:// ]]; then
        url="http://$url"
    fi

    # Descarga los archivos del URL dado
    wget --timeout="$timeout" -r -np -P "$output_folder" -A "$file_types" "$url"
}

# Función para extraer metadatos de todos los archivos descargados en todos los subdirectorios y convertirlos a HTML
extract_metadata() {
    local output_folder="$1"
    local url="$2"
    local url_name=$(echo "$url" | sed 's|.*//||; s|/.*||')
    local output_file="${url_name}_metadata.txt"
    local html_output_file="${url_name}_metadata.html"

    # Extrae los metadatos de todos los archivos descargados en todos los subdirectorios y los guarda en un archivo de texto
    find "$output_folder" -type d -exec exiftool -a -u -g1 {} + >"$output_file"
    echo "Metadata extracted and saved to $output_file"

    # Comienza el documento HTML
    echo "<!DOCTYPE html>
<html>
<head>
<title>Exif Data</title>
<style>
table {
    border-collapse: collapse;
    width: 100%;
    text-align: center;
}

table, th, td {
    border: 1px solid black;
    padding: 8px;
}

th {
    background-color: #f2f2f2;
}

body {
    width: fit-content;
    margin: 0 auto;
}
</style>
</head>
<body>
<table>
<tr>
<th>Tag</th>
<th>Value</th>
</tr>" > "$html_output_file"

    # Leer el archivo de entrada línea por línea y agregar datos a la tabla HTML
    while IFS= read -r line; do
        # Dividir la línea en el separador ':'
        IFS=':' read -r -a parts <<< "$line"
        tag="${parts[0]}"
        value="${parts[1]}"
        
        # Eliminar espacios en blanco al principio y al final de la etiqueta y el valor
        tag="$(echo -e "$tag" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        value="$(echo -e "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

        # Agregar fila a la tabla HTML
        echo "<tr>
    <td>$tag</td>
    <td>$value</td>
    </tr>" >> "$html_output_file"
    done < "$output_file"

    # Finalizar la tabla y el documento HTML
    echo "</table>
</body>
</html>" >> "$html_output_file"

    echo "Document HTML generated: $html_output_file"
}


# Función para realizar spidering y descargar archivos de un dominio URL
spider_website() {
    local url="$1"
    local output_folder="$2"
    local file_types="$3"
    local dictionary="$4"
    local max_requests="$5"
    local visited_links_file="$output_folder/visited_links.txt"
    local timeout=10   # Tiempo de espera en segundos
    local sleep_time=5 # Tiempo de espera entre peticiones en segundos
    local requests_count=0

    # Asegurarse de que la URL tenga el formato correcto
    if [[ ! "$url" =~ ^https?:// ]]; then
        url="http://$url"
    fi

    # Contar el número de entradas en el diccionario
    local dictionary_entries=$(wc -l < "$dictionary")

    # Si max_requests es 0, establecerlo como el número de entradas en el diccionario
    if [ "$max_requests" -eq 0 ]; then
        max_requests="$dictionary_entries"
    fi

    # Realiza fuerza bruta en los directorios del dominio
    while IFS= read -r directory; do
        # Verifica si se han excedido el número máximo de solicitudes
        if [ "$requests_count" -ge "$max_requests" ]; then
            break
        fi

        # Verifica si el directorio existe
        if wget --spider --timeout="$timeout" "$url/$directory" 2>/dev/null; then
            # Descarga los archivos del directorio si existe
            download_files "$url/$directory" "$output_folder" "$file_types" "$timeout"
            requests_count=$((requests_count + 1))

            # Espera antes de realizar la siguiente petición
            sleep "$sleep_time"
        else
            echo "Directory $directory not found on $url"
            requests_count=$((requests_count + 1))
        fi
    done <"$dictionary"

    echo "Spidering completed."
}

# Verifica si se solicita ayuda
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

# Verifica si se proporcionan suficientes argumentos
if [ $# -ne 5 ]; then
    echo "Usage: $0 <URL> <output_folder> <file_types> <dictionary> <max_requests>"
    exit 1
fi

# Obtiene los argumentos de entrada
url="$1"
output_folder="$2"
file_types="$3"
dictionary="$4"
max_requests="$5"

#banner
banner

# Crea la carpeta de salida si no existe
mkdir -p "$output_folder"

# Realiza el spidering y descarga los archivos
spider_website "$url" "$output_folder" "$file_types" "$dictionary" "$max_requests"

# Extrae los metadatos de las imágenes descargadas y los guarda en un archivo HTML
extract_metadata "$output_folder" "$url"
