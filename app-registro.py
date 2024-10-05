import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Función para ejecutar consultas SQL con manejo de errores y asegurar la conexión
def execute_query(query, params=()):
    try:
        conn = sqlite3.connect('usuarios.db', check_same_thread=False)
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        result = c.fetchall()
        return result
    except sqlite3.IntegrityError as e:
        st.error('Error: El correo electrónico ya está registrado. Por favor, use otro correo electrónico.')
        return None
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
            email TEXT NOT NULL UNIQUE,
            asistencia INTEGER DEFAULT 0
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
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración'])

    if menu == 'Registro':
        st.title('Registro de Evento')

        nombre = st.text_input('Nombre')
        email = st.text_input('Email')

        if st.button('Registrarse'):
            if nombre and email:
                result = execute_query('INSERT INTO usuarios (nombre, email, asistencia) VALUES (?, ?, 0)', (nombre, email))
                if result is not None:
                    user_id = execute_query('SELECT last_insert_rowid()', ())[0][0]

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

        if st.button('Confirmar'):
            if email:
                user = execute_query('SELECT id FROM usuarios WHERE email = ?', (email,))
                if user and len(user) > 0:
                    user_id = user[0][0]
                    if execute_query('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,)) is not None:
                        st.success('¡Asistencia confirmada!')
                else:
                    st.error('Correo electrónico no encontrado.')
            else:
                st.error('Por favor, ingrese su correo electrónico.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Solicitar contraseña de administrador
        password = st.text_input('Contraseña de administrador', type='password')

        if st.button('Ingresar'):
            admin_password = 'admin123'  # Contraseña fija para acceso administrativo
            if password == admin_password:
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
                st.error('Contraseña de administrador incorrecta.')
