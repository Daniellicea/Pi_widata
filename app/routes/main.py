import io
import qrcode
from flask import Blueprint, render_template, send_file, request

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('main/index.html')

@main.route('/academia')
def academy():
    return render_template('main/academy.html')

@main.route('/faq')
def faq():
    return render_template('main/faq.html')

@main.route('/qr')
def qr_page():
    """Página pública que muestra el código QR del sistema."""
    base_url = request.host_url.rstrip('/')
    return render_template('main/qr.html', base_url=base_url)

@main.route('/generar-qr')
def generar_qr():
    """Genera y devuelve la imagen del código QR como PNG."""
    try:
        base_url = request.host_url.rstrip('/')
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(base_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#820ad1", back_color="white")
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    except Exception as e:
        return f"Error al generar QR: {str(e)}", 500

