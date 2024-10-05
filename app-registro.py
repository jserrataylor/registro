import streamlit as st
import qrcode
from io import BytesIO
import sqlite3
import pandas as pd

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
query_params = st.query_params
user_id = query_params.get('user_id', [None])[0]

# Si el parámetro user_id está presente y válido, confirmar asistencia automáticamente
if user_id and user_id != 'None':
    st.title('Confirmación de Asistencia')
    try:
        c.execute('UPDATE usuarios SET asistencia = 1 WHERE id = ?', (user_id,))
        if c.rowcount > 0:
            conn.commit()
            st.success('¡Asistencia confirmada!')
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
                except sqlite3.IntegrityError:
                    st.warning('El correo electrónico ya está registrado. Recuperando el código QR existente...')
                    c.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
                    existing_user_id = c.fetchone()[0]

                    # Generar el código QR existente
                    qr_data = f'https://registro-app.streamlit.app/?user_id={existing_user_id}'
                    qr_img = qrcode.make(qr_data)
                    buf = BytesIO()
                    qr_img.save(buf, format='PNG')
                    byte_im = buf.getvalue()

                    st.image(byte_im, caption='Tu Código QR')
                    st.success('Registro encontrado. Este es tu código QR.')
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
                        st.success('¡Asistencia confirmada!')
                    else:
                        st.error('ID de usuario no válido.')
                except sqlite3.IntegrityError:
                    st.error('Error al confirmar la asistencia. Por favor, intente nuevamente.')
            else:
                st.error('No se proporcionó un ID de usuario válido.')

    elif menu == 'Administración':
        st.title('Panel de Administración')

        # Mostrar los usuarios registrados
        df = pd.read_sql_query('SELECT * FROM usuarios', conn)
        st.dataframe(df)

        if st.button('Exportar a Excel'):
            df.to_excel('registro_usuarios.xlsx', index=False)
            st.success('Datos exportados exitosamente.')
