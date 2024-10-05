import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Configurar la conexión a la base de datos
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()

# Crear la tabla de usuarios si no existe
c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    asistencia INTEGER DEFAULT 0,
    es_admin INTEGER DEFAULT 0
)
""")
conn.commit()

# Obtener los parámetros de la URL
query_params = st.experimental_get_query_params()
user_id = query_params.get('user_id', [None])[0]

# Si el parámetro user_id está presente y válido, confirmar asistencia automáticamente
if user_id and user_id != 'None':
    st.title('Confirmación de Asistencia')
    c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
    conn.commit()
    st.success('¡Asistencia confirmada!')
else:
    # Menú lateral para navegar entre las opciones
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración', 'Registro de Administrador'])

    if menu == 'Registro':
        st.title('Registro de Evento')

        nombre = st.text_input('Nombre')
        email = st.text_input('Email')

        if st.button('Registrarse'):
            if nombre and email:
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
                # Verificar si el usuario es administrador y existe
                c.execute('SELECT id FROM usuarios WHERE email = ? AND es_admin = 1', (email,))
                admin = c.fetchone()
                if admin:
                    user_id = admin[0]
                    c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
                    conn.commit()
                    st.success('¡Asistencia confirmada!')
                else:
                    st.error('Credenciales incorrectas o no tiene acceso de administrador.')
            else:
                st.error('Por favor, ingrese sus credenciales.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Solicitar credenciales de administrador
        email = st.text_input('Correo electrónico de administrador')
        password = st.text_input('Contraseña', type='password')

        if st.button('Ingresar'):
            # Verificar si el usuario es administrador y existe
            c.execute('SELECT * FROM usuarios WHERE email = ? AND es_admin = 1', (email,))
            admin = c.fetchone()
            if admin:
                # Mostrar los usuarios registrados
                df = pd.read_sql_query('SELECT * FROM usuarios', conn)
                st.dataframe(df)

                if st.button('Exportar a Excel'):
                    df.to_excel('registro_usuarios.xlsx', index=False)
                    st.success('Datos exportados exitosamente.')
            else:
                st.error('Credenciales de administrador incorrectas.')

    elif menu == 'Registro de Administrador':
        st.title('Registro de Administrador')

        nombre = st.text_input('Nombre del Administrador')
        email = st.text_input('Correo Electrónico del Administrador')
        password = st.text_input('Contraseña', type='password')

        if st.button('Registrar Administrador'):
            if nombre and email and password:
                # Insertar los datos del administrador en la base de datos
                c.execute('INSERT INTO usuarios (nombre, email, es_admin) VALUES (?, ?, 1)', (nombre, email))
                conn.commit()
                st.success('¡Administrador registrado exitosamente!')
            else:
                st.error('Por favor, complete todos los campos.')
