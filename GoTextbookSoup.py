import os
import json
import fitz
from pathlib import Path

PDF_INPUT_DIR = "./go_books"
OUTPUT_DIR = "./scraped_go_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "go_books_dataset.jsonl")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_to_jsonl(data, path):
    with open(path, 'a') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def clean_text(text):
    return ' '.join(text.strip().split())

def extract_text_from_pdf(pdf_path):
    print(f"Processing {pdf_path}...")
    doc = fitz.open(pdf_path)
    results = []

    current_heading = None
    current_chunk = ""

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                span_text = " ".join([span["text"] for span in line["spans"] if span["text"].strip()])
                if not span_text:
                    continue

                font_size = line["spans"][0]["size"]

                # Treat this line as heading if it's large and short
                if font_size > 13 and len(span_text.split()) < 15:
                    if current_heading and current_chunk:
                        results.append({
                            "prompt": current_heading,
                            "completion": clean_text(current_chunk)
                        })
                    current_heading = clean_text(span_text)
                    current_chunk = ""
                else:
                    current_chunk += span_text + " "

    if current_heading and current_chunk:
        results.append({
            "prompt": current_heading,
            "completion": clean_text(current_chunk)
        })

    doc.close()
    return results

if __name__ == "__main__":
    all_data = []
    pdf_files = list(Path(PDF_INPUT_DIR).glob("*.pdf"))

    for pdf in pdf_files:
        extracted = extract_text_from_pdf(str(pdf))
        all_data.extend(extracted)

    print(f"Writing {len(all_data)} entries to {OUTPUT_FILE}")
    write_to_jsonl(all_data, OUTPUT_FILE)
    print("Done.")
