import streamlit as st
import google.generativeai as genai
import re
import os
import tempfile
from PIL import Image
import PyPDF2
import fitz  # PyMuPDF
import easyocr
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

# Configuration
st.set_page_config(page_title="MediSimplify", layout="centered")

# Set up Gemini API
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    st.sidebar.success("✓ Gemini API connected successfully")
except KeyError:
    st.error("Gemini API key not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error setting up Gemini: {str(e)}")
    st.stop()

# Global OCR reader with thread safety
_ocr_reader = None
_ocr_lock = threading.Lock()

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        with _ocr_lock:
            if _ocr_reader is None:
                _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader

# Safety Disclaimer
def display_disclaimer():
    st.warning("""
    **DISCLAIMER**: This tool provides simplified explanations for informational purposes only. 
    It is NOT a substitute for professional advice, diagnosis, or treatment. 
    Always consult a healthcare provider for medical concerns.
    """)

# Keyword Filter for Safety
def contains_harmful_content(text):
    harmful_keywords = [
        "suicide", "self-harm", "overdose", "abuse", "violence",
        "emergency", "critical", "life-threatening"
    ]
    return any(keyword in text.lower() for keyword in harmful_keywords)

# Truncate text to manage processing time
def truncate_text(text, max_chars=8000):
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Text truncated for processing efficiency]"

