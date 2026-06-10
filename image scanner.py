import streamlit as st
import pandas as pd
import google as genai
from PIL import Image
import io

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Gemini Product Checker", layout="wide")
st.title("📦 AI Product Image Validator (Gemini Pro Vision)")

api_key = st.text_input("Enter Gemini API Key")
if api_key:
    client = genai.Client(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

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
def extract_with_gemini(image):
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

    response = model.generate_content([prompt, image])
    return response.text

# -----------------------------
# Main logic
# -----------------------------
if api_key and excel_file and image_files:

    df = pd.read_excel(excel_file)
    st.success("Excel loaded successfully!")

    results = []

    for img_file in image_files:

        image = Image.open(img_file)

        with st.spinner(f"Analyzing {img_file.name}..."):
            response = extract_with_gemini(image)

        try:
            extracted = eval(response.replace("```json", "").replace("```", ""))
        except:
            results.append([img_file.name, "FAIL", "Gemini parsing error", "-"])
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

else:
    st.info("Upload Excel, images, and API key to start.")
