import streamlit as st
import cv2
import numpy as np
from pyzbar import pyzbar
import requests
import time
from PIL import Image

# =========================
# Helper Functions
# =========================
def preprocess_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return gray, binary

def detect_barcodes(frame):
    """Decode barcodes using pyzbar."""
    barcodes = pyzbar.decode(frame)
    results = []
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8", errors="ignore")
        barcode_type = barcode.type
        results.append((barcode_type, barcode_data, barcode))
    return results

def get_product_info(barcode):
    """Fetch product info from OpenFoodFacts or UPCItemDB."""
    product_info = {
        "barcode": barcode,
        "found": False
    }

    # OpenFoodFacts
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                product_info.update({
                    "found": True,
                    "name": product.get("product_name", "Unknown Product"),
                    "brand": product.get("brands", "Unknown Brand"),
                    "category": product.get("categories", "Unknown Category"),
                    "origin": product.get("countries", "Unknown"),
                    "ingredients": product.get("ingredients_text", "N/A"),
                    "nutrition": {
                        "energy": product.get("nutriments", {}).get("energy-kcal_100g", "N/A"),
                        "fat": product.get("nutriments", {}).get("fat_100g", "N/A"),
                        "carbs": product.get("nutriments", {}).get("carbohydrates_100g", "N/A"),
                        "protein": product.get("nutriments", {}).get("proteins_100g", "N/A"),
                    },
                    "image_url": product.get("image_url", None)
                })
                return product_info
    except Exception:
        pass

    # UPCItemDB fallback
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                item = data["items"][0]
                product_info.update({
                    "found": True,
                    "name": item.get("title", "Unknown Product"),
                    "brand": item.get("brand", "Unknown Brand"),
                    "category": item.get("category", "Unknown Category"),
                    "description": item.get("description", "N/A")
                })
                return product_info
    except Exception:
        pass

    return product_info

def draw_barcodes(frame, results):
    for (barcode_type, barcode_data, barcode) in results:
        x, y, w, h = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"{barcode_type}: {barcode_data}"
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame

# =========================
# Streamlit Interface
# =========================
st.set_page_config(page_title="Enhanced Barcode Scanner", layout="wide")

st.title("📷 Enhanced Barcode Scanner (Streamlit Version)")
st.markdown("Detect and decode barcodes or QR codes directly from your webcam or uploaded image.")

tab1, tab2 = st.tabs(["🎥 Live Camera", "🖼️ Upload Image"])

# Shared cache for product lookups
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

# =========================
# TAB 1: Live Camera
# =========================
with tab1:
    st.markdown("### Live Camera Feed")

    # Capture webcam frames
    camera = st.camera_input("Show a barcode to your camera")

    if camera:
        # Convert to OpenCV format
        img = Image.open(camera)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        gray, binary = preprocess_frame(frame)
        results = detect_barcodes(gray)

        if results:
            frame = draw_barcodes(frame, results)
            st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption="Detected Barcode(s)", use_container_width=True)

            for barcode_type, barcode_data, _ in results:
                st.success(f"**Detected:** {barcode_type} → `{barcode_data}`")

                # Prevent duplicate lookups in a single session
                if barcode_data not in [h["data"] for h in st.session_state.scan_history]:
                    info = get_product_info(barcode_data)
                    st.session_state.scan_history.append({"time": time.strftime("%H:%M:%S"),
                                                          "type": barcode_type,
                                                          "data": barcode_data,
                                                          "info": info})

                    if info["found"]:
                        st.subheader(info["name"])
                        st.write(f"**Brand:** {info['brand']}")
                        st.write(f"**Category:** {info['category']}")
                        st.write(f"**Origin:** {info['origin']}")

                        if info.get("image_url"):
                            st.image(info["image_url"], width=200)

                        if "nutrition" in info:
                            st.markdown("**Nutrition (per 100g):**")
                            st.write(info["nutrition"])
                        if "ingredients" in info:
                            st.markdown("**Ingredients:**")
                            st.text(info["ingredients"][:300])
                    else:
                        st.warning("❌ Product not found in databases.")
        else:
            st.info("No barcode detected. Try adjusting lighting or distance.")

# =========================
# TAB 2: Upload Image
# =========================
with
