# MetaSpidey
            
        @@@@@@@@@@  @@@@@@@@ @@@@@@@  @@@@@@   @@@@@@ @@@@@@@  @@@ @@@@@@@  @@@@@@@@ @@@ @@@ 
        @@! @@! @@! @@!        @!!   @@!  @@@ !@@     @@!  @@@ @@! @@!  @@@ @@!      @@! !@@                                                                                                                                                
        @!! !!@ @!@ @!!!:!     @!!   @!@!@!@!  !@@!!  @!@@!@!  !!@ @!@  !@! @!!!:!    !@!@!                                                                                                                                                 
        !!:     !!: !!:        !!:   !!:  !!!     !:! !!:      !!: !!:  !!! !!:        !!:                                                                                                                                                  
         :      :   : :: ::     :     :   : : ::.: :   :       :   :: :  :  : :: ::    .:                                                                                                                                                   
                                                                                                  v1.0                                                                                                                                      
                              .:.:. Script encoded by: @pr0ff3 .:.:.
      .:.:. Description: Brute force directory on URL, download the files and extract metadata .:.:.


MetaSpidey is a simple bash script that enables brute force on a domain by downloading all specified files from existing directories and conducting a metadata analysis. These metadata are exported into two documents, one .txt and another .html. 

![imagen](https://github.com/sPROFFEs/MetaSpidey/assets/150958256/27b06a5b-6798-43cc-a47a-0be179dda832)

>> Quick guide.

 	!.- Ensure that Exiftool is installed.
  		* sudo apt install libimage-exiftool-perl
if not https://exiftool.org/install.html
      
	1.- Clone repository.

		* git clone https://github.com/sPROFFEs/MetaSpidey

	2.- Go to directory.

		* cd MetaSpidey

	3.- Grant permissions.:

		* chmod +x MetaSpidey.sh

	4.- Execute:

		* bash MetaSpidey.sh -h
  		* ./MetaSpidey.sh --help

	5.- Parameters:
		* Usage: ./MetaSpidey.sh <URL> <output_folder> <file_types> <dictionary> <max_requests>
                  Arguments:
 		  URL               The URL of the website to spider.
		  OUTPUT_FOLDER     The folder where downloaded files and metadata will be saved.
		  FILE_TYPES        The file types to download (e.g., jpg,png,pdf).
		  DICTIONARY        The file containing directory names for brute forcing.
		  MAX_REQUESTS      Set the maximum number of requests to make. Set to 0 for complete the dictonary
		  Please clean all comments on your dictonary

Use under environments with appropriate permissions.

