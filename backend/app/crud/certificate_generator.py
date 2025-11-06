from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from minio import Minio
import os

# --- MinIO Configuration ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000").replace("http://", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_CERT_BUCKET = os.getenv("MINIO_CERT_BUCKET", "certificates")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)


def generate_certificate(student_name: str, course_name: str):
    """
    Generates a certificate PDF and uploads it to MinIO.
    Returns: certificate file URL.
    """
    # ✅ Ensure bucket exists
    if not minio_client.bucket_exists(MINIO_CERT_BUCKET):
        minio_client.make_bucket(MINIO_CERT_BUCKET)

    # 🕒 Unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"certificate_{student_name.replace(' ', '_')}_{timestamp}.pdf"

    # 🧾 Create PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFillColor(colors.HexColor("#004aad"))
    pdf.setFont("Helvetica-Bold", 32)
    pdf.drawCentredString(width / 2, height - 150, "Certificate of Completion")

    pdf.setFont("Helvetica", 18)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width / 2, height - 220, "This certificate is proudly presented to")

    pdf.setFont("Helvetica-Bold", 26)
    pdf.setFillColor(colors.HexColor("#d46f4d"))
    pdf.drawCentredString(width / 2, height - 270, student_name)

    pdf.setFont("Helvetica", 18)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width / 2, height - 320, f"For successfully completing:")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 350, course_name)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 420, f"Issued on: {datetime.utcnow().strftime('%d %B %Y')}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    # ☁️ Upload to MinIO
    minio_client.put_object(
        MINIO_CERT_BUCKET,
        filename,
        buffer,
        length=len(buffer.getvalue()),
        content_type="application/pdf",
    )

    file_url = f"http://{MINIO_ENDPOINT}/{MINIO_CERT_BUCKET}/{filename}"
    print(f"✅ Certificate uploaded to MinIO: {file_url}")
    return file_url
