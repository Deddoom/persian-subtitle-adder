#!/bin/bash

# Print colored output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Persian Subtitle App Installer (Linux) ===${NC}"

# 1. Check/Install System Dependencies
echo -e "\n${GREEN}[1/4] Installing System Dependencies (FFmpeg, Tkinter)...${NC}"
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-tk ffmpeg
else
    echo -e "${RED}[WARNING] 'apt-get' not found. If you are not on Debian/Ubuntu, please install 'ffmpeg' and 'python3-tk' manually.${NC}"
fi

# 2. Create Virtual Environment
echo -e "\n${GREEN}[2/4] Creating Python Virtual Environment...${NC}"
python3 -m venv venv

# 3. Activate and Install
echo -e "\n${GREEN}[3/4] Installing Python Libraries...${NC}"
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# 4. Check FFmpeg
echo -e "\n${GREEN}[4/4] Verifying FFmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}[OK] FFmpeg is installed.${NC}"
else
    echo -e "${RED}[ERROR] FFmpeg could not be found. Please install it manually.${NC}"
fi

echo -e "\n${GREEN}=============================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "To run the app, use the following command:"
echo -e "   ${GREEN}source venv/bin/activate && python3 persian_subtitle_app.py${NC}"
echo -e "${GREEN}=============================================${NC}"