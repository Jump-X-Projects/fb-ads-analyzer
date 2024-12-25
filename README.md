# Facebook Ads Analyzer

A tool for analyzing competitor video ads using Gemini AI.

## Setup

1. Create and activate virtual environment:
    ```bash
    python -m venv venv

    # On Windows:
    venv\Scripts\activate
    # On Mac/Linux:
    source venv/bin/activate
    ```

2. Install requirements:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:
    ```bash
    # Create .env file and add your Google API key
    echo "GOOGLE_API_KEY=your_key_here" > .env
    ```

4. Run the application:
    ```bash
    streamlit run src/app.py
    ```

## Features
- Video ad analysis from Facebook Ad Library
- Scene-by-scene breakdown
- Competitive insights generation
- Strategic recommendations
- Export functionality

## Project Structure
```plaintext
fb-ads-analyzer/
├── src/
│   ├── __init__.py
│   └── app.py
├── venv/
├── .gitignore
├── README.md
├── requirements.txt
└── setup.sh
