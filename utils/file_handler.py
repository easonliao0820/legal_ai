import os
import zipfile
import rarfile
import py7zr
import subprocess
import shutil

class FileHandler:
    @staticmethod
    def extract_archive(archive_path, extract_to, fmt):
        """Extracts various archive formats to a directory."""
        fmt = fmt.lower()
        is_archive = False
        try:
            if fmt == '7z':
                with py7zr.SevenZipFile(archive_path, 'r') as z:
                    z.extractall(extract_to)
                is_archive = True
            elif fmt == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as z:
                    z.extractall(extract_to)
                is_archive = True
            elif fmt == 'rar':
                try:
                    # Prefer bsdtar on macOS
                    subprocess.run(['bsdtar', '-xf', archive_path, '-C', extract_to], check=True)
                    is_archive = True
                except Exception:
                    # Fallback to rarfile
                    with rarfile.RarFile(archive_path, 'r') as z:
                        z.extractall(extract_to)
                    is_archive = True
        except Exception as e:
            print(f"Extraction error: {e}")
            return False
        return is_archive

    @staticmethod
    def read_text_file(filepath, max_size=512000):
        """Reads a text file with encoding detection (UTF-8, Big5)."""
        try:
            with open(filepath, 'rb') as f:
                raw_bytes = f.read(max_size)
                
                # Try UTF-8 first
                try:
                    return raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # Fallback to Big5 for traditional Chinese documents
                    try:
                        return raw_bytes.decode('big5')
                    except Exception:
                        return None
        except Exception as e:
            print(f"File read error: {e}")
            return None

    @staticmethod
    def cleanup_dir(directory):
        """Safely removes a directory and its contents."""
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=True)
