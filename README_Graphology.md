# Handwriting Rules Extractor (Graphology.py)

This is a backend script that processes handwriting reference books (PDFs) and saves their rules into a database file.

## What it does
1. **Reads PDFs**: It opens two PDF books (`graphologyhowtor00howa.pdf` and `handwriting_quick_reference_guide.pdf`) and extracts their text.
2. **AI Extraction**: It sends segments of the text to Google's Gemini AI to find handwriting rules.
3. **Structured Format**: The AI converts the descriptions into structured records (the trait name, how it looks, what it means, and which book it came from).
4. **Saves Database**: It saves everything to `knowledge_base.json`. The web app (`app.py`) reads this file to match handwriting features.

## How to run it
1. Ensure your API key is in the `.env` file:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
2. Run the script in your terminal to build or update the database:
   ```bash
   python Graphology.py
   ```
3. Wait for it to finish. It will save the rules database to `knowledge_base.json` in the same folder.
