import streamlit as st
import google.generativeai as genai
import re
import os
import tempfile
from PIL import Image
import PyPDF2
import pytesseract
import pdf2image
import io

# Configuration
st.set_page_config(page_title="MediSimplify", layout="centered")

# Set up Gemini API
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    st.sidebar.success("✓ Gemini API connected successfully")
except KeyError:
    st.error("Gemini API key not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error setting up Gemini: {str(e)}")
    st.stop()

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

# Extract text from PDF with multiple methods
def extract_text_from_pdf(pdf_file):
    text = ""
    
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    
    try:
        # Method 1: Try direct text extraction
        with open(tmp_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # If we got a reasonable amount of text, return it
        if len(text.strip()) > 50:  # Arbitrary threshold
            return text
            
        # Method 2: If direct extraction failed, try OCR
        st.info("Direct text extraction failed. Using OCR to extract text from images...")
        
        # Convert PDF to images
        images = pdf2image.convert_from_path(tmp_path)
        
        for img in images:
            # Use Tesseract to extract text from each image
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
            
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return ""
    finally:
        # Clean up the temporary file
        os.unlink(tmp_path)
    
    return text

# Extract text from image using OCR
def extract_text_from_image(image_file):
    image = Image.open(image_file)
    text = pytesseract.image_to_string(image)
    return text

# Simplification Prompt
def create_simplification_prompt(medical_text):
    return f"""
    You are a medical communication expert. Convert this complex medical text into simple, 
    easy-to-understand English for patients. Follow these rules:
    
    1. Replace medical jargon with everyday terms
    2. Use short sentences and simple language
    3. Maintain all critical medical information
    4. Add brief explanations for unavoidable technical terms
    5. Use bullet points for lists
    6. Do not add new information not in the original text
    
    Original Text:
    {medical_text}
    
    Simplified Version:
    """

# Main App
def main():
    st.title("🏥 MediSimplify")
    st.markdown("Translate complex medical text into plain English")
    
    display_disclaimer()
    
    # Input Section - Tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Paste Text", "Upload PDF", "Upload Image"])
    
    medical_text = ""
    
    with tab1:
        medical_text = st.text_area(
            "Paste medical text here:",
            height=200,
            placeholder="e.g., 'The patient shows signs of cardiomegaly with pulmonary edema...'"
        )
    
    with tab2:
        uploaded_pdf = st.file_uploader("Upload a PDF medical report", type=["pdf"])
        if uploaded_pdf is not None:
            with st.spinner("Extracting text from PDF..."):
                try:
                    medical_text = extract_text_from_pdf(uploaded_pdf)
                    if medical_text.strip():
                        st.success("Text extracted successfully!")
                        st.text_area("Extracted Text", medical_text, height=150)
                    else:
                        st.warning("No text could be extracted from the PDF. It might be a scanned document with poor quality or protected content.")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
    
    with tab3:
        uploaded_image = st.file_uploader("Upload an image of medical report", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            with st.spinner("Extracting text from image..."):
                try:
                    medical_text = extract_text_from_image(uploaded_image)
                    if medical_text.strip():
                        st.success("Text extracted successfully!")
                        st.text_area("Extracted Text", medical_text, height=150)
                    else:
                        st.warning("No text could be extracted from the image. Please ensure the image is clear and contains readable text.")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    st.info("Note: For image processing, you need Tesseract OCR installed on your system.")
    
    # Process Button
    if st.button("Simplify", type="primary"):
        if not medical_text.strip():
            st.error("Please enter or upload medical text to simplify")
        elif contains_harmful_content(medical_text):
            st.error("This text contains sensitive content. Please consult a healthcare professional directly.")
        else:
            with st.spinner("Simplifying..."):
                try:
                    # Generate content using Gemini
                    response = model.generate_content(create_simplification_prompt(medical_text))
                    simplified_text = response.text
                    
                    # Display Results
                    st.subheader("Simplified Explanation")
                    st.success(simplified_text)
                    
                    # Add Download Button
                    st.download_button(
                        label="Download Simplified Text",
                        data=simplified_text,
                        file_name="simplified_medical_text.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.caption("This tool uses AI to simplify medical terminology. Always verify with healthcare professionals.")

if __name__ == "__main__":
    main()