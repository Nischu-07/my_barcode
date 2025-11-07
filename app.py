import React, { useState, useRef } from "react";
import axios from "axios";
import ProductInfo from "./components/ProductInfo";

function App() {
  const videoRef = useRef(null);
  const [productData, setProductData] = useState(null);

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoRef.current.srcObject = stream;
  };

  const captureFrame = async () => {
    const canvas = document.createElement("canvas");
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg"));
    const formData = new FormData();
    formData.append("frame", blob);

    const res = await axios.post("http://localhost:5000/scan", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (res.data.length > 0) {
      setProductData(res.data[0]);
    } else {
      alert("No barcode detected!");
    }
  };

  return (
    <div style={{ textAlign: "center", padding: 20 }}>
      <h1>📷 Enhanced Barcode Scanner</h1>
      <video
        ref={videoRef}
        autoPlay
        style={{ width: "80%", borderRadius: 10, border: "2px solid #ccc" }}
      ></video>
      <div style={{ marginTop: 20 }}>
        <button onClick={startCamera}>Start Camera</button>
        <button onClick={captureFrame} style={{ marginLeft: 10 }}>
          Scan
        </button>
      </div>
      {productData && <ProductInfo info={productData} />}
    </div>
  );
}

export default App;
