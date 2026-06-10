import streamlit as st
import pandas as pd
import google as genai  # Use explicit full namespace import
from PIL import Image
import io
import json  

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Gemini Product Checker", layout="wide")
st.title("📦 AI Product Image Validator")

api_key = st.text_input("Enter Gemini API Key", type="password")

# Initialize client using absolute full path to prevent Name/Attribute errors
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# -----------------------------
# Upload files
# -----------------------------
excel_file = st.file_uploader("📊 Upload Product Excel", type=["xlsx"])
image_files = st.file_uploader(
    "🖼️ Upload Images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

# -----------------------------
# Gemini extraction function
# -----------------------------
def extract_with_gemini(client, image):
    prompt = """
    You are a product validation assistant.
    Extract ALL product information from this image in JSON format:
    {
      "product_name": "",
      "gpu": "",
      "cpu": "",
      "ram": "",
      "storage": "",
      "price": ""
    }
    If a field is missing, put null.
    """
    
    # Explicit full path to the types configuration
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image],
        config=google.genai.types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text
