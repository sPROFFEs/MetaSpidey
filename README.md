# MetaSpidey

<p align="center">
  <img src="https://github.com/sPROFFEs/MetaSpidey/assets/150958256/85392748-398a-45d7-ac37-607af54422d7">
</p>

MetaSpidey is a powerful graphical tool designed for web crawling, file discovery, and metadata extraction. It features a user-friendly interface that simplifies the process of spidering websites, conducting brute-force directory discovery, downloading files, and analyzing metadata using Exiftool.

## Features

- **Website Crawling**: Silent or brute-force spidering with customizable parameters
- **File Discovery**: Advanced file filtering capabilities
- **Bulk Downloads**: Download multiple files from discovered URLs
- **Metadata Analysis**: Extract and analyze metadata from downloaded files using Exiftool
- **Export Options**: Save results in TXT or HTML format
- **User-Friendly Interface**: Intuitive GUI with four main tabs:
  - Crawling (Rastreo)
  - Brute Force
  - Downloads
  - Metadata

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sPROFFEs/MetaSpidey
```

2. Navigate to the MetaSpidey directory:
```bash
cd MetaSpidey
```

3. Install dependencies:
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

4. Launch the application:
```bash
python3 MetaSpidey.py
```

## Usage Guide

### Crawling Tab
- Enter the target URL in the URL field
- Set crawling depth using the dropdown menu
- Configure request delay (in seconds)
- Apply file filters (e.g., .pdf, .doc, .txt)
- Click "Iniciar Rastreo" to start crawling

### Brute Force Tab
- Input the base URL
- Select a dictionary file for directory/file discovery
- Monitor progress in the status window
- Save results when finished

### Downloads Tab
- Load a file containing URLs
- Select output directory for downloaded files
- Start downloading with a single click
- Monitor download progress

### Metadata Tab
- Select the directory containing downloaded files
- Choose output file for metadata results
- Extract metadata with Exiftool integration
- View detailed metadata analysis

## Features in Detail

1. **Crawling Options**
   - Adjustable crawling depth
   - Customizable request delays
   - File type filtering
   - Real-time progress monitoring

2. **Brute Force Capabilities**
   - Custom dictionary support
   - Progress tracking
   - Results export functionality

3. **Download Management**
   - Bulk file downloading
   - Progress tracking
   - Organized output structure

4. **Metadata Analysis**
   - Comprehensive metadata extraction
   - Multiple export formats
   - Detailed file analysis

## Disclaimer

This tool is intended for educational purposes and authorized security testing only. Users must ensure they have permission to test target systems. The authors assume no liability for misuse or damage caused by this software.

# MetaSpidey


## License

MetaSpidey is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

### Quick License Overview
- You are free to:
  - Use the software for any purpose
  - Change the software to suit your needs
  - Share the software with your friends and neighbors
  - Share the changes you make

- You must:
  - Share the source code when you share the software
  - License any derivatives under GPL-3.0
  - Keep intact all copyright notices
  - Include a copy of the license and copyright notice with the code

For the full license text, see the [LICENSE](LICENSE) file in the repository.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.
