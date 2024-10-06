import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Función para enviar correo
def enviar_correo(destinatario, asunto, mensaje, adjunto=None):
    email_usuario = 'tu_correo@gmail.com'
    email_contraseña = 'tu_contraseña_de_aplicacion'  # Asegúrate de usar una contraseña de aplicación (Google)
    email_destino = destinatario

    msg = MIMEMultipart()
    msg['From'] = email_usuario
    msg['To'] = email_destino
    msg['Subject'] = asunto

    msg.attach(MIMEText(mensaje, 'plain'))

    if adjunto:
        # Adjuntar el archivo (en este caso el código QR)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(adjunto)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {adjunto}")
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_usuario, email_contraseña)
    text = msg.as_string()
    server.sendmail(email_usuario, email_destino, text)
    server.quit()

# Llamada a la función al registrarse el usuario
if st.button('Registrarse'):
    if nombre and email:
        try:
            c.execute('INSERT INTO usuarios (nombre, email) VALUES (?, ?)', (nombre, email))
            conn.commit()
            user_id = c.lastrowid

            # Generar el código QR
            qr_data = f'https://registro-app.streamlit.app/?user_id={user_id}'
            qr_img = qrcode.make(qr_data)
            buf = BytesIO()
            qr_img.save(buf, format='PNG')
            byte_im = buf.getvalue()

            # Enviar correo con el QR adjunto
            mensaje = f"Hola {nombre}, gracias por registrarte. Aquí está tu código QR."
            enviar_correo(email, 'Registro Confirmado', mensaje, byte_im)

            st.image(byte_im, caption='Tu Código QR')
            st.success('¡Registro exitoso! Guarda este código QR.')
        except sqlite3.IntegrityError:
            st.warning('El correo electrónico ya está registrado. Recuperando el código QR existente...')

