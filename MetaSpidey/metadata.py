import os
import json
import magic
from PIL import Image
import mimetypes
from datetime import datetime
import hashlib
import zipfile
import docx
import PyPDF2
import magic
import subprocess
from PIL.ExifTags import TAGS as EXIF_TAGS
from PIL.ExifTags import GPSTAGS
import struct

class MetadataExtractor:
    """Class for extracting metadata from files using Python native libraries"""
    def __init__(self):
        self.mime = magic.Magic(mime=True)

    def get_file_hash(self, filepath):
        """Calculate file hashes"""
        blocksize = 65536
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            while True:
                block = f.read(blocksize)
                if not block:
                    break
                md5.update(block)
                sha1.update(block)
                sha256.update(block)
                
        return {
            'MD5': md5.hexdigest(),
            'SHA1': sha1.hexdigest(),
            'SHA256': sha256.hexdigest()
        }

    def get_basic_metadata(self, filepath):
        """Get enhanced basic file metadata"""
        stat = os.stat(filepath)
        file_type = self.mime.from_file(filepath)
        extension = os.path.splitext(filepath)[1].lower()
        
        # Obtener hashes
        hashes = self.get_file_hash(filepath)
        
        metadata = {
            "FileName": os.path.basename(filepath),
            "FileExtension": extension,
            "FileSize": f"{stat.st_size / 1024:.2f} KB",
            "FileSizeBytes": stat.st_size,
            "FileType": file_type,
            "MIMEType": mimetypes.guess_type(filepath)[0] or "unknown",
            "LastModified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "LastAccessed": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
            "Created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "Permissions": oct(stat.st_mode)[-3:],
            "OwnerUID": stat.st_uid,
            "GroupGID": stat.st_gid,
            "MD5": hashes['MD5'],
            "SHA1": hashes['SHA1'],
            "SHA256": hashes['SHA256']
        }
        
        return metadata

    def get_image_metadata(self, filepath):
        """Get enhanced image metadata"""
        try:
            with Image.open(filepath) as img:
                metadata = {
                    "ImageFormat": img.format,
                    "ImageMode": img.mode,
                    "ImageSize": f"{img.width}x{img.height}",
                    "ImageWidth": img.width,
                    "ImageHeight": img.height,
                    "ImageDPI": str(img.info.get('dpi', 'N/A')),
                    "ImagePalette": bool(img.getpalette()),
                    "ImageLayers": getattr(img, 'n_frames', 1),
                    "ImageTransparency": img.info.get('transparency', 'No'),
                    "ImageCompression": img.info.get('compression', 'N/A'),
                }

                # Obtener información EXIF detallada
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        for tag_id in exif:
                            tag = EXIF_TAGS.get(tag_id, tag_id)
                            data = exif.get(tag_id)
                            if isinstance(data, bytes):
                                data = data.decode(errors='ignore')
                            if isinstance(data, (str, int, float)):
                                metadata[f"EXIF_{tag}"] = str(data)

                        # Procesar datos GPS si existen
                        if 'GPSInfo' in metadata:
                            gps_data = {}
                            for tag_id in exif[34853]:
                                tag = GPSTAGS.get(tag_id, tag_id)
                                data = exif[34853][tag_id]
                                gps_data[tag] = data
                            if gps_data:
                                metadata['GPS_Data'] = str(gps_data)

                return metadata
            
        except Exception as e:
            print(f"Error reading image metadata: {e}")
            return {}

    def get_pdf_metadata(self, filepath):
        """Get PDF file metadata"""
        try:
            with open(filepath, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                info = pdf.metadata
                metadata = {
                    "PDF_Pages": len(pdf.pages),
                    "PDF_Encrypted": pdf.is_encrypted,
                    "PDF_Author": info.get('/Author', 'N/A'),
                    "PDF_Creator": info.get('/Creator', 'N/A'),
                    "PDF_Producer": info.get('/Producer', 'N/A'),
                    "PDF_Subject": info.get('/Subject', 'N/A'),
                    "PDF_Title": info.get('/Title', 'N/A'),
                    "PDF_Creation_Date": info.get('/CreationDate', 'N/A'),
                    "PDF_Modified_Date": info.get('/ModDate', 'N/A')
                }
                
                # Extraer tamaño de la primera página
                if len(pdf.pages) > 0:
                    page = pdf.pages[0]
                    if '/MediaBox' in page:
                        metadata["PDF_Page_Size"] = f"{page['/MediaBox'][2]}x{page['/MediaBox'][3]}"
                
                return metadata
        except Exception as e:
            print(f"Error reading PDF metadata: {e}")
            return {}

    def get_office_metadata(self, filepath):
        """Get metadata from Microsoft Office documents"""
        try:
            doc = docx.Document(filepath)
            core_properties = doc.core_properties
            metadata = {
                "Office_Author": core_properties.author or 'N/A',
                "Office_Created": str(core_properties.created or 'N/A'),
                "Office_Modified": str(core_properties.modified or 'N/A'),
                "Office_LastPrintedTime": str(core_properties.last_printed or 'N/A'),
                "Office_Title": core_properties.title or 'N/A',
                "Office_Subject": core_properties.subject or 'N/A',
                "Office_Keywords": core_properties.keywords or 'N/A',
                "Office_Comments": core_properties.comments or 'N/A',
                "Office_Category": core_properties.category or 'N/A',
                "Office_Language": core_properties.language or 'N/A',
                "Office_Paragraphs": len(doc.paragraphs),
                "Office_Sections": len(doc.sections),
                "Office_Tables": len(doc.tables)
            }
            return metadata
        except Exception as e:
            print(f"Error reading Office document metadata: {e}")
            return {}

    def get_zip_metadata(self, filepath):
        """Get metadata from ZIP files"""
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                files = zip_ref.filelist
                total_size = sum(file.file_size for file in files)
                compressed_size = sum(file.compress_size for file in files)
                
                metadata = {
                    "ZIP_Files_Count": len(files),
                    "ZIP_Total_Size": f"{total_size / 1024:.2f} KB",
                    "ZIP_Compressed_Size": f"{compressed_size / 1024:.2f} KB",
                    "ZIP_Compression_Ratio": f"{(1 - compressed_size/total_size) * 100:.1f}%",
                    "ZIP_File_List": str([f.filename for f in files][:10]) + 
                                   ("..." if len(files) > 10 else "")
                }
                return metadata
        except Exception as e:
            print(f"Error reading ZIP metadata: {e}")
            return {}

    def get_text_file_info(self, filepath):
        """Get enhanced text file information"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.count('\n') + 1
                words = len(content.split())
                chars = len(content)
                spaces = content.count(' ')
                tabs = content.count('\t')
                empty_lines = content.count('\n\n') + content.count('\r\n\r\n')
                
                return {
                    "LineCount": lines,
                    "WordCount": words,
                    "CharacterCount": chars,
                    "SpaceCount": spaces,
                    "TabCount": tabs,
                    "EmptyLines": empty_lines,
                    "AverageLineLength": f"{chars/lines:.1f}" if lines > 0 else "0",
                    "AverageWordLength": f"{chars/words:.1f}" if words > 0 else "0",
                    "Encoding": "UTF-8",
                    "HasBOM": content.startswith('\ufeff'),
                    "LineEndings": self.detect_line_endings(content)
                }
        except UnicodeDecodeError:
            return {"FileType": "Binary/Non-UTF8 text file"}
        except Exception as e:
            print(f"Error reading text file: {e}")
            return {}

    def detect_line_endings(self, content):
        """Detect line ending type in text files"""
        if '\r\n' in content:
            return 'CRLF (Windows)'
        elif '\n' in content:
            return 'LF (Unix)'
        elif '\r' in content:
            return 'CR (Mac)'
        return 'No line endings'

    def _extract_metadata_native(self, filepath, metadata):
        """Extract metadata from a file based on its type using native Python libraries."""
        try:
            mime_type = self.mime.from_file(filepath)
            extension = os.path.splitext(filepath)[1].lower()
            
            if mime_type.startswith('image/'):
                metadata.update(self.get_image_metadata(filepath))
            elif mime_type.startswith('text/'):
                metadata.update(self.get_text_file_info(filepath))
            elif extension == '.pdf':
                metadata.update(self.get_pdf_metadata(filepath))
            elif extension in ['.docx', '.doc']:
                metadata.update(self.get_office_metadata(filepath))
            elif extension in ['.zip', '.jar', '.war']:
                metadata.update(self.get_zip_metadata(filepath))
            
            return metadata
        except Exception as e:
            print(f"Error extracting native metadata from {filepath}: {str(e)}")
            return metadata # Return what we have so far

    def extract_metadata(self, filepath):
        """Extract metadata from a file using exiftool, with a native fallback."""
        try:
            # Start with basic metadata
            metadata = self.get_basic_metadata(filepath)

            # Use exiftool for deep metadata extraction
            command = ["exiftool", "-j", "-G", filepath]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')

            exiftool_data = json.loads(result.stdout)[0]

            for key, value in exiftool_data.items():
                clean_key = f"Exiftool_{key.replace(':', '_')}"
                if isinstance(value, (str, int, float, bool)):
                    metadata[clean_key] = value
                else:
                    metadata[clean_key] = str(value)

            return metadata
        except FileNotFoundError:
            print("Exiftool not found. Falling back to native Python extraction.")
            # Fallback to the original method
            return self._extract_metadata_native(filepath, metadata)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Exiftool failed for {filepath}: {e}. Falling back to native extraction.")
            # Fallback to the original method
            return self._extract_metadata_native(filepath, metadata)
        except Exception as e:
            print(f"An unexpected error occurred with {filepath}: {str(e)}")
            # Fallback to the original method
            return self._extract_metadata_native(filepath, metadata)