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
conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Crear la tabla de usuarios si no existe
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        asistencia INTEGER DEFAULT 0
    )
''')
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
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración'])

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

        # Pedir el ID del usuario manualmente para pruebas locales
        user_id = st.text_input('Ingrese el ID de usuario para confirmar la asistencia')

        if st.button('Confirmar'):
            if user_id:
                # Actualizar el registro en la base de datos
                c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
                conn.commit()
                st.success('¡Asistencia confirmada!')
            else:
                st.error('No se proporcionó un ID de usuario válido.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Solicitar credenciales de administrador
        admin_user = st.text_input('Usuario administrador')
        admin_password = st.text_input('Contraseña', type='password')

        if st.button('Ingresar'):
            if admin_user == 'admin' and admin_password == 'admin123':
                # Mostrar los usuarios registrados
                df = pd.read_sql_query('SELECT * FROM usuarios', conn)
                st.dataframe(df)

                if st.button('Exportar a Excel'):
                    df.to_excel('registro_usuarios.xlsx', index=False)
                    st.success('Datos exportados exitosamente.')
            else:
                st.error('Credenciales de administrador incorrectas.')


'''
import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd

# Configurar la conexión a la base de datos
conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Crear la tabla de usuarios si no existe
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL,
        asistencia INTEGER DEFAULT 0
    )
''')
conn.commit()

# Obtener los parámetros de la URL
query_params = st.query_params
user_id = query_params.get('user_id', [None])[0]

# Si el parámetro user_id está presente y válido, confirmar asistencia automáticamente
if user_id and user_id != 'None':
    st.title('Confirmación de Asistencia')
    c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
    conn.commit()
    st.success('¡Asistencia confirmada!')
else:
    # Menú lateral para navegar entre las opciones
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración'])

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
            else:
                st.error('Por favor, completa todos los campos.')

    elif menu == 'Confirmar Asistencia':
        st.title('Confirmación de Asistencia')

        # Pedir el ID del usuario manualmente para pruebas locales
        user_id = st.text_input('Ingrese el ID de usuario para confirmar la asistencia')

        if st.button('Confirmar'):
            if user_id:
                # Actualizar el registro en la base de datos
                c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
                conn.commit()
                st.success('¡Asistencia confirmada!')
            else:
                st.error('No se proporcionó un ID de usuario válido.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Mostrar los usuarios registrados
        df = pd.read_sql_query('SELECT * FROM usuarios', conn)
        st.dataframe(df)
'''
        if st.button('Exportar a Excel'):
            df.to_excel('registro_usuarios.xlsx', index=False)
            st.success('Datos exportados exitosamente.')
