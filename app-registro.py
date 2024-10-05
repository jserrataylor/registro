import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl

# Función para enviar correos electrónicos
def enviar_correo(destinatario, asunto, cuerpo, qr_image=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = 'tu_correo@gmail.com'
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # Cuerpo del correo
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

        # Adjuntar el código QR si existe
        if qr_image:
            image = MIMEImage(qr_image, name='codigo_qr.png')
            msg.attach(image)

        # Configurar servidor SMTP
        context = ssl.create_default_context()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(context=context)
        server.login('tu_correo@gmail.com', 'tu_contraseña')
        server.sendmail('tu_correo@gmail.com', destinatario, msg.as_string())
        server.quit()

        st.success('Correo electrónico enviado con éxito.')
    except Exception as e:
        st.error(f'Error al enviar el correo electrónico: {e}')

# Configurar la conexión a la base de datos
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()

# Crear la tabla de usuarios si no existe
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
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
    c.execute('SELECT nombre, email FROM usuarios WHERE id = ?', (user_id,))
    user = c.fetchone()
    if user:
        c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
        conn.commit()
        st.success('¡Asistencia confirmada!')

        # Enviar correo electrónico de confirmación
        nombre, email = user
        asunto = 'Confirmación de Asistencia'
        cuerpo = f'Hola {nombre},\n\nGracias por confirmar tu asistencia al evento.\n\nSaludos,'
        enviar_correo(email, asunto, cuerpo)
    else:
        st.error('Usuario no encontrado.')
else:
    # Menú lateral para navegar entre las opciones
    menu = st.sidebar.selectbox('Seleccione una opción', ['Registro', 'Confirmar Asistencia', 'Administración'])

    if menu == 'Registro':
        st.title('Registro de Evento')

        nombre = st.text_input('Nombre')
        email = st.text_input('Email')

        if st.button('Registrarse'):
            if nombre and email:
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

                    st.image(byte_im, caption='Tu Código QR')
                    st.success('¡Registro exitoso! Guarda este código QR.')

                    # Enviar correo electrónico con la información de registro y el código QR
                    asunto = 'Confirmación de Registro y Código QR'
                    cuerpo = f'Hola {nombre},\n\nGracias por registrarte en nuestro evento.\nAdjunto encontrarás tu código QR para la confirmación de asistencia.\n\nSaludos,'
                    enviar_correo(email, asunto, cuerpo, qr_image=byte_im)
                except sqlite3.IntegrityError:
                    st.warning('El correo electrónico ya está registrado. Si ya te has registrado, verifica tu correo para obtener tu código QR.')
            else:
                st.error('Por favor, completa todos los campos.')

    elif menu == 'Confirmar Asistencia':
        st.title('Confirmación de Asistencia')

        # Solicitar contraseña de administrador
        password = st.text_input('Contraseña de administrador', type='password')

        if st.button('Ingresar'):
            admin_password = 'admin123'  # Contraseña fija para acceso administrativo
            if password == admin_password:
                st.success('Acceso concedido. Ahora puede confirmar la asistencia de los usuarios.')

                # Mostrar la opción para confirmar asistencia
                email = st.text_input('Ingrese el correo electrónico del usuario para confirmar la asistencia')
                if st.button('Confirmar Asistencia'):
                    if email:
                        c.execute('SELECT id, nombre FROM usuarios WHERE email = ?', (email,))
                        user = c.fetchone()
                        if user:
                            user_id, nombre = user
                            # Actualizar el registro en la base de datos para confirmar asistencia
                            c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
                            conn.commit()
                            st.success('¡Asistencia confirmada y registrada en la base de datos!')

                            # Verificar si la actualización se realizó correctamente
                            c.execute('SELECT asistencia FROM usuarios WHERE id = ?', (user_id,))
                            asistencia = c.fetchone()[0]
                            if asistencia == 1:
                                # Enviar correo electrónico de confirmación
                                asunto = 'Confirmación de Asistencia'
                                cuerpo = f'Hola {nombre},\n\nGracias por confirmar tu asistencia al evento.\n\nSaludos,'
                                enviar_correo(email, asunto, cuerpo)
                            else:
                                st.error('Error al registrar la asistencia en la base de datos. Intente nuevamente.')
                        else:
                            st.error('Correo electrónico no encontrado.')
                    else:
                        st.error('Por favor, ingrese el correo electrónico del usuario.')
            else:
                st.error('Contraseña de administrador incorrecta.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Solicitar contraseña de administrador
        password = st.text_input('Contraseña de administrador', type='password')

        if st.button('Ingresar'):
            admin_password = 'admin123'  # Contraseña fija para acceso administrativo
            if password == admin_password:
                # Mostrar los usuarios registrados
                df = pd.read_sql_query('SELECT * FROM usuarios', conn)
                st.dataframe(df)

                if st.button('Exportar a Excel'):
                    df.to_excel('registro_usuarios.xlsx', index=False)
                    st.success('Datos exportados exitosamente.')
            else:
                st.error('Contraseña de administrador incorrecta.')
