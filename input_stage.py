import os
import streamlit as st
from utils.file_reader import read_pdf, read_docx

st.title("📄 RFP Analyzer - Upload Your File")

uploaded_file = st.file_uploader("Choose a PDF or DOCX RFP", type=["pdf", "docx"])

if uploaded_file is not None:
    # Show file details
    st.write({
        "filename": uploaded_file.name,
        "type": uploaded_file.type,
        "size": uploaded_file.size
    })

    # ✅ Clean filename for Windows
    filename = uploaded_file.name
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        filename = filename.replace(c, "_")

    # ✅ Create folder safely
    save_folder = os.path.join(os.getcwd(), "data", "raw")
    os.makedirs(save_folder, exist_ok=True)

    # ✅ Full file path
    file_path = os.path.join(save_folder, filename)

    # ✅ Save the uploaded file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File saved at {file_path}")

    # ✅ Read file safely
    try:
        if filename.lower().endswith(".pdf"):
            text = read_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            text = read_docx(file_path)
        else:
            st.error("Unsupported file type!")
            text = ""

        # Preview first 500 characters
        if text:
            st.subheader("🔎 RFP Text Preview:")
            st.text(text[:500])

    except Exception as e:
        st.error(f"Error reading file: {e}")
