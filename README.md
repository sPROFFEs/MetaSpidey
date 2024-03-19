# MetaSpidey

<p align="center">
  <img src="https://github.com/sPROFFEs/MetaSpidey/assets/150958256/85392748-398a-45d7-ac37-607af54422d7">
</p>



MetaSpidey is a simple bash script that enables brute force on a domain by downloading all specified files from existing directories and conducting a metadata analysis. These metadata are exported into two documents, one .txt and another .html. 

<p align="center">
  <img src="https://github.com/sPROFFEs/MetaSpidey/assets/150958256/27b06a5b-6798-43cc-a47a-0be179dda832">
</p>



# Quick guide.

 	!.- Ensure that Exiftool is installed.
  		* sudo apt install libimage-exiftool-perl
    
>if not https://exiftool.org/install.html
      
	1.- Clone repository.

		* git clone https://github.com/sPROFFEs/MetaSpidey

	2.- Go to directory.

		* cd MetaSpidey

	3.- Grant permissions.:

		* chmod +x MetaSpidey.sh

	4.- Execute:

		* bash MetaSpidey.sh -h
  		* ./MetaSpidey.sh --help

# Usage:
		  ./MetaSpidey.sh <URL> <output_folder> <file_types> <dictionary> <max_requests>
                  Arguments:
 		  URL               The URL of the website to spider.
		  OUTPUT_FOLDER     The folder where downloaded files and metadata will be saved.
		  FILE_TYPES        The file types to download (e.g., jpg,png,pdf).
		  DICTIONARY        The file containing directory names for brute forcing.
		  MAX_REQUESTS      Set the maximum number of requests to make. Set to 0 for complete the dictonary
		  Please clean all comments on your dictonary

## Disclaimer:
The use of this script is solely for educational purposes or within controlled environments under prior agreement. The authors of this script do not condone any illegal or unethical use of the provided software. By using this script, you agree that the authors shall not be held responsible for any misuse or damage caused by the script. Use it at your own risk and discretion.


