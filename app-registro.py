import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import hashlib

# Función para encriptar contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para ejecutar consultas SQL con manejo de errores y asegurar la conexión
def execute_query(query, params=()):
    try:
        conn = sqlite3.connect('usuarios.db', check_same_thread=False)
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        result = c.fetchall()
        return result
    except sqlite3.OperationalError as e:
        st.error(f'Error en la base de datos: {str(e)}. Por favor, inténtelo de nuevo más tarde.')
        return None
    finally:
        conn.close()

# Crear la tabla de usuarios si no existe
def initialize_database():
    try:
        conn = sqlite3.connect('usuarios.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            asistencia INTEGER DEFAULT 0,
            es_admin INTEGER DEFAULT 0
        )
        """)
        conn.commit()
    except sqlite3.OperationalError as e:
        st.error(f'Error al inicializar la base de datos: {str(e)}')
    finally:
        conn.close()

initialize_database()

# Obtener los parámetros de la URL
query_params = st.experimental_get_query_params()
user_id = query_params.get('user_id', [None])[0]

# Si el parámetro user_id está presente y válido, confirmar asistencia automáticamente
if user_id and user_id != 'None':
    st.title('Confirmación de Asistencia')
    if execute_query('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,)) is not None:
        st.success('¡Asistencia confirmada!')
else:
    # Menú lateral para navegar entre las opciones
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración', 'Registro de Administrador'])

    if menu == 'Registro':
        st.title('Registro de Evento')

        nombre = st.text_input('Nombre')
        email = st.text_input('Email')
        password = st.text_input('Contraseña', type='password')

        if st.button('Registrarse'):
            if nombre and email and password:
                hashed_password = hash_password(password)
                result = execute_query('INSERT INTO usuarios (nombre, email, password, asistencia, es_admin) VALUES (?, ?, ?, 0, 0)', (nombre, email, hashed_password))
                if result is not None:
                    user_id = execute_query('SELECT last_insert_rowid()')[0][0]

                    # Generar el código QR
                    qr_data = f'https://registro-app.streamlit.app/?user_id={user_id}'
                    qr_img = qrcode.make(qr_data)
                    buf = BytesIO()
                    qr_img.save(buf, format='PNG')
                    byte_im = buf.getvalue()

                    st.image(byte_im, caption='Tu Código QR')
                    st.success('¡Registro exitoso! Guarda este código QR.')

                    # Enviar el correo electrónico con la información de registro y el código QR
                    try:
                        msg = MIMEMultipart()
                        msg['From'] = 'tu_correo@gmail.com'
                        msg['To'] = email
                        msg['Subject'] = 'Confirmación de Registro y Código QR'

                        # Cuerpo del correo
                        body = f'Hola {nombre},\n\nGracias por registrarte en nuestro evento.\nAdjunto encontrarás tu código QR para la confirmación de asistencia.\n\nSaludos,'
                        msg.attach(MIMEText(body, 'plain'))

                        # Adjuntar el código QR
                        image = MIMEImage(byte_im, name='codigo_qr.png')
                        msg.attach(image)

                        # Configurar servidor SMTP
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login('tu_correo@gmail.com', 'tu_contraseña')
                        server.sendmail('tu_correo@gmail.com', email, msg.as_string())
                        server.quit()

                        st.success('Correo electrónico enviado con éxito.')
                    except Exception as e:
                        st.error(f'Error al enviar el correo electrónico: {e}')
            else:
                st.error('Por favor, completa todos los campos.')

    elif menu == 'Confirmar Asistencia':
        st.title('Confirmación de Asistencia')

        email = st.text_input('Ingrese su correo electrónico para confirmar la asistencia')
        password = st.text_input('Contraseña', type='password')

        if st.button('Confirmar'):
            if email and password:
                hashed_password = hash_password(password)
                admin = execute_query('SELECT id FROM usuarios WHERE email = ? AND password = ?', (email, hashed_password))
                if admin:
                    user_id = admin[0][0]
                    if execute_query('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,)) is not None:
                        st.success('¡Asistencia confirmada!')
                else:
                    st.error('Credenciales incorrectas.')
            else:
                st.error('Por favor, ingrese sus credenciales.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Solicitar credenciales de administrador
        email = st.text_input('Correo electrónico de administrador')
        password = st.text_input('Contraseña', type='password')

        if st.button('Ingresar'):
            hashed_password = hash_password(password)
            admin = execute_query('SELECT * FROM usuarios WHERE email = ? AND password = ? AND es_admin = 1', (email, hashed_password))
            if admin:
                # Mostrar los usuarios registrados
                try:
                    conn = sqlite3.connect('usuarios.db', check_same_thread=False)
                    df = pd.read_sql_query('SELECT * FROM usuarios', conn)
                    st.dataframe(df)
                except Exception as e:
                    st.error(f'Error al acceder a los datos: {e}')
                finally:
                    conn.close()

                if st.button('Exportar a Excel'):
                    try:
                        df.to_excel('registro_usuarios.xlsx', index=False)
                        st.success('Datos exportados exitosamente.')
                    except Exception as e:
                        st.error(f'Error al exportar los datos: {e}')
            else:
                st.error('Credenciales de administrador incorrectas.')

    elif menu == 'Registro de Administrador':
        st.title('Registro de Administrador')

        nombre = st.text_input('Nombre del Administrador')
        email = st.text_input('Correo Electrónico del Administrador')
        password = st.text_input('Contraseña', type='password')

        if st.button('Registrar Administrador'):
            if nombre and email and password:
                hashed_password = hash_password(password)
                result = execute_query('INSERT INTO usuarios (nombre, email, password, asistencia, es_admin) VALUES (?, ?, ?, 0, 1)', (nombre, email, hashed_password))
                if result is not None:
                    st.success('¡Administrador registrado exitosamente!')
                else:
                    st.error('Error al registrar al administrador. Por favor, inténtelo de nuevo más tarde.')
            else:
                st.error('Por favor, complete todos los campos.')
