import argparse
import os
import sys

import subprocess

def install_python_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("Installing Python dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Python dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}", file=sys.stderr)
        sys.exit(1)

import platform
import urllib.request
import tarfile
import zipfile
import shutil

def get_ffuf_url():
    """Determine the correct ffuf download URL based on OS and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if "aarch64" in machine or "arm64" in machine:
            arch = "arm64"
        else:
            arch = "amd64"
        ext = "tar.gz"
    elif system == "darwin":
        arch = "amd64"
        ext = "tar.gz"
    elif system == "windows":
        arch = "amd64"
        ext = "zip"
    else:
        print(f"Unsupported OS: {system}", file=sys.stderr)
        return None

    url = f"https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_{system}_{arch}.{ext}"
    return url

def install_ffuf():
    """Download and extract the ffuf binary."""
    print("Installing ffuf...")
    ffuf_url = get_ffuf_url()
    if not ffuf_url:
        sys.exit(1)

    bin_dir = "bin"
    os.makedirs(bin_dir, exist_ok=True)

    # Check if ffuf already exists
    ffuf_path = os.path.join(bin_dir, "ffuf.exe" if platform.system().lower() == "windows" else "ffuf")
    if os.path.exists(ffuf_path):
        print("ffuf is already installed.")
        return

    try:
        filename = os.path.basename(ffuf_url)
        download_path = os.path.join(bin_dir, filename)

        print(f"Downloading ffuf from {ffuf_url}...")
        urllib.request.urlretrieve(ffuf_url, download_path)
        print("Download complete.")

        print("Extracting ffuf...")
        if download_path.endswith(".tar.gz"):
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extract("ffuf", path=bin_dir)
        elif download_path.endswith(".zip"):
            with zipfile.ZipFile(download_path, "r") as zip_ref:
                zip_ref.extract("ffuf.exe", path=bin_dir)

        os.remove(download_path)

        if not os.path.exists(ffuf_path):
             # In some tarballs, ffuf is in a subdirectory
             extracted_ffuf = os.path.join(bin_dir, 'ffuf_2.1.0', 'ffuf')
             if os.path.exists(extracted_ffuf):
                 shutil.move(extracted_ffuf, ffuf_path)
                 shutil.rmtree(os.path.join(bin_dir, 'ffuf_2.1.0'))


        if os.path.exists(ffuf_path):
            os.chmod(ffuf_path, 0o755)
            print("ffuf installed successfully.")
        else:
            print("Error: ffuf executable not found after extraction.", file=sys.stderr)

    except Exception as e:
        print(f"Error installing ffuf: {e}", file=sys.stderr)
        sys.exit(1)

def check_exiftool():
    """Check if exiftool is installed and provide instructions if not."""
    print("Checking for exiftool...")
    if shutil.which("exiftool"):
        print("exiftool is installed.")
    else:
        print("\n---")
        print("Warning: exiftool not found in your system's PATH.", file=sys.stderr)
        print("The metadata extraction feature will be limited without it.", file=sys.stderr)
        print("Please install it using your system's package manager:", file=sys.stderr)
        print("  - Debian/Ubuntu: sudo apt-get install libimage-exiftool-perl", file=sys.stderr)
        print("  - Fedora/RHEL: sudo dnf install perl-Image-ExifTool", file=sys.stderr)
        print("  - Arch Linux: sudo pacman -S perl-image-exiftool", file=sys.stderr)
        print("  - macOS (Homebrew): brew install exiftool", file=sys.stderr)
        print("  - Windows: Download from https://exiftool.org/", file=sys.stderr)
        print("---\n")

def handle_install():
    """Run the complete installation process."""
    print("Starting MetaSpidey setup...")
    install_python_dependencies()
    install_ffuf()
    check_exiftool()
    print("\nInstallation complete. You can now run the application with 'python launch.py run'.")

def handle_run():
    """Run the main MetaSpidey application."""
    print("Launching MetaSpidey...")
    main_script_path = os.path.join("MetaSpidey", "main.py")
    if not os.path.exists(main_script_path):
        print(f"Error: Main script not found at {main_script_path}", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run([sys.executable, main_script_path])
    except Exception as e:
        print(f"Error launching MetaSpidey: {e}", file=sys.stderr)
        sys.exit(1)

def handle_build():
    """Build the application using PyInstaller."""
    print("Building application with PyInstaller...")
    spec_file = "metaspidey.spec"
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found. Cannot build the application.", file=sys.stderr)
        sys.exit(1)

    print(f"Using spec file: {spec_file}")
    try:
        subprocess.check_call([sys.executable, "-m", "PyInstaller", spec_file, "--noconfirm"])
        print("\nBuild successful!")
        print("You can find the distributable in the 'dist' directory.")
    except subprocess.CalledProcessError as e:
        print(f"Error during build process: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: PyInstaller is not installed. Please run 'python launch.py install' first.", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to parse arguments and call the appropriate handler."""
    parser = argparse.ArgumentParser(
        description="MetaSpidey Launcher: A tool to install, run, and build the MetaSpidey application."
    )
    parser.add_argument(
        "command",
        choices=["install", "run", "build"],
        help="The command to execute: 'install' to set up dependencies, 'run' to start the application, 'build' to package it."
    )

    args = parser.parse_args()

    if args.command == "install":
        handle_install()
    elif args.command == "run":
        handle_run()
    elif args.command == "build":
        handle_build()

if __name__ == "__main__":
    main()
