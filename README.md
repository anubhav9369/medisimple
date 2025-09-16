# 🏥 MediSimplify

MediSimplify is an AI-powered Streamlit app that helps **translate complex medical text** (from PDFs, images, or plain text) into **simple, easy-to-understand English** for patients.  

It uses **Google Gemini AI** for text simplification and **EasyOCR** + **PyMuPDF** + **PyPDF2** for robust text extraction.


Website : https://medisimple.streamlit.app/
---

## ✨ Features

- 📄 **Upload PDF medical reports**  
  - Extracts text from digital PDFs  
  - Falls back to **OCR** for scanned/image-based PDFs  

- 🖼️ **Upload medical report images**  
  - Uses **EasyOCR** to detect and read text  

- 📝 **Paste raw text** for direct simplification  

- 🤖 **AI-powered simplification** with **Gemini 1.5 Flash**  
  - Converts medical jargon into patient-friendly language  
  - Uses bullet points, short sentences, and clear explanations  

- ⚡ **Optimized performance**  
  - Limits text to first 10 PDF pages & 8000 characters for speed  
  - Caches OCR models for faster reuse  

- 📥 **Export results**  
  - Download simplified text as `.txt` file  
  - Copy to clipboard  

---

## 🛠️ Tech Stack

### Core Framework
- [Streamlit](https://streamlit.io/) → Web app framework  

### AI Model
- [Google Generative AI (Gemini)](https://ai.google.dev/) → Medical text simplification  

### PDF & OCR Tools
- [PyPDF2](https://pypi.org/project/PyPDF2/) → Fast PDF text extraction  
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) → Advanced PDF parsing, rendering pages to images  
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) → OCR for scanned PDFs & images  

### Image Processing
- [Pillow (PIL)](https://pypi.org/project/Pillow/) → Image handling  
- [NumPy](https://numpy.org/) → Array & image transformations  

### Machine Learning Libraries (for EasyOCR)
- [PyTorch](https://pytorch.org/) → Backend engine for EasyOCR  
- [Torchvision](https://pytorch.org/vision/stable/index.html) → Vision utilities for OCR  

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/MediSimplify.git
cd MediSimplify
```
2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Set up Gemini API Key

Create a Streamlit secrets file:

.streamlit/secrets.toml


Add your Gemini API key:

GEMINI_API_KEY = "your_api_key_here"

4️⃣ Run the app
streamlit run app.py
