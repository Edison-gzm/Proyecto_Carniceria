import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from fpdf import FPDF
from sqlalchemy.orm import Session
from database.models.sale import Sale
from config import INVOICES_DIR, APP_NAME

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
 
 
class InvoiceService:
    def __init__(self, session: Session):
        self.session = session
 
    def generate_pdf(self, sale_id: int) -> Path:
        sale = self.session.get(Sale, sale_id)
        if not sale:
            raise ValueError(f"Venta {sale_id} no encontrada")
 
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
 
        # Encabezado
        pdf.cell(0, 10, APP_NAME, ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Factura: {sale.invoice_number}", ln=True, align="C")
        pdf.cell(0, 6, f"Fecha: {sale.created_at.strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        pdf.ln(4)
 
        # Cliente
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Cliente:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        if sale.customer:
            pdf.cell(0, 6, f"{sale.customer.full_name} - {sale.customer.id_number}", ln=True)
        pdf.ln(4)
 
        # Tabla de productos
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(80, 7, "Producto", border=1)
        pdf.cell(20, 7, "Cant.", border=1, align="C")
        pdf.cell(25, 7, "Unidad", border=1, align="C")
        pdf.cell(30, 7, "P. Unit.", border=1, align="R")
        pdf.cell(35, 7, "Subtotal", border=1, align="R", ln=True)
 
        pdf.set_font("Helvetica", "", 9)
        for item in sale.items:
            pdf.cell(80, 6, item.product_name[:40], border=1)
            pdf.cell(20, 6, str(item.quantity), border=1, align="C")
            pdf.cell(25, 6, item.unit, border=1, align="C")
            pdf.cell(30, 6, f"${item.unit_price:,.0f}", border=1, align="R")
            pdf.cell(35, 6, f"${item.subtotal:,.0f}", border=1, align="R", ln=True)
 
        # Total
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(155, 8, "TOTAL", align="R")
        pdf.cell(35, 8, f"${sale.total:,.0f}", border=1, align="R", ln=True)
 
        # Guardar
        output_path = Path(INVOICES_DIR) / f"{sale.invoice_number}.pdf"
        pdf.output(str(output_path))

        # Guardar la ruta en la base de datos para el contador
        sale.invoice_pdf_path = str(output_path)
        self.session.commit()

        return output_path

    def print_invoice(self, sale_id: int) -> Path:
        """Genera (si no existe) e imprime la factura en la impresora predeterminada de Windows."""
        sale = self.session.get(Sale, sale_id)
        if not sale:
            raise ValueError(f"Venta {sale_id} no encontrada")

        if sale.invoice_pdf_path and Path(sale.invoice_pdf_path).exists():
            pdf_path = Path(sale.invoice_pdf_path)
        else:
            pdf_path = self.generate_pdf(sale_id)

        try:
            os.startfile(str(pdf_path), "print")
        except Exception as e:
            raise RuntimeError(f"No se pudo imprimir: {e}")

        return pdf_path

    def send_email(self, sale_id: int) -> bool:
        """Genera (si no existe) y envía la factura por correo al cliente vía Gmail."""
        sale = self.session.get(Sale, sale_id)
        if not sale:
            raise ValueError(f"Venta {sale_id} no encontrada")

        if not sale.customer or not sale.customer.email:
            raise ValueError("El cliente no tiene un correo electrónico registrado.")

        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            raise ValueError("Las credenciales de Gmail no están configuradas en el archivo .env")

        if sale.invoice_pdf_path and Path(sale.invoice_pdf_path).exists():
            pdf_path = Path(sale.invoice_pdf_path)
        else:
            pdf_path = self.generate_pdf(sale_id)

        msg = EmailMessage()
        msg["Subject"] = f"Factura {sale.invoice_number} — {APP_NAME}"
        msg["From"] = GMAIL_USER
        msg["To"] = sale.customer.email
        msg.set_content(
            f"Hola {sale.customer.full_name},\n\n"
            f"Adjuntamos tu factura {sale.invoice_number} por un total de ${sale.total:,.0f}.\n\n"
            f"Gracias por tu compra.\n\n{APP_NAME}"
        )

        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=pdf_path.name,
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)

        return True