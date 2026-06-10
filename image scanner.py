import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image
import io
import json  

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Gemini Product Checker", layout="wide")
st.title("📦 AI Product Image Validator")

api_key = st.text_input("Enter Gemini API Key", type="password")

# Initialize client if API key is provided
client = None
if api_key:
    client = Client(api_key=api_key)

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
    
    # 2. Changed to explicit GenerateContentConfig class to prevent AttributeErrors
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[prompt, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

# -----------------------------
# Main logic
# -----------------------------
if client and excel_file and image_files:

    df = pd.read_excel(excel_file)
    st.success("Excel loaded successfully!")

    results = []

    for img_file in image_files:
        image = Image.open(img_file)

        with st.spinner(f"Analyzing {img_file.name}..."):
            try:
                response_text = extract_with_gemini(client, image)
                extracted = json.loads(response_text) 
                
                # 3. Guard against cases where Gemini returns an array instead of an object
                if not isinstance(extracted, dict):
                    results.append([img_file.name, "FAIL", "Gemini did not return a valid JSON object", "-"])
                    continue
                    
            except Exception as e:
                results.append([img_file.name, "FAIL", f"Gemini error/parsing failed: {e}", "-"])
                continue

        # Find matching product
        matched = None
        for _, row in df.iterrows():
            if str(row["Model"]).lower() in str(extracted.get("product_name", "")).lower():
                matched = row
                break

        if matched is None:
            results.append([img_file.name, "FAIL", "Product not found", "-"])
            continue

        issues = []

        if extracted.get("gpu") and str(matched["GPU"]).lower() not in str(extracted["gpu"]).lower():
            issues.append(f"GPU mismatch (Excel: {matched['GPU']})")

        if extracted.get("ram") and str(matched["RAM"]).lower() not in str(extracted["ram"]).lower():
            issues.append(f"RAM mismatch (Excel: {matched['RAM']})")

        if extracted.get("price") and str(matched["Price"]).lower() not in str(extracted["price"]).lower():
            issues.append(f"Price mismatch (Excel: {matched['Price']})")

        if issues:
            for i in issues:
                results.append([img_file.name, "FAIL", i, matched["Model"]])
        else:
            results.append([img_file.name, "PASS", "All correct", matched["Model"]])

    # -----------------------------
    # Report
    # -----------------------------
    report = pd.DataFrame(results, columns=["Image", "Status", "Issue", "Product"])

    st.subheader("📊 Validation Report")
    st.dataframe(report, use_container_width=True)

    st.download_button(
        "⬇️ Download Report",
        report.to_csv(index=False).encode("utf-8"),
        "report.csv",
        "text/csv"
    )

elif not api_key:
    st.info("Please enter your Gemini API key to start.")
else:
    st.info("Upload Excel sheet and images to start validation.")
