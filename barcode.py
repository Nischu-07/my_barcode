import cv2
from pyzbar import pyzbar
import requests
import time
import numpy as np

class EnhancedBarcodeScanner:
    def __init__(self):
        self.last_scanned = None
        self.last_scan_time = 0
        self.scan_cooldown = 2  # seconds between rescans of same barcode
        self.scan_history = []
        
    def preprocess_frame(self, frame):
        """
        Apply multiple preprocessing techniques to improve barcode detection
        Returns a list of processed frames to try
        """
        processed_frames = []
        
        # Original frame
        processed_frames.append(('Original', frame))
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        processed_frames.append(('Grayscale', gray))
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        processed_frames.append(('Blurred', blurred))
        
        # Adaptive thresholding for better contrast
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        processed_frames.append(('Adaptive Threshold', adaptive))
        
        # Binary threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        processed_frames.append(('Binary', binary))
        
        # Otsu's thresholding
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_frames.append(('Otsu', otsu))
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        clahe_img = clahe.apply(gray)
        processed_frames.append(('CLAHE', clahe_img))
        
        # Sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        processed_frames.append(('Sharpened', sharpened))
        
        return processed_frames
    
    def detect_barcodes_enhanced(self, frame):
        """
        Try multiple preprocessing methods to maximize barcode detection
        """
        all_barcodes = []
        unique_barcodes = {}
        
        # Get all preprocessed versions
        processed_frames = self.preprocess_frame(frame)
        
        # Try to decode from each preprocessed frame
        for name, processed in processed_frames:
            barcodes = pyzbar.decode(processed)
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8', errors='ignore')
                barcode_type = barcode.type
                key = f"{barcode_type}:{barcode_data}"
                
                # Store unique barcodes
                if key not in unique_barcodes:
                    unique_barcodes[key] = barcode
                    all_barcodes.append(barcode)
        
        return all_barcodes
    
    def get_product_info(self, barcode):
        """
        Fetch product information from multiple APIs
        """
        product_info = {
            'barcode': barcode,
            'found': False
        }
        
        # Try OpenFoodFacts first (great for food products)
        try:
            print(f"\n🔍 Looking up barcode: {barcode}")
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1:
                    product = data.get('product', {})
                    product_info.update({
                        'found': True,
                        'name': product.get('product_name', 'Unknown Product'),
                        'brand': product.get('brands', 'Unknown Brand'),
                        'category': product.get('categories', 'Unknown Category'),
                        'origin': product.get('countries', 'Unknown'),
                        'ingredients': product.get('ingredients_text', 'N/A'),
                        'nutrition': {
                            'energy': product.get('nutriments', {}).get('energy-kcal_100g', 'N/A'),
                            'fat': product.get('nutriments', {}).get('fat_100g', 'N/A'),
                            'carbs': product.get('nutriments', {}).get('carbohydrates_100g', 'N/A'),
                            'protein': product.get('nutriments', {}).get('proteins_100g', 'N/A'),
                        },
                        'image_url': product.get('image_url', None)
                    })
                    return product_info
        except Exception as e:
            print(f"⚠ OpenFoodFacts error: {e}")
        
        # Try UPCItemDB as fallback
        try:
            url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    product_info.update({
                        'found': True,
                        'name': item.get('title', 'Unknown Product'),
                        'brand': item.get('brand', 'Unknown Brand'),
                        'category': item.get('category', 'Unknown Category'),
                        'origin': 'N/A',
                        'description': item.get('description', 'N/A'),
                    })
                    return product_info
        except Exception as e:
            print(f"⚠ UPCItemDB error: {e}")
        
        # Try Barcode Lookup API (alternative)
        try:
            url = f"https://api.barcodelookup.com/v3/products?barcode={barcode}&formatted=y&key=YOUR_API_KEY"
            # Note: This requires an API key - user would need to sign up at barcodelookup.com
            # Commenting out as it needs authentication
        except Exception as e:
            pass
        
        return product_info
    
    def display_product_info(self, info):
        """
        Display product information in a clean format
        """
        print("\n" + "="*60)
        print("✅ PRODUCT DETECTED")
        print("="*60)
        print(f"📊 Barcode: {info['barcode']}")
        
        if info['found']:
            print(f"📦 Product: {info.get('name', 'N/A')}")
            print(f"🏷️  Brand: {info.get('brand', 'N/A')}")
            print(f"📂 Category: {info.get('category', 'N/A')}")
            print(f"🌍 Origin: {info.get('origin', 'N/A')}")
            
            if 'nutrition' in info and info['nutrition']['energy'] != 'N/A':
                print(f"\n🍎 Nutrition (per 100g):")
                print(f"   • Energy: {info['nutrition']['energy']} kcal")
                print(f"   • Fat: {info['nutrition']['fat']} g")
                print(f"   • Carbs: {info['nutrition']['carbs']} g")
                print(f"   • Protein: {info['nutrition']['protein']} g")
            
            if 'description' in info:
                print(f"\n📝 Description: {info['description']}")
            
            if 'ingredients' in info and info['ingredients'] != 'N/A':
                ingredients = info['ingredients'][:200]
                print(f"\n🧪 Ingredients: {ingredients}...")
        else:
            print("❌ Product not found in database")
            print("   (This barcode may not be registered or may be region-specific)")
        
        print("="*60 + "\n")
    
    def draw_barcode_box(self, frame, barcode, color=(0, 255, 0)):
        """
        Draw a box around detected barcode with label
        """
        points = barcode.polygon
        if len(points) == 4:
            pts = [(point.x, point.y) for point in points]
            pts.append(pts[0])
            for j in range(len(pts) - 1):
                cv2.line(frame, pts[j], pts[j + 1], color, 3)
        
        # Add barcode data as label
        x, y = barcode.rect.left, barcode.rect.top - 10
        barcode_data = barcode.data.decode('utf-8', errors='ignore')
        barcode_type = barcode.type
        
        # Create label background
        label = f"{barcode_type}: {barcode_data}"
        (label_width, label_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
        )
        
        cv2.rectangle(frame, (x, y - label_height - 10), 
                     (x + label_width + 10, y), color, -1)
        cv2.putText(frame, label, (x + 5, y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return barcode_data
    
    def run(self):
        """
        Main scanning loop with enhanced detection
        """
        print("\n" + "="*60)
        print("📷 ENHANCED BARCODE SCANNER - ALL TYPES")
        print("="*60)
        print("Supports: EAN-13, EAN-8, UPC-A, UPC-E, Code 39, Code 128,")
        print("          QR Code, Data Matrix, PDF417, Aztec, and more!")
        print("="*60)
        print("\nStarting camera... (Press 'q' to quit)")
        print("Position a barcode in front of the camera to scan.")
        print("\nControls:")
        print("  • 'q' - Quit scanner")
        print("  • 'r' - Reset cooldown (rescan same barcode)")
        print("  • 'h' - Show scan history")
        print("="*60 + "\n")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Error: Could not access camera.")
            print("   Make sure your camera is connected and not in use.")
            return
        
        # Set camera resolution and properties for better detection
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        
        print("✅ Camera activated! Scanning for barcodes...\n")
        
        detected_barcodes = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to grab frame from camera")
                break
            
            frame_count += 1
            
            # Enhanced barcode detection (try multiple preprocessing methods)
            barcodes = self.detect_barcodes_enhanced(frame)
            
            # Clear previous detections
            detected_barcodes = []
            
            # Process each detected barcode
            for idx, barcode in enumerate(barcodes):
                # Use different colors for multiple barcodes
                colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0)]
                color = colors[idx % len(colors)]
                
                barcode_data = self.draw_barcode_box(frame, barcode, color)
                detected_barcodes.append({
                    'data': barcode_data,
                    'type': barcode.type
                })
                
                # Check if this is a new barcode or enough time has passed
                current_time = time.time()
                scan_key = f"{barcode.type}:{barcode_data}"
                
                if (scan_key != self.last_scanned or 
                    current_time - self.last_scan_time > self.scan_cooldown):
                    
                    # Update tracking
                    self.last_scanned = scan_key
                    self.last_scan_time = current_time
                    
                    # Add to history
                    self.scan_history.append({
                        'time': time.strftime("%H:%M:%S"),
                        'type': barcode.type,
                        'data': barcode_data
                    })
                    
                    # Get and display product info
                    product_info = self.get_product_info(barcode_data)
                    self.display_product_info(product_info)
            
            # Add instructions overlay
            cv2.putText(frame, "Controls: 'q' Quit | 'r' Rescan | 'h' History", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if detected_barcodes:
                status_text = f"Detected: {len(detected_barcodes)} barcode(s)"
                cv2.putText(frame, status_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show barcode types
                for idx, bc in enumerate(detected_barcodes):
                    type_text = f"  {idx+1}. {bc['type']}"
                    cv2.putText(frame, type_text, (10, 90 + idx*25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            else:
                cv2.putText(frame, "Scanning... Show a barcode to camera", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Display frame count for debugging
            cv2.putText(frame, f"Frame: {frame_count}", (frame.shape[1] - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Display the frame
            cv2.imshow('Enhanced Barcode Scanner - Live Feed', frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n👋 Stopping scanner...")
                break
            elif key == ord('r'):
                # Reset to allow rescanning same barcode
                self.last_scanned = None
                print("\n🔄 Ready to rescan...")
            elif key == ord('h'):
                # Show scan history
                print("\n" + "="*60)
                print("📋 SCAN HISTORY")
                print("="*60)
                if self.scan_history:
                    for idx, scan in enumerate(self.scan_history[-10:], 1):
                        print(f"{idx}. [{scan['time']}] {scan['type']}: {scan['data']}")
                else:
                    print("No scans yet!")
                print("="*60 + "\n")
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("\n✅ Scanner stopped. Camera released.")
        print(f"📊 Total scans: {len(self.scan_history)}\n")


if __name__ == "__main__":
    scanner = EnhancedBarcodeScanner()
    scanner.run()
