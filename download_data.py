"""
download_data.py
----------------
Downloads the Online Retail II dataset from the UCI Machine Learning Repository.
Place this script in the project root and run it once:

    python download_data.py

The file will be saved to  data/raw/online_retail_II.xlsx

Source : https://archive.ics.uci.edu/dataset/502/online+retail+ii
Licence: CC BY 4.0  (https://creativecommons.org/licenses/by/4.0/)
Citation: Chen, D. (2012). Online Retail II [Dataset]. UCI ML Repository.
"""

import os
import zipfile
import urllib.request
import sys
import time

# ---- Configuration ----
URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
ZIP_PATH = os.path.join(RAW_DIR, "online_retail_ii.zip")
XLSX_NAME = "online_retail_II.xlsx"
XLSX_PATH = os.path.join(RAW_DIR, XLSX_NAME)

MAX_RETRIES = 3


def download_dataset():
    """Download and extract the Online Retail II dataset."""

    # Skip if already downloaded
    if os.path.exists(XLSX_PATH):
        size_mb = os.path.getsize(XLSX_PATH) / (1024 * 1024)
        print(f"[OK] Dataset already exists at {XLSX_PATH} ({size_mb:.1f} MB)")
        return XLSX_PATH

    os.makedirs(RAW_DIR, exist_ok=True)

    # Download with retries
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Download attempt {attempt}/{MAX_RETRIES} from {URL} ...")
        try:
            urllib.request.urlretrieve(URL, ZIP_PATH)
            print(f"[OK] Downloaded to {ZIP_PATH}")
            break
        except Exception as e:
            print(f"[FAIL] Attempt {attempt} failed: {e}")
            # Clean up partial download
            if os.path.exists(ZIP_PATH):
                os.remove(ZIP_PATH)
            if attempt < MAX_RETRIES:
                wait = 5 * attempt
                print(f"  Retrying in {wait} seconds ...")
                time.sleep(wait)
            else:
                print("  All attempts failed. Please download manually from:")
                print("  https://archive.ics.uci.edu/dataset/502/online+retail+ii")
                print("  Extract online_retail_II.xlsx into data/raw/")
                sys.exit(1)

    # Extract the xlsx from the zip
    print("Extracting ...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        xlsx_files = [f for f in zf.namelist() if f.endswith(".xlsx")]
        if not xlsx_files:
            print("[FAIL] No .xlsx file found in the archive.")
            sys.exit(1)

        for xlsx_file in xlsx_files:
            zf.extract(xlsx_file, RAW_DIR)
            extracted_path = os.path.join(RAW_DIR, xlsx_file)
            # If extracted to a subfolder, move to RAW_DIR
            if extracted_path != XLSX_PATH and os.path.exists(extracted_path):
                os.replace(extracted_path, XLSX_PATH)
            print(f"[OK] Extracted {xlsx_file}")

    # Clean up the zip file
    os.remove(ZIP_PATH)
    print("[OK] Removed zip file")

    # Report file size
    size_mb = os.path.getsize(XLSX_PATH) / (1024 * 1024)
    print(f"[OK] Dataset ready: {XLSX_PATH} ({size_mb:.1f} MB)")
    return XLSX_PATH


if __name__ == "__main__":
    download_dataset()
