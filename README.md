# MetaSpidey

<p align="center">
  <img src="https://github.com/sPROFFEs/MetaSpidey/assets/150958256/85392748-398a-45d7-ac37-607af54422d7">
</p>

MetaSpidey is a Python script designed for conducting silent or brute-force spidering on a specified domain, capturing URLs in the process. Additionally, it facilitates the downloading of all files from URLs listed in a text file and extracting metadata using Exiftool, with the option to export the results in TXT or HTML format.

<p align="center">
  <img src="https://github.com/sPROFFEs/MetaSpidey/assets/150958256/ec1ea12b-09e5-40e8-a513-ffe39b9742e1">
</p>

## Quick guide.

 	!.- Ensure that dependencies are installed.
  		* chmod +x install_dependencies.sh
		* ./install_dependencies.sh
		      
	1.- Clone repository.

		* git clone https://github.com/sPROFFEs/MetaSpidey/tree/v2.0-Python-Version

	2.- Go to directory.

		* cd MetaSpidey
  
	3.- Execute:

		* python3 MetaSpidey.py

 # Usage:
		MetaSpidey.py [-h] [-u URL] [-s] [-b] [-d DICTIONARY] [-o OUTPUT] [-g] [-f FROM_FILE] [-od OUTPUT_DIR] [-mo METADATA_OUTPUT]

		Tool for silent/brute spidering, downloading files and extracting metadata from domains

		Options:
		  -h, --help            show this help message and exit
		  -u, --url             URL of the website to spider or brute-force (http://example.com)
		  -s, --spider          Spider the website
		  -b, --brute           Perform brute-force discovery
		  -d, --dictionary      Dictionary file for brute-force discovery
		  -o, --output 	        Output file for discovered URLs
		  -g, --get             Download files from URLs specified in a text file
		  -f, --from            Text file containing URLs
		  -od, --output-dir     Output directory for downloaded files
 		  -mo, --metadata-output Output file for metadata

## Disclaimer:
The use of this script is solely for educational purposes or within controlled environments under prior agreement. The authors of this script do not condone any illegal or unethical use of the provided software. By using this script, you agree that the authors shall not be held responsible for any misuse or damage caused by the script. Use it at your own risk and discretion.

