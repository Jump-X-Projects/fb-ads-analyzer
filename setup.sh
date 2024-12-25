#!/bin/bash

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment (you'll need to do this manually)
echo "To activate virtual environment:"
echo "On Windows: venv\\Scripts\\activate"
echo "On Mac/Linux: source venv/bin/activate"

# After activation, run:
echo "After activation, run: pip install -r requirements.txt"

# Create downloads directory
mkdir -p downloads

# Create .env file template
if [ ! -f .env ]; then
    echo "GOOGLE_API_KEY=your_key_here" > .env
    echo "Created .env file template"
fi
