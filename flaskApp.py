from flask import Flask, request, send_file, render_template_string
import qrcode
from PIL import Image
import io
import logging
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# -----------------------------
# QR generation function
# -----------------------------
def create_qr(url, icon_file=None):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Optional icon
    if icon_file:
        icon = Image.open(icon_file)

        qr_w, qr_h = qr_img.size
        icon_size = qr_w // 4

        icon = icon.resize((icon_size, icon_size))

        pos = ((qr_w - icon_size) // 2, (qr_h - icon_size) // 2)

        qr_img.paste(icon, pos, mask=icon if icon.mode == "RGBA" else None)

    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    return buf


# -----------------------------
# API endpoint
# -----------------------------
@app.route("/generate", methods=["POST"])
def generate():
    client_ip = request.remote_addr
    url = request.form.get("url")

    logger.info(f"Incoming request ip={client_ip} url={url}")

    file = request.files.get("file")

    try:
        img_io = create_qr(url, file)
        logger.info(f"QR generated successfully ip={client_ip}")
        return send_file(img_io, mimetype="image/png")
    except Exception as e:
        logger.exception(f"Error generating QR ip={client_ip}: {e}")
        return {"error": "QR generation failed"}, 500


# -----------------------------
# UI page
# -----------------------------
@app.route("/")
def index():
    return render_template_string("""
    <html>
    <head>
        <title>Flask QR Generator</title>
    </head>
    <body style="font-family: Arial; padding: 40px;">
        <h2>QR Code Generator</h2>

        <form id="form">
            <label>Website URL:</label><br>
            <input type="text" name="url" style="width:300px" required><br><br>

            <label>Upload Icon (optional):</label><br>
            <input type="file" name="file"><br><br>

            <button type="submit">Generate</button>
        </form>

        <br>
        <img id="result" style="max-width:300px; margin-top:20px;" />

        <script>
            const form = document.getElementById("form");
            const result = document.getElementById("result");

            form.addEventListener("submit", async (e) => {
                e.preventDefault();

                const formData = new FormData(form);

                const res = await fetch("/generate", {
                    method: "POST",
                    body: formData
                });

                const blob = await res.blob();
                result.src = URL.createObjectURL(blob);
            });
        </script>
    </body>
    </html>
    """)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)