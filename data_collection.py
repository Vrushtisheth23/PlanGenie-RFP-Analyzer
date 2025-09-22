import os

# Path to raw RFP files
raw_folder = "data/raw"

# List all files in the raw folder
rfp_files = os.listdir(raw_folder)

print("📄 Found RFP files:")
for f in rfp_files:
    print(f"- {f}")
