import os
from utils.file_reader import read_pdf, read_docx

raw_folder = "data/raw"
processed_folder = "data/processed"

# Make sure processed folder exists
os.makedirs(processed_folder, exist_ok=True)

# Go through each file in raw folder
for file_name in os.listdir(raw_folder):
    file_path = os.path.join(raw_folder, file_name)
    if file_name.endswith(".pdf"):
        text = read_pdf(file_path)
    elif file_name.endswith(".docx"):
        text = read_docx(file_path)
    else:
        print(f"⚠️ Skipping unsupported file: {file_name}")
        continue

    # Clean text a bit
    text = text.replace("\n\n", "\n").strip()

    # Save cleaned text
    save_path = os.path.join(processed_folder, file_name.replace(".pdf", ".txt").replace(".docx", ".txt"))
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ Processed and saved: {save_path}")
