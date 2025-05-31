#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Amega AI development environment...${NC}"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo -e "${YELLOW}Error: Python $required_version or higher is required (you have $python_version)${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install pre-commit hooks
echo -e "${GREEN}Setting up pre-commit hooks...${NC}"
pre-commit install

# Create necessary directories
echo -e "${GREEN}Creating project directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p models

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update the .env file with your configuration${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the .env file with your configuration"
echo "2. Run 'python scripts/init_db.py' to initialize the database"
echo "3. Start the development server with 'uvicorn src.amega_ai.main:app --reload'" 