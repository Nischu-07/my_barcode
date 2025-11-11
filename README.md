# 📷 Enhanced Barcode Scanner using OpenCV & Pyzbar

This project is an advanced **real-time barcode and QR code scanner** built using **Python**, **OpenCV**, and **Pyzbar**.  
It enhances barcode detection with multiple preprocessing methods and retrieves **product details** using **OpenFoodFacts** and **UPCItemDB APIs**.

---

## 🚀 Features

- 🔍 Detects **all major barcode types** (EAN, UPC, Code39, Code128, QR, PDF417, DataMatrix, etc.)
- 🧠 **Multiple preprocessing filters** (grayscale, thresholding, contrast enhancement, sharpening)
- 🌐 **Fetches product data** automatically from:
  - [OpenFoodFacts API](https://world.openfoodfacts.org)
  - [UPCItemDB API](https://upcitemdb.com)
- 🧾 Displays:
  - Product name, brand, category, and origin  
  - Nutrition and ingredients (if available)
- 🕒 **Scan cooldown system** to prevent duplicate scans
- 🧩 **Scan history viewer**
- ✅ Clean interface with live camera feed and bounding boxes around barcodes

---

## 🧰 Requirements

Install the required packages before running the script:

```bash
pip install opencv-python pyzbar requests numpy
