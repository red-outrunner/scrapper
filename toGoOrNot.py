import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_OUTPUT_DIR = "./scraped_go_data"
JSONL_OUTPUT_FILE = os.path.join(BASE_OUTPUT_DIR, "go_dataset.jsonl")
TARGET_SITES = [
    "https://gobyexample.com/",
    "https://go.dev/doc/",
    "https://pkg.go.dev/std",
    "https://docs.fyne.io/"
]

os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

def write_to_jsonl(data, path):
    with open(path, 'a') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def clean_text(text):
    return ' '.join(text.strip().split())

def scrape_gobyexample():
    base_url = "https://gobyexample.com/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    links = [urljoin(base_url, a['href']) for a in soup.select('a.example-link') if a.get('href')]
    examples = []

    for link in links:
        res = requests.get(link)
        ex_soup = BeautifulSoup(res.content, "html.parser")
        title = ex_soup.find("h2").text if ex_soup.find("h2") else "Go Example"
        content = ex_soup.find("pre")
        explanation = ex_soup.find("p")

        prompt = clean_text(title)
        completion = clean_text(explanation.text if explanation else content.text if content else "")
        if prompt and completion:
            examples.append({"prompt": prompt, "completion": completion})
    return examples

def scrape_godoc():
    base_url = "https://go.dev/doc/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    links = [urljoin(base_url, a['href']) for a in soup.select('a') if a.get('href') and '/doc/' in a['href']]
    docs = []

    for link in links:
        try:
            res = requests.get(link)
            doc_soup = BeautifulSoup(res.content, "html.parser")
            paras = doc_soup.select("main p")
            for p in paras:
                text = clean_text(p.text)
                if len(text.split()) > 10:
                    docs.append({"prompt": "Explain: " + text[:50] + "...", "completion": text})
        except Exception as e:
            print(f"Failed to scrape {link}: {e}")
    return docs

def scrape_fyne_docs():
    base_url = "https://developer.fyne.io"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    links = [urljoin(base_url, a['href']) for a in soup.select('a') if a.get('href') and ('/develop/' in a['href'] or '/tutorial/' in a['href'])]
    content_blocks = []

    for link in links:
        try:
            res = requests.get(link)
            doc_soup = BeautifulSoup(res.content, "html.parser")
            title = doc_soup.find("h1").text if doc_soup.find("h1") else "Fyne Topic"
            sections = doc_soup.find_all(['h2', 'p', 'img'])
            for i, section in enumerate(sections):
                if section.name == 'h2':
                    prompt = clean_text(section.text)
                elif section.name == 'p':
                    completion = clean_text(section.text)
                    if prompt and completion:
                        content_blocks.append({"prompt": prompt, "completion": completion})
                elif section.name == 'img' and section.get('src'):
                    img_url = urljoin(link, section['src'])
                    content_blocks.append({"prompt": f"Diagram for topic: {prompt}", "completion": f"Image URL: {img_url}"})
        except Exception as e:
            print(f"Failed to scrape {link}: {e}")
    return content_blocks

if __name__ == "__main__":
    print("Scraping gobyexample.com...")
    examples = scrape_gobyexample()
    print(f"Collected {len(examples)} examples")

    print("Scraping go.dev/doc...")
    docs = scrape_godoc()
    print(f"Collected {len(docs)} docs")

    print("Scraping developer.fyne.io...")
    fyne_docs = scrape_fyne_docs()
    print(f"Collected {len(fyne_docs)} fyne entries")

    print("Writing to JSONL file...")
    write_to_jsonl(examples + docs + fyne_docs, JSONL_OUTPUT_FILE)
    print(f"Done. Output saved to {JSONL_OUTPUT_FILE}")
