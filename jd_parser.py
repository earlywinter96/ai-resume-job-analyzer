import requests
from bs4 import BeautifulSoup
import PyPDF2

def extract_jd_from_url(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(p.get_text() for p in soup.find_all("p"))
    return text.strip()

def extract_jd_from_pdf(path):
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()
