#!/bin/bash

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Detect package manager
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt-get"
    print_status "Detected Debian/Ubuntu based system"
    # Update package lists
    print_status "Updating package lists..."
    apt-get update
    # Install Qt dependencies
    apt-get install -y qt6-base-dev libqt6core6 libqt6gui6 libqt6widgets6
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
    print_status "Detected Fedora/RHEL based system"
    # Install Qt dependencies
    dnf install -y qt6-qtbase-devel
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
    print_status "Detected Arch Linux based system"
    # Update package lists
    print_status "Updating package lists..."
    pacman -Sy
    # Install Qt dependencies
    pacman -S --noconfirm qt6-base
else
    print_error "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

# Install system dependencies based on package manager
print_status "Installing system dependencies..."

case $PKG_MANAGER in
    "apt-get")
        apt-get install -y python3 python3-pip python3-venv libexif-dev exiftool wget curl \
        libmagic-dev libtiff5-dev libjpeg-dev libopenjp2-7-dev libwebp-dev python3-tk
        ;;
    "dnf")
        dnf install -y python3 python3-pip python3-devel perl-Image-ExifTool wget curl \
        file-devel libtiff-devel libjpeg-devel openjpeg2-devel libwebp-devel python3-tkinter
        ;;
    "pacman")
        pacman -S --noconfirm python python-pip perl-image-exiftool wget curl \
        file libtiff libjpeg-turbo openjpeg2 libwebp tk
        ;;
esac

if [ $? -ne 0 ]; then
    print_error "Failed to install system dependencies"
    exit 1
fi

# Install ffuf
print_status "Installing ffuf..."
if [ ! -f "ffuf" ]; then
    FFUF_URL="https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz"
    wget -q --show-progress -O ffuf.tar.gz "$FFUF_URL"
    if [ $? -eq 0 ]; then
        tar -xzf ffuf.tar.gz ffuf
        if [ $? -eq 0 ]; then
            chmod +x ffuf
            print_status "ffuf installed successfully"
            rm ffuf.tar.gz
        else
            print_error "Failed to extract ffuf"
            rm ffuf.tar.gz
            exit 1
        fi
    else
        print_error "Failed to download ffuf"
        exit 1
    fi
else
    print_status "ffuf already installed"
fi


# Create and activate virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Install required Python packages
print_status "Installing Python packages..."
pip install \
    requests \
    beautifulsoup4 \
    pillow \
    python-magic \
    python-docx \
    PyPDF2 \
    PyQt6 \
    urllib3 \
    tqdm \
    colorama

if [ $? -ne 0 ]; then
    print_error "Failed to install Python packages"
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p downloads
mkdir -p results
mkdir -p temp

# Set correct permissions
print_status "Setting correct permissions..."
chmod +x MetaSpidey.py
chown -R $SUDO_USER:$SUDO_USER .

print_status "Installation completed successfully!"
echo 
print_warning "To use MetaSpidey:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the program: python3 MetaSpidey.py"
echo 
print_warning "Note: Some packages like 'hashlib', 'mimetypes', 'datetime', 'struct', and 'os' are part of Python's standard library and don't need separate installation."
print_warning "Make sure your system has Qt6 properly configured for the GUI to work."

# Test GUI capability
print_status "Testing Qt6 installation..."
python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null
if [ $? -eq 0 ]; then
    print_status "Qt6 installation verified successfully"
else
    print_warning "Qt6 installation might need manual configuration"
fi

