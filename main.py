from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from PIL import Image
import qrcode
from datetime import datetime
import io,logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()


# Optional: simple request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    logger.info(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("Unhandled error occurred")
        raise

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Completed {request.method} {request.url} in {duration:.3f}s status={response.status_code}")
    return response
# -----------------------------
# Endpoint 1: Generate QR code
# -----------------------------
@app.post("/generate")
async def generate_qr(
    url: str = Form(...),
    file: UploadFile = File(...)
):
    
    logger.info(f"Generating QR for URL: {url}")
    # Read uploaded icon
    # icon_bytes = await file.read()
    # icon = Image.open(io.BytesIO(icon_bytes))
    icon = None
    if file is not None:
        icon_bytes = await file.read()
        if icon_bytes:
            logger.info(f"Icon uploaded: {file.filename}")
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
    if icon is not None:
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
    logger.info("QR generation successful")
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
                <input type="file" name="file" accept="image/*" ><br><br>

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
