from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from fpdf import FPDF
import base64
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from werkzeug.utils import secure_filename

def agregar_logo(pdf):
    """ Agrega el logo en la parte superior derecha del PDF si el archivo existe. """
    logo_path = "logo_msi.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=160, y=10, w=40)  # Ajuste de posición y tamaño

def generar_pdf(datos, firma_b64):
    pdf_path = "registro_servicio.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # Agregar el logo
    agregar_logo(pdf)

    pdf.cell(200, 10, "MONTAJES Y SOLUCIONES INDUSTRIALES S.A.S.", ln=True, align='C')
    pdf.cell(200, 10, "Calle 75B #64A - 23, Medellín - Colombia", ln=True, align='C')
    pdf.cell(200, 10, "Tel: (57 4) 322 26 18 - 300 535 9176 - 304 606 9187", ln=True, align='C')
    pdf.cell(200, 10, "Email: cyp@montajesysolucionesindustriales.com.co", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(200, 10, "REGISTRO DE SERVICIO AL CLIENTE", ln=True, align='C')
    pdf.ln(5)

    campos = [
        ("Ciudad", "Empresa"),
        ("Fecha", "Contacto"),
        ("No_Obra", "Tipo_Equipo"),
        ("Asignado_A", "Marca_Año_Serie"),
        ("Fecha_Hora_Ingreso", "Fecha_Hora_Salida"),
    ]

    for izq, der in campos:
        pdf.cell(95, 10, f"{izq}: {datos.get(izq, '')}", border=1)
        pdf.cell(95, 10, f"{der}: {datos.get(der, '')}", border=1, ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, "DESCRIPCIÓN:", ln=True)
    pdf.multi_cell(190, 7, datos.get("Descripcion", ""))
    pdf.ln(5)

    pdf.cell(200, 10, "FIRMA CLIENTE:", ln=True)

    if firma_b64:
        firma_data = base64.b64decode(firma_b64.split(',')[1])
        firma_path = "firma.png"
        with open(firma_path, "wb") as f:
            f.write(firma_data)
        pdf.image(firma_path, x=10, y=pdf.get_y(), w=50)
        os.remove(firma_path)

    pdf.output(pdf_path)
    return pdf_path

def enviar_correo(destinatario, archivos, empresa, fecha):
    try:
        remitente = "diroperacionesmsi@gmail.com"
        password = "fdnc isdn owdg zzxr"
        destinatarios = [destinatario, "diroperaciones@montajesysolucionesindustriales.com.co"]

        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios)
        msg['Subject'] = f"Acta de entrega {empresa} {fecha}"

        cuerpo = """Buen día

A continuación se adjunta el acta de entrega y evidencias fotográficas del trabajo realizado."""
        msg.attach(MIMEText(cuerpo, 'plain'))

        for archivo in archivos:
            with open(archivo, "rb") as adjunto:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(adjunto.read())
                encoders.encode_base64(parte)
                parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(archivo)}")
                msg.attach(parte)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatarios, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error enviando correo: {e}")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

@app.route('/firma', methods=['GET', 'POST'])
def firma():
    if request.method == 'POST':
        # Aquí se procesaría la firma si fuera necesario
        return redirect(url_for('formulario'))  # Redirige a formulario.html después de guardar la firma

    return render_template('firma.html')

@app.route('/enviar', methods=['POST'])
def enviar():
    datos = request.form.to_dict()
    firma_b64 = datos.pop('firma', None)
    pdf_path = generar_pdf(datos, firma_b64)
    destinatario = datos.get('email')
    empresa = datos.get('Empresa', 'SIN_EMPRESA')
    fecha = datos.get('Fecha', 'SIN_FECHA')

    archivos = [pdf_path]

    if 'imagenes' in request.files:
        imagenes = request.files.getlist('imagenes')
        imagen_paths = []
        for imagen in imagenes:
            if imagen.filename:
                filename = secure_filename(imagen.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(filepath)
                imagen_paths.append(filepath)
        archivos.extend(imagen_paths)

    enviar_correo(destinatario, archivos, empresa, fecha)

    os.remove(pdf_path)
    for imagen_path in archivos[1:]:  # Eliminar imágenes temporales
        os.remove(imagen_path)

    return redirect(url_for('formulario'))

if __name__ == '__main__':
    app.run(debug=True)
