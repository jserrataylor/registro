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
            qr_data = f'https://tusitio.com/?user_id={user_id}'
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

    if st.button('Exportar a Excel'):
        df.to_excel('registro_usuarios.xlsx', index=False)
        st.success('Datos exportados exitosamente.')
