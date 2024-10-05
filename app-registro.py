import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import hashlib

# Configurar la conexión a la base de datos
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()

# Crear la tabla de usuarios y administradores si no existen
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        asistencia INTEGER DEFAULT 0
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')
conn.commit()

# Función para generar un hash de la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para enviar correo
def enviar_correo(destinatario, asunto, mensaje, adjunto=None):
    email_usuario = 'tu_correo@gmail.com'
    email_contraseña = 'tu_contraseña_de_aplicacion'  # Usa una contraseña de aplicación generada por tu servicio de correo
    email_destino = destinatario

    msg = MIMEMultipart()
    msg['From'] = email_usuario
    msg['To'] = email_destino
    msg['Subject'] = asunto

    msg.attach(MIMEText(mensaje, 'plain'))

    if adjunto:
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

# Autenticación del administrador
st.sidebar.title('Iniciar Sesión')

# Registro de un nuevo administrador (solo debe hacerse manualmente una vez)
if st.sidebar.button('Registrar Admin'):
    new_username = st.sidebar.text_input('Nuevo Usuario')
    new_password = st.sidebar.text_input('Nueva Contraseña', type='password')
    if new_username and new_password:
        hashed_password = hash_password(new_password)
        try:
            c.execute('INSERT INTO admins (username, password) VALUES (?, ?)', (new_username, hashed_password))
            conn.commit()
            st.sidebar.success('Administrador registrado con éxito.')
        except sqlite3.IntegrityError:
            st.sidebar.error('El usuario ya existe.')

# Ingreso del administrador
username = st.sidebar.text_input('Usuario')
password = st.sidebar.text_input('Contraseña', type='password')
login_button = st.sidebar.button('Iniciar Sesión')

admin_logged_in = False
if login_button:
    hashed_password = hash_password(password)
    c.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, hashed_password))
    admin = c.fetchone()
    if admin:
        st.sidebar.success('Sesión iniciada.')
        admin_logged_in = True
    else:
        st.sidebar.error('Credenciales incorrectas.')

# Obtener los parámetros de la URL para confirmación de asistencia automática
query_params = st.experimental_get_query_params()
user_id = query_params.get('user_id', [None])[0]

# Si el parámetro user_id está presente y válido, confirmar asistencia automáticamente
if user_id and user_id != 'None':
    st.title('Confirmación de Asistencia')
    try:
        c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
        if c.rowcount > 0:
            conn.commit()
            
            # Enviar correo de confirmación de asistencia
            c.execute('SELECT nombre, email FROM usuarios WHERE id = ?', (user_id,))
            usuario = c.fetchone()
            nombre_usuario, email_usuario = usuario[0], usuario[1]
            mensaje = f"Hola {nombre_usuario}, hemos confirmado tu asistencia al evento."
            enviar_correo(email_usuario, 'Asistencia Confirmada', mensaje)

            st.success('¡Asistencia confirmada! Se ha enviado un correo de confirmación.')
        else:
            st.error('ID de usuario no válido.')
    except sqlite3.IntegrityError:
        st.error('Error al confirmar la asistencia. Por favor, intente nuevamente.')

else:
    # Menú lateral para navegar entre las opciones
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración'])

    if menu == 'Registro':
        st.title('Registro de Evento')

        nombre = st.text_input('Nombre')
        email = st.text_input('Email')

        if st.button('Registrarse'):
            if nombre and email:
                # Limpiar espacios en blanco del correo
                email = email.strip()

                try:
                    # Insertar los datos en la base de datos
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

                    c.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
                    result = c.fetchone()
                    if result:
                        existing_user_id = result[0]

                        # Generar el código QR existente
                        qr_data = f'https://registro-app.streamlit.app/?user_id={existing_user_id}'
                        qr_img = qrcode.make(qr_data)
                        buf = BytesIO()
                        qr_img.save(buf, format='PNG')
                        byte_im = buf.getvalue()

                        st.image(byte_im, caption='Tu Código QR')
                        st.success('Registro encontrado. Este es tu código QR.')
                    else:
                        st.error('Error al recuperar el registro existente. Por favor, inténtalo nuevamente.')
            else:
                st.error('Por favor, completa todos los campos.')

    elif menu == 'Confirmar Asistencia':
        st.title('Confirmación de Asistencia')

        # Pedir el ID del usuario manualmente para pruebas locales
        user_id = st.text_input('Ingrese el ID de usuario para confirmar la asistencia')

        if st.button('Confirmar'):
            if user_id:
                try:
                    # Actualizar el registro en la base de datos
                    c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
                    if c.rowcount > 0:
                        conn.commit()

                        # Enviar correo de confirmación de asistencia
                        c.execute('SELECT nombre, email FROM usuarios WHERE id = ?', (user_id,))
                        usuario = c.fetchone()
                        nombre_usuario, email_usuario = usuario[0], usuario[1]
                        mensaje = f"Hola {nombre_usuario}, hemos confirmado tu asistencia al evento."
                        enviar_correo(email_usuario, 'Asistencia Confirmada', mensaje)

                        st.success('¡Asistencia confirmada! Se ha enviado un correo de confirmación.')
                    else:
                        st.error('ID de usuario no válido.')
                except sqlite3.IntegrityError:
                    st.error('Error al confirmar la asistencia. Por favor, intente nuevamente.')
            else:
                st.error('No se proporcionó un ID de usuario válido.')

    elif menu == 'Administración' and admin_logged_in:
        st.title('Panel de Administración')

        # Mostrar los usuarios registrados
        df = pd.read_sql_query('SELECT * FROM usuarios', conn)
        st.dataframe(df)

        if st.button('Exportar a Excel'):
            df.to_excel('registro_usuarios.xlsx', index=False)
            st.success('Datos exportados exitosamente.')
