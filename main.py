from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from PIL import Image
import qrcode
import io

app = FastAPI()

# -----------------------------
# Endpoint 1: Generate QR code
# -----------------------------
@app.post("/generate")
async def generate_qr(
    url: str = Form(...),
    file: UploadFile = File(...)
):
    # Read uploaded icon
    icon_bytes = await file.read()
    icon = Image.open(io.BytesIO(icon_bytes))

    # Create QR
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Resize icon
    qr_w, qr_h = qr_img.size
    icon_size = qr_w // 4
    icon = icon.resize((icon_size, icon_size))

    # Center position
    pos = ((qr_w - icon_size) // 2, (qr_h - icon_size) // 2)

    # Paste icon
    qr_img.paste(icon, pos, mask=icon if icon.mode == 'RGBA' else None)

    # Save to buffer
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


# -----------------------------
# Endpoint 2: UI Page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
    <html>
        <head>
            <title>QR Generator</title>
        </head>
        <body style="font-family: Arial; padding: 40px;">
            <h2>Generate QR Code</h2>
            
            <form id="qrForm">
                <label>Website URL:</label><br>
                <input type="text" name="url" style="width:300px" required><br><br>

                <label>Upload Icon:</label><br>
                <input type="file" name="file" accept="image/*" required><br><br>

                <button type="submit">Generate</button>
            </form>

            <br>
            <img id="result" style="margin-top:20px; max-width:300px;" />

            <script>
                const form = document.getElementById('qrForm');
                const resultImg = document.getElementById('result');

                form.addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const formData = new FormData(form);

                    const response = await fetch('/generate', {
                        method: 'POST',
                        body: formData
                    });

                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);

                    resultImg.src = url;
                });
            </script>
        </body>
    </html>
    """


# -----------------------------
# Run with:
# uvicorn main:app --reload
# -----------------------------
