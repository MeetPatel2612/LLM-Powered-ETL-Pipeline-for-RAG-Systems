import os
import json
import time
# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF
from google import genai
from pydantic import BaseModel, Field

def load_env(env_path=".env"):
    """Loads key-value pairs from a local .env file into os.environ."""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip().strip('"').strip("'")
                        os.environ[key.strip()] = val

# Execute environment configuration load
load_env()

# ==============================================================================
# 1. DEFINE THE STRUCTURED DATA MODEL (The Contract)
# ==============================================================================
class GraphologyTrait(BaseModel):
    trait_name: str = Field(description="The core handwriting feature name normalized (e.g., 't-bar', 'i-dot', 'slant', 'margins', 'baseline', 'pressure').")
    variation: str = Field(description="The explicit layout modification or stroke variation observed (e.g., 'crossed high', 'vertical', 'wide spacing', 'ascending').")
    interpretation: str = Field(description="The exact psychological trait, significance, or behavioral tendency associated with this variation according ONLY to the text.")
    source_book: str = Field(description="The name/author of the source text used for this specific rule mapping.")

# ==============================================================================
# 2. CORE ETL PIPELINE EXECUTION ENGINE
# ==============================================================================
def run_phase_one_etl():
    if not os.environ.get("GEMINI_API_KEY"):
        print("CRITICAL ERROR: GEMINI_API_KEY environment variable not found.")
        print("Please configure your GEMINI_API_KEY in the `.env` file.")
        return

    # Initialize the official modern Google GenAI Client
    client = genai.Client()
    
    # Using the standard reliable and fast tier-free model
    MODEL_NAME = "gemini-2.5-flash" 

    # Concrete pipeline configurations matching your source books
    books = [
        {
            "file_name": "graphologyhowtor00howa.pdf",
            "title": "Howard 1922 (Clifford Howard)",
            "style": "narrative",
            "prompt": (
                "You are an academic research assistant parsing a historical, dense narrative-style book on graphology. "
                "Analyze the provided text layout chunk and extract all underlying graphological rules, laws, "
                "and character associations. Normalize the trait names to clean categories. "
                "Extract terms cleanly into the required structured array format. "
                "If no graphology rules or interpretations exist in this exact chunk, return an empty array []."
            )
        },
        {
            "file_name": "handwriting_quick_reference_guide.pdf",
            "title": "Baggett 2004 (Bart Baggett)",
            "style": "structured",
            "prompt": (
                "You are a strict data extraction bot processing a structured quick-reference directory. "
                "Extract every feature variation, baseline, stroke, or letter pattern along with its direct personality meaning. "
                "Strictly isolate the values into the schema definitions. Avoid formatting conversational explanations or meta-commentary. "
                "If no traits or structural meanings are present in this text chunk, return an empty array []."
            )
        }
    ]

    output_file = "knowledge_base.json"
    all_extracted_traits = []

    # Fault-Tolerance Check: Resume safely if script gets disconnected or hits limits
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                all_extracted_traits = json.load(f)
            print(f" Found existing '{output_file}' containing {len(all_extracted_traits)} rules. Resuming operations and appending...")
        except json.JSONDecodeError:
            print(" Found corrupted output file. Overwriting and starting fresh.")

    # Process files sequentially
    for book in books:
        file_path = book["file_name"]
        
        if not os.path.exists(file_path):
            print(f"Warning: Target file '{file_path}' not found in script folder. Skipping execution block for: {book['title']}.")
            continue
            
        print(f"\n==================================================")
        print(f"INGESTING SOURCE: {book['title']}")
        print(f"==================================================")
        
        # Read the raw text streaming from the target PDF document layout
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()
        
        # Chunks of 10,000 characters bundle multiple pages cleanly, optimizing context maps and minimizing daily/minute RPM limits
        chunk_size = 10000
        chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]
        print(f"Text parsed. Segmented document into {len(chunks)} structural text blocks.")

        # Loop processing through individual layout sections
        for idx, chunk in enumerate(chunks):
            print(f"Processing block {idx + 1}/{len(chunks)}...")
            
            # Enforce Schema Constraints directly inside the API Configuration
            config_params = {
                "response_mime_type": "application/json",
                "response_schema": list[GraphologyTrait],
                "system_instruction": book["prompt"]
            }
            
            max_retries = 3
            backoff_delay = 5  # Initial cooling period (seconds)
            extracted_data_chunk = None
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=f"Document Context: {book['title']}\n\nRaw Fragment Input:\n{chunk}",
                        config=config_params
                    )
                    # Automatically unpacks validated JSON into native Pydantic class objects
                    extracted_data_chunk = response.parsed
                    break  # Success! Break from retry strategy
                except Exception as e:
                    print(f"[API Threshold/Error] Attempt {attempt + 1} blocked: {e}")
                    if attempt < max_retries - 1:
                        print(f"Applying backoff: Cooling down for {backoff_delay} seconds...")
                        time.sleep(backoff_delay)
                        backoff_delay *= 2  # Exponential step increase
                    else:
                        print(f"Failed chunk {idx + 1} permanently across all backoffs. Moving forward to protect loop state.")

            # Append validation maps to disk instantly to prevent total process data wipes
            if extracted_data_chunk:
                print(f"Successfully extracted {len(extracted_data_chunk)} structured entries.")
                for trait in extracted_data_chunk:
                    all_extracted_traits.append(trait.model_dump())
                
                # Flushing data payload directly to disk
                with open(output_file, "w") as f:
                    json.dump(all_extracted_traits, f, indent=4)
            
            # Safe resting delay between network requests to handle regular Free-tier rate-limit resets
            time.sleep(2.5)

    print(f"\n🏆 Pipeline Process Completed Successfully!")
    print(f"📊 Total Extracted Rule Records inside Database: {len(all_extracted_traits)}")
    print(f"📂 Master JSON Schema Saved At: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    run_phase_one_etl()