# Fast text extraction from PDF with smart fallback
def extract_text_from_pdf(pdf_file):
    text = ""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    try:
        # First try PyPDF2 (fastest)
        with open(tmp_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages[:10]:  # Limit to first 10 pages
                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 50:  # Only if substantial text
                    text += page_text + "\n"
        
        # If PyPDF2 got good results, return early
        if len(text.strip()) > 200:
            return truncate_text(text)
        
        # Fallback to PyMuPDF with OCR only if needed
        doc = fitz.open(tmp_path)
        ocr_reader = None
        
        for page_num, page in enumerate(doc[:5], start=1):  # Limit to first 5 pages
            # Try direct text extraction first
            page_text = page.get_text("text")
            if page_text and len(page_text.strip()) > 50:
                text += page_text + "\n"
            else:
                # OCR fallback with lower DPI for speed
                try:
                    if ocr_reader is None:
                        ocr_reader = get_ocr_reader()
                    
                    pix = page.get_pixmap(dpi=150)  # Reduced from 200 to 150
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Resize image if too large (speeds up OCR significantly)
                    max_size = 1500
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    img_array = np.array(img)
                    ocr_results = ocr_reader.readtext(img_array, detail=0, paragraph=True, width_ths=0.9)
                    
                    if ocr_results:
                        text += "\n".join(ocr_results) + "\n"
                    
                except Exception as e:
                    st.warning(f"⚠️ OCR failed for page {page_num}: {str(e)}")
                    
            # Early exit if we have enough text
            if len(text) > 5000:
                break
                
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return truncate_text(text)

# Optimized image OCR
def extract_text_from_image(image_file):
    try:
        reader = get_ocr_reader()
        image = Image.open(image_file).convert("RGB")
        
        # Optimize image size for faster OCR
        max_size = 1500
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        img_array = np.array(image)
        
        # Optimized OCR parameters for speed
        ocr_results = reader.readtext(
            img_array, 
            detail=0, 
            paragraph=True,
            width_ths=0.9,  # Faster text grouping
            height_ths=0.9
        )
        
        text = "\n".join(ocr_results) if ocr_results else ""
        return truncate_text(text)
        
    except Exception as e:
        st.error(f"OCR failed: {str(e)}")
        return ""

# Optimized simplification prompt
def create_simplification_prompt(medical_text):
    # Pre-process to remove excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', medical_text.strip())
    
    return f"""
    You are a medical communication expert. Convert this complex medical text into simple, 
    easy-to-understand English for patients. Be concise but complete:
    
    Rules:
    1. Replace medical jargon with everyday terms
    2. Use short sentences and simple language
    3. Maintain all critical medical information
    4. Add brief explanations for unavoidable technical terms
    5. Use bullet points for lists
    6. Keep the explanation under 500 words
    
    Medical Text:
    {cleaned_text}
    
    Simplified Version:
    """

# Async text processing
def process_text_async(text, progress_bar):
    try:
        progress_bar.progress(30)
        response = model.generate_content(create_simplification_prompt(text))
        progress_bar.progress(80)
        return response.text
    except Exception as e:
        raise e

# Main App
def main():
    st.title("🏥 MediSimplify")
    st.markdown("Translate complex medical text into plain English")

    display_disclaimer()

    # Performance tips
    with st.expander("💡 Tips for faster processing"):
        st.markdown("""
        - For PDFs: First 10 pages are processed for speed
        - For images: Keep resolution reasonable (not ultra-high DPI)
        - Text is automatically truncated at 8000 characters
        - OCR works best with clear, high-contrast text
        """)

    # Input Section - Tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["📝 Paste Text", "📄 Upload PDF", "🖼️ Upload Image"])

    medical_text = ""

    with tab1:
        medical_text = st.text_area(
            "Paste medical text here:",
            height=200,
            max_chars=8000,
            placeholder="e.g., 'The patient shows signs of cardiomegaly with pulmonary edema...'"
        )

    with tab2:
        uploaded_pdf = st.file_uploader("Upload a PDF medical report", type=["pdf"])
        if uploaded_pdf is not None:
            # Show file info
            file_size = len(uploaded_pdf.read())
            uploaded_pdf.seek(0)  # Reset file pointer
            st.info(f"File size: {file_size/1024:.1f} KB")
            
            if file_size > 5 * 1024 * 1024:  # 5MB limit
                st.warning("Large files may take longer to process. Consider using smaller files or specific pages.")
            
            with st.spinner("Extracting text from PDF..."):
                try:
                    medical_text = extract_text_from_pdf(uploaded_pdf)
                    if medical_text.strip():
                        st.success(f"✓ Text extracted successfully! ({len(medical_text)} characters)")
                        with st.expander("Preview extracted text"):
                            st.text_area("Extracted Text", medical_text[:1000] + "..." if len(medical_text) > 1000 else medical_text, height=150)
                    else:
                        st.warning("No text could be extracted from the PDF.")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")

    with tab3:
        uploaded_image = st.file_uploader("Upload an image of medical report", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            # Show image preview
            st.image(uploaded_image, width=300, caption="Uploaded image")
            
            with st.spinner("Extracting text from image..."):
                try:
                    medical_text = extract_text_from_image(uploaded_image)
                    if medical_text.strip():
                        st.success(f"✓ Text extracted successfully! ({len(medical_text)} characters)")
                        with st.expander("Preview extracted text"):
                            st.text_area("Extracted Text", medical_text, height=150)
                    else:
                        st.warning("No text could be extracted from the image.")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

    # Process Button
    if st.button("🚀 Simplify", type="primary", use_container_width=True):
        if not medical_text.strip():
            st.error("Please enter or upload medical text to simplify")
        elif contains_harmful_content(medical_text):
            st.error("This text contains sensitive content. Please consult a healthcare professional directly.")
        else:
            # Show processing progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("Processing with AI...")
                progress_bar.progress(10)
                
                simplified_text = process_text_async(medical_text, progress_bar)
                
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()

                st.subheader("📋 Simplified Explanation")
                st.success(simplified_text)

                # Download and copy options
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download as Text",
                        data=simplified_text,
                        file_name="simplified_medical_text.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                with col2:
                    if st.button("📋 Copy to Clipboard", use_container_width=True):
                        st.write("Click the text above to select and copy")

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"An error occurred: {str(e)}")

    st.markdown("---")
    st.caption("⚡ Optimized for speed • This tool uses AI to simplify medical terminology • Always verify with healthcare professionals")

if __name__ == "__main__":
    main()
