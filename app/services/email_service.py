import smtplib
from email.message import EmailMessage
from flask import current_app

def send_reset_email(to_email, token):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Recuperación de Contraseña - Widata'
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = to_email

        reset_link = f"http://127.0.0.1:5000/auth/reset_password/{token}"
        msg.set_content(f'''Para restablecer tu contraseña, visita el siguiente enlace:
{reset_link}

Si no solicitaste este cambio, ignora este correo.
Este enlace expirará en 1 hora.
''')

        # Si el correo no está configurado, solo lo imprimimos por consola en debug
        if not current_app.config.get('MAIL_USERNAME'):
            print(f"DEBUG EMAIL TO: {to_email}\nLINK: {reset_link}")
            return True

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
