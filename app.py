from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import Flask, request, abort, send_file, session, redirect, url_for, flash
import os, secrets, io, textwrap
import mysql.connector
import time, urllib.parse, json
from collections import Counter
from datetime import timedelta, date, datetime
from flask import jsonify, request
import mariadb
from fpdf import FPDF




app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cámbiala por una cadena segura
app.permanent_session_lifetime = timedelta(hours=4)  # Expiración de sesión de 4 horas

# Configuración de la base de datos
db_config = {
    'host': '127.0.0.1',
    'user': 'if0_38210727',
    'password': 'yBxDZHWJ45vhR',
    'database': 'if0_38210727_doroti'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

SESSION_EXPIRATION_TIME = 14400  # 4 horas en segundos

def check_session_expiration():
    """Revisa si la sesión ha expirado. Si es así, se borra la sesión."""
    if 'LAST_ACTIVITY' in session:
        if time.time() - session['LAST_ACTIVITY'] > SESSION_EXPIRATION_TIME:
            session.clear()
            return False
    session['LAST_ACTIVITY'] = time.time()
    return True


def get_carpetas(user_id):
    """Consulta las carpetas activas para el usuario dado."""
    conn = None
    cursor = None
    carpetas = []
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Carpetas WHERE Estado = 'A' AND user_id = %s ORDER BY Caja"
        cursor.execute(query, (user_id,))
        carpetas = cursor.fetchall()
    except Exception as e:
        flash(f"Error en la consulta: {e}", "danger")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    return carpetas


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated') and check_session_expiration():
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username and password:
            conn = None
            cursor = None
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                query = "SELECT id, password FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                if row:
                    user_id, db_password = row
                    if password == db_password:  # Si usas hashes, reemplaza por una función de verificación
                        session['authenticated'] = True
                        session['username'] = username
                        session['user_id'] = user_id
                        session['LAST_ACTIVITY'] = time.time()
                        return redirect(url_for('index'))
                    else:
                        error = "Contraseña incorrecta."
                else:
                    error = "Usuario no encontrado."
            except Exception as e:
                error = f"Error en la base de datos: {e}"
            finally:
                if cursor is not None:
                    cursor.close()
                if conn is not None:
                    conn.close()
        else:
            error = "Por favor, completa todos los campos."
    
    return render_template('login.html', error=error)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Verificar autenticación y expiración de sesión
    if not session.get('authenticated') or not check_session_expiration():
        return redirect(url_for('login'))
    
    # Manejo de cierre de sesión si se envía el formulario
    if request.method == 'POST':
        if 'cerrar_seccion' in request.form:
            session.clear()
            return redirect(url_for('login'))
        # Patrón POST/Redirect/GET
        return redirect(url_for('index'))
    
    # Generar token CSRF si no existe
    if 'csrf_token' not in session:
        session['csrf_token'] = os.urandom(32).hex()
    
    if 'user_id' not in session:
        flash("No se ha definido el ID de usuario. Por favor, inicie sesión nuevamente.", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    carpetas = get_carpetas(user_id)
    
    return render_template('index.html', carpetas=carpetas)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/agregarcarpeta', methods=['GET'])
def agregarcarpeta():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    # Asegúrate de que el token CSRF esté en la sesión
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    
    carpetas = []
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        # Usamos cursor(dictionary=True) para que cada fila sea un diccionario
        cursor = conn.cursor(dictionary=True)
        query = "SELECT Car2, Caja, Folios FROM Carpetas ORDER BY FechaIngreso DESC LIMIT 7"
        cursor.execute(query)
        carpetas = cursor.fetchall()
    except Exception as e:
        app.logger.error("Error al cargar carpetas: %s", e, exc_info=True)
        flash("Error al cargar las carpetas recientes.", "danger")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    
    return render_template('agregarcarpeta.html', csrf_token=session['csrf_token'], carpetas=carpetas)


@app.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    # Verifica si el usuario está autenticado
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Manejo del cierre de sesión
    if 'cerrar_seccion' in request.form:
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Verificar el token CSRF
        token_form = request.form.get('csrf_token')
        if not token_form or token_form != session.get('csrf_token'):
            flash("Error: Token CSRF inválido.", "danger")
            return redirect(url_for('agregarcarpeta'))
        
        # Validar campos y convertirlos a enteros
        try:
            caja = int(request.form.get('caja', '').strip())
            car2 = int(request.form.get('car2', '').strip())
        except ValueError:
            flash("Ambos campos deben ser números positivos.", "warning")
            return redirect(url_for('agregarcarpeta'))
        
        if caja <= 0 or car2 <= 0:
            flash("Ambos campos deben ser números positivos.", "warning")
            return redirect(url_for('agregarcarpeta'))
        
        # Verificar que el ID de usuario esté definido
        if 'user_id' not in session:
            flash("No se ha definido el ID de usuario. Por favor, inicie sesión nuevamente.", "danger")
            return redirect(url_for('login'))
        user_id = session['user_id']
        
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            # Verificar si la combinación de Caja y Car2 ya existe
            check_query = "SELECT COUNT(*) FROM Carpetas WHERE Caja = %s AND Car2 = %s"
            cursor.execute(check_query, (caja, car2))
            count = cursor.fetchone()[0]
            if count > 0:
                flash("Esta carpeta ya existe en la base de datos.", "warning")
                return redirect(url_for('agregarcarpeta'))
            
            # Insertar datos (Carpeta y CaCa se dejan en NULL, Serie y Subs en '', Título vacío, fechas y Folios fijos)
            insert_query = """
                INSERT INTO Carpetas (Caja, Carpeta, CaCa, Car2, Serie, Subs, Titulo, FInicial, FFinal, Folios, Estado, user_id)
                VALUES (%s, NULL, NULL, %s, '', NULL, '', '1970-01-01', '1970-01-01', 0, 'A', %s)
            """
            cursor.execute(insert_query, (caja, car2, user_id))
            conn.commit()
            
            # Guardar algunas variables en la sesión (opcional)
            session['caja'] = caja
            session['car2'] = car2
            flash("Datos guardados correctamente.", "success")
            
            # Regenera el token CSRF para evitar reenvío accidental
            session['csrf_token'] = secrets.token_hex(32)
            
            return redirect(url_for('indice'))
        except Exception as e:
            app.logger.error("Error de base de datos: %s", e, exc_info=True)
            flash("Error inesperado. Por favor, inténtalo de nuevo.", "danger")
            return redirect(url_for('agregarcarpeta'))
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
    else:
        flash("Método no permitido.", "danger")
        return redirect(url_for('agregarcarpeta'))


@app.route('/buscador', methods=['GET', 'POST'])
def buscador():
    # Verificar autenticación
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    carpetas = []
    search_query = ""
    
    # Consulta principal: obtener las carpetas
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Carpetas ORDER BY Caja DESC, Car2 ASC;"
        cursor.execute(query)
        carpetas = cursor.fetchall()
    except Exception as e:
        flash(f"Error al obtener carpetas: {e}", "danger")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    
    # Para cada carpeta, consultar su índice documental
    for carpeta in carpetas:
        conn2 = None
        cursor2 = None
        try:
            conn2 = mysql.connector.connect(**db_config)
            cursor2 = conn2.cursor(dictionary=True)
            # Ajuste en el nombre de la tabla: 'indicedocumental'
            query2 = "SELECT * FROM indicedocumental WHERE Caja = %s AND Carpeta = %s"
            cursor2.execute(query2, (carpeta['Caja'], carpeta['Car2']))
            carpeta['indice'] = cursor2.fetchall()
        except Exception as e:
            carpeta['indice'] = []  # Si hay error, dejamos una lista vacía
            flash(f"Error al obtener índice documental: {e}", "danger")
        finally:
            if cursor2 is not None:
                cursor2.close()
            if conn2 is not None:
                conn2.close()
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        carpetas = [c for c in carpetas if search_query.lower() in c.get('Titulo', '').lower()]
    
    return render_template('buscador.html', carpetas=carpetas, query=search_query)




@app.route('/indice', methods=['GET', 'POST'])
def indice():
    # Verificar autenticación
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Si se ha enviado la acción de cerrar sesión, limpiamos la sesión
    if request.method == 'POST' and 'cerrar_seccion' in request.form:
        session.clear()
        return redirect(url_for('login'))

    # Si la solicitud es POST (por ejemplo, desde el formulario en index) asignamos caja y carpeta a la sesión
    if request.method == 'POST':
        try:
            # Convertir a entero y almacenar en sesión
            session['caja'] = int(request.form.get('caja', '').strip())
            session['carpeta'] = int(request.form.get('carpeta', '').strip())
        except (ValueError, AttributeError):
            return "Parámetros inválidos. Por favor, selecciona Caja y Carpeta.", 400

    # Obtener las variables de sesión
    caja = session.get('caja')
    carpeta = session.get('carpeta')
    if caja is None or carpeta is None:
        return "Parámetros inválidos. Por favor, selecciona Caja y Carpeta.", 400

    # Consulta a la base de datos para obtener los capítulos (índice documental) de la carpeta
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql_get_capitulos = """
      SELECT id2, DescripcionUnidadDocumental, NoFolioInicio, NoFolioFin, paginas 
      FROM IndiceTemp 
      WHERE Caja = %s AND Carpeta = %s
    """
    cursor.execute(sql_get_capitulos, (caja, carpeta))
    capitulos = cursor.fetchall()
    cursor.close()
    conn.close()

    # Calcular la última página como el máximo valor de NoFolioFin
    ultima_pagina = 0
    for cap in capitulos:
        try:
            nf = int(cap['NoFolioFin'])
            if nf > ultima_pagina:
                ultima_pagina = nf
        except (ValueError, TypeError):
            pass

    # Además, obtén las etiquetas (Serie) de la base de datos en otra consulta
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM Serie")
    etiquetas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Renderiza el template 'indice.html' pasando los datos importantes
    return render_template('indice.html',
                           caja=caja,
                           carpeta=carpeta,
                           capitulos=capitulos,
                           ultima_pagina=ultima_pagina,
                           etiquetas=etiquetas)


@app.route('/tcarpeta', methods=['POST'])
def tcarpeta():
    # Extraer los datos del formulario
    caja = request.form.get('caja')
    carpeta = request.form.get('carpeta')
    folios = request.form.get('folios')
    
    # Validación básica (opcional)
    if not caja or not carpeta or not folios:
        flash("Faltan datos para terminar la carpeta.", "warning")
        return redirect(url_for('indice'))
    
    # Aquí podrías agregar la lógica para finalizar la carpeta,
    # por ejemplo, actualizar la base de datos, cerrar la sesión de edición, etc.
    
    # Luego, renderiza el template tcarpeta.html pasando las variables necesarias
    return render_template('tcarpeta.html', caja=caja, carpeta=carpeta, folios=folios)


@app.route('/agregar_capitulo', methods=['POST'])
def agregar_capitulo():
    """
    Procesa la solicitud POST para agregar un nuevo capítulo:
      - Valida y sanitiza los datos: caja, carpeta, título y página final.
      - Obtiene la última página registrada en IndiceTemp para calcular la página de inicio.
      - Calcula el número de páginas y determina el nuevo id (id2).
      - Inserta el nuevo capítulo en la tabla IndiceTemp.
      - Retorna un JSON con la información del capítulo agregado o un error en caso de fallo.
    """
    try:
        # Convertir y validar los datos enviados
        caja = int(request.form.get('caja', '').strip())
        carpeta = int(request.form.get('carpeta', '').strip())
        titulo = request.form.get('titulo', '').strip()
        paginaFinal = int(request.form.get('paginaFinal', '').strip())
    except (ValueError, AttributeError):
        return jsonify(status="error", message="Todos los campos son obligatorios y deben ser válidos."), 400

    if not titulo:
        return jsonify(status="error", message="El título no puede estar vacío."), 400

    conn = None
    cursor = None
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Obtener la última página final para la caja y carpeta dadas
        sql_last_page = """
            SELECT MAX(NoFolioFin) as ultima_pagina 
            FROM IndiceTemp 
            WHERE Caja = %s AND Carpeta = %s
        """
        cursor.execute(sql_last_page, (caja, carpeta))
        result_last_page = cursor.fetchone()
        ultima_pagina = result_last_page["ultima_pagina"] if result_last_page and result_last_page["ultima_pagina"] is not None else 0

        # La página de inicio es la última página + 1
        paginaInicio = ultima_pagina + 1

        if paginaFinal < paginaInicio:
            return jsonify(status="error", message=f"La página final debe ser mayor o igual que {paginaInicio}."), 400

        # Calcular el número de páginas
        paginas = paginaFinal - paginaInicio + 1

        # 2. Obtener el último id2 registrado para esta caja y carpeta
        sql_last_id = """
            SELECT MAX(id2) as last_id 
            FROM IndiceTemp 
            WHERE Caja = %s AND Carpeta = %s
        """
        cursor.execute(sql_last_id, (caja, carpeta))
        result_last_id = cursor.fetchone()
        last_id = result_last_id["last_id"] if result_last_id and result_last_id["last_id"] is not None else 0
        id2 = last_id + 1

        # 3. Insertar el nuevo capítulo en la tabla IndiceTemp
        sql_insert = """
            INSERT INTO IndiceTemp (id2, Caja, Carpeta, DescripcionUnidadDocumental, NoFolioInicio, NoFolioFin, paginas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (id2, caja, carpeta, titulo, paginaInicio, paginaFinal, paginas))
        conn.commit()

        # Responder con JSON con los datos del nuevo capítulo
        return jsonify(
            status="success",
            capitulo={
                "id": id2,
                "titulo": titulo,
                "pagina_inicio": paginaInicio,
                "pagina_final": paginaFinal,
                "num_paginas": paginas
            }
        )
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/actualizar_orden', methods=['GET', 'POST'])
def actualizar_orden():
    try:
        # Obtener el parámetro 'data'
        if request.method == 'GET':
            data = request.args.get('data')
        else:
            data = request.form.get('data')
        
        if not data:
            return jsonify(status="error", message="No se recibieron datos"), 400
        
        # Decodificar la cadena URL (similar a urldecode en PHP)
        data_decoded = urllib.parse.unquote(data)
        jsonData = json.loads(data_decoded)
        
        # Extraer los datos necesarios
        cambios = jsonData.get("cambios")
        caja = jsonData.get("caja")
        carpeta = jsonData.get("carpeta")
        
        if cambios is None or caja is None or carpeta is None:
            return jsonify(status="error", message="Datos incompletos"), 400
        
        # Conectar a la base de datos y preparar la consulta
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE IndiceTemp 
            SET NoFolioInicio = %s, NoFolioFin = %s, DescripcionUnidadDocumental = %s, paginas = %s 
            WHERE id2 = %s AND Caja = %s AND Carpeta = %s
        """
        
        # Recorrer cada cambio y ejecutar la actualización
        for capitulo in cambios:
            inicio = capitulo.get("inicio")
            fin = capitulo.get("fin")
            titulo = capitulo.get("titulo")
            paginas = capitulo.get("paginas")
            id2 = capitulo.get("id")
            
            cursor.execute(sql, (inicio, fin, titulo, paginas, id2, caja, carpeta))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify(status="success", message="Actualización exitosa")
    except Exception as e:
        return jsonify(status="error", message="Error al actualizar: " + str(e)), 500


@app.route('/eliminar_capitulo', methods=['POST'])
def eliminar_capitulo():
    # Verificar que el usuario esté autenticado
    if not session.get('authenticated'):
        return jsonify(status="error", message="No autorizado"), 401

    # Obtener y validar los parámetros enviados (id, caja, carpeta)
    try:
        id_capitulo = int(request.form.get('id'))
        caja = int(request.form.get('caja'))
        carpeta = int(request.form.get('carpeta'))
    except (ValueError, TypeError):
        return jsonify(status="error", message="Parámetros no válidos"), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Iniciar la transacción
        conn.start_transaction()

        # Paso 1: Eliminar el capítulo
        sql_delete = "DELETE FROM IndiceTemp WHERE id2 = %s AND Caja = %s AND Carpeta = %s"
        cursor.execute(sql_delete, (id_capitulo, caja, carpeta))

        # Paso 2: Obtener los capítulos restantes, ordenados por id2
        sql_select = "SELECT id2, paginas FROM IndiceTemp WHERE Caja = %s AND Carpeta = %s ORDER BY id2 ASC"
        cursor.execute(sql_select, (caja, carpeta))
        capitulos = cursor.fetchall()

        # Paso 3: Recalcular páginas y actualizar cada capítulo
        siguiente_pagina = 1
        sql_update = """
            UPDATE IndiceTemp
            SET NoFolioInicio = %s, NoFolioFin = %s, id2 = %s
            WHERE Caja = %s AND Carpeta = %s AND id2 = %s
        """
        for index, capitulo in enumerate(capitulos):
            pagina_inicio = siguiente_pagina
            pagina_final = pagina_inicio + capitulo['paginas'] - 1
            nuevo_id2 = index + 1  # Nuevo id2 basado en el orden
            cursor.execute(sql_update, (pagina_inicio, pagina_final, nuevo_id2, caja, carpeta, capitulo['id2']))
            siguiente_pagina = pagina_final + 1

        # Confirmar la transacción
        conn.commit()

        return jsonify(status="success", message="Capítulo eliminado y páginas recalculadas correctamente")
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify(status="error", message="Error al actualizar: " + str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/obtener_capitulos', methods=['GET'])
def obtener_capitulos():
    caja = request.args.get("caja", type=int)
    carpeta = request.args.get("carpeta", type=int)

    if caja is None or carpeta is None:
        return jsonify({'status': 'error', 'message': 'Parámetros inválidos.'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'status': 'error', 'message': 'No se pudo conectar a la base de datos.'}), 500

    try:
        cursor = conn.cursor(dictionary=True)  # Permite obtener resultados como diccionarios

        query = """
            SELECT id2 AS id, DescripcionUnidadDocumental AS titulo, paginas, 
                   NoFolioInicio AS paginaInicio, NoFolioFin AS paginaFinal 
            FROM IndiceTemp 
            WHERE Caja = %s AND Carpeta = %s
        """
        cursor.execute(query, (caja, carpeta))
        capitulos = cursor.fetchall()

        return jsonify(capitulos)  # Devuelve los capítulos en formato JSON
    except mariadb.Error as e:
        print(f"Error en la consulta: {e}")
        return jsonify({'status': 'error', 'message': 'Error al obtener los capítulos.'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/actualizar_titulo', methods=['POST'])
def actualizar_titulo():
    try:
        id2 = int(request.form.get('id'))
        caja = int(request.form.get('caja'))
        carpeta = int(request.form.get('carpeta'))
        titulo = request.form.get('titulo', '').strip()
        if not titulo:
            return jsonify(status="error", message="El título no puede estar vacío."), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE IndiceTemp 
            SET DescripcionUnidadDocumental = %s 
            WHERE id2 = %s AND Caja = %s AND Carpeta = %s
        """
        cursor.execute(sql, (titulo, id2, caja, carpeta))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(status="success")
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500


@app.route('/actualizar_final', methods=['POST'])
def actualizar_final():
    try:
        # Obtener datos del formulario
        id = int(request.form.get('id'))
        caja = int(request.form.get('caja'))
        carpeta = int(request.form.get('carpeta'))
        pagina_final = int(request.form.get('paginaFinal'))
        
        # Lógica para actualizar la página final en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE IndiceTemp
            SET NoFolioFin = %s
            WHERE id2 = %s AND Caja = %s AND Carpeta = %s
        """
        cursor.execute(sql, (pagina_final, id, caja, carpeta))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify(status="success", message="Página final actualizada")
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500


@app.route('/pdf/rotulo-carpeta', methods=['POST'])
def rotulo_carpeta():
    # Verificar que se envió el parámetro 'consulta'
    if 'consulta' not in request.form:
        abort(400, description="Falta el parámetro 'consulta'")
    try:
        idpost = int(request.form['consulta'])
    except ValueError:
        abort(400, description="El parámetro 'consulta' debe ser un entero.")

    # Consulta a la base de datos para obtener los datos de la carpeta
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Carpetas WHERE id = %s"
        cursor.execute(query, (idpost,))
        fila = cursor.fetchone()
    except Exception as e:
        app.logger.error("Error de base de datos: %s", e)
        abort(500, description="Error en la base de datos.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if not fila:
        abort(404, description="Carpeta no encontrada.")

    # Extraer campos (ajusta los nombres según tu base de datos)
    Caja = fila.get('Caja')
    Car2 = fila.get('Car2')
    Serie = fila.get('Serie') or ""
    Subs = fila.get('Subs') or ""
    Titulo = fila.get('Titulo') or ""
    FInicial = fila.get('FInicial') or ""
    FFinal = fila.get('FFinal') or ""
    Folios = fila.get('Folios') or ""

    # Definir la clase PDF heredada de FPDF (para agregar el header con imagen)
    class PDF(FPDF):
        def header(self):
            # Agregar logo (ajusta la ruta según tu estructura)
            try:
                self.image("static/img/flayer seminario mujeres.jpeg", 0, 0, -50)
            except Exception as e:
                app.logger.error("Error al cargar la imagen del header: %s", e)

    # Crear el objeto PDF (formato: Horizontal, unidades en mm, tamaño personalizado)
    pdf = PDF('L', 'mm', (216, 330))
    pdf.set_title(f"{Car2} Carpeta (Caja {Caja})")
    pdf.add_page()
    pdf.alias_nb_pages()
    # Fondo: imagen de fondo (ajusta la ruta y dimensiones según corresponda)
    try:
        pdf.image("static/img/Carpeta AYC-GDO-FR-19.jpg", 0, 0, 335)
    except Exception as e:
        app.logger.error("Error al cargar la imagen de fondo: %s", e)
    pdf.set_font('Arial', '', 9)

    # Serie
    pdf.set_xy(42.3, 91.5)
    pdf.multi_cell(87, 6.1, Serie, 0)
    # Subs
    pdf.set_xy(42.3, 99.1)
    pdf.multi_cell(87, 6.8, Subs, 0)
    # Título Carpeta
    pdf.set_xy(42.3, 107.3)
    pdf.multi_cell(87, 6.2, Titulo, 0)
    # Número de Carpeta (Car2)
    pdf.set_xy(134.1, 109.9)
    pdf.multi_cell(24.1, 10, str(Car2), 0, 'C')
    # Título Expediente (vacío)
    pdf.set_xy(42.3, 121.4)
    pdf.multi_cell(87, 8.5, "", 0)
    # Total Folios
    pdf.set_xy(134.1, 124.1)
    pdf.multi_cell(24.1, 5.7, str(Folios), 0, 'C')
    # Caja
    pdf.set_xy(134.1, 134.9)
    pdf.multi_cell(24.1, 6.6, str(Caja), 0, 'C')
    # Folios 2
    pdf.set_xy(89, 142.9)
    pdf.multi_cell(30.6, 6.8, str(Folios), 0, 'C')

    # Procesar la fecha inicial
    try:
        fecha_inicial = time.strptime(FInicial, "%Y-%m-%d")
        Iano = time.strftime("%Y", fecha_inicial)
        Imes = time.strftime("%m", fecha_inicial)
        Idia = time.strftime("%d", fecha_inicial)
    except Exception:
        Iano = Imes = Idia = ""
    pdf.set_xy(55.2, 154.5)
    pdf.multi_cell(14.4, 4.5, Iano, 0, 'C')
    pdf.set_xy(69.7, 154.5)
    pdf.multi_cell(14.4, 4.5, Imes, 0, 'C')
    pdf.set_xy(84.2, 154.5)
    pdf.multi_cell(14.4, 4.5, Idia, 0, 'C')

    # Procesar la fecha final
    try:
        fecha_final = time.strptime(FFinal, "%Y-%m-%d")
        Fano = time.strftime("%Y", fecha_final)
        Fmes = time.strftime("%m", fecha_final)
        Fdia = time.strftime("%d", fecha_final)
    except Exception:
        Fano = Fmes = Fdia = ""
    pdf.set_xy(118, 154.5)
    pdf.multi_cell(12.8, 4.5, Fano, 0, 'C')
    pdf.set_xy(130.9, 154.5)
    pdf.multi_cell(12.8, 4.5, Fmes, 0, 'C')
    pdf.set_xy(143.7, 154.5)
    pdf.multi_cell(12.8, 4.5, Fdia, 0, 'C')

    # Generar el PDF en un stream de bytes (pdf.output ya devuelve un bytearray)
    pdf_output = pdf.output(dest='S')
    
    # Enviar el PDF para visualizarlo en el navegador (Content-Disposition inline)
    return send_file(
        io.BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=False  # Esto permite que se muestre en línea
    )


@app.route('/pdf/rotulo-caja', methods=['POST'])
def rotulo_caja():
    # Validar y obtener el valor de 'consulta'
    if 'consulta' not in request.form:
        abort(400, description="Falta el parámetro 'consulta'")
    try:
        idpost = int(request.form['consulta'])
    except ValueError:
        abort(400, description="El parámetro 'consulta' debe ser un entero.")
    
    # Consultar la base de datos para obtener todas las filas donde Caja = idpost
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Carpetas WHERE Caja = %s"
        cursor.execute(query, (idpost,))
        rows = cursor.fetchall()
    except Exception as e:
        app.logger.error("Error de base de datos: %s", e)
        abort(500, description="Error en la base de datos.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    if not rows:
        abort(404, description="No se encontraron registros para la Caja solicitada.")
    
    # Inicializar variables para fechas, series, títulos, etc.
    # Trabajamos con objetos de tipo date para las fechas
    FInicial = date.today()
    FFinal = None
    series = []
    titulos = []
    subSerie = ""
    caja = ""
    numeroCarpeta = ""
    
    # Procesar cada fila
    for row in rows:
        caja = row.get('Caja')
        numeroCarpeta = row.get('Car2')  # Número de carpeta
        serie = row.get('Serie') or ""
        subSerie = row.get('Subs') or ""
        titulo = row.get('Titulo') or ""
        
        # Convertir fechas a objetos date (si son cadenas)
        row_FInicial = row.get('FInicial')
        row_FFinal = row.get('FFinal')
        if row_FInicial:
            if isinstance(row_FInicial, str):
                try:
                    row_FInicial = datetime.strptime(row_FInicial, "%Y-%m-%d").date()
                except Exception:
                    row_FInicial = None
        if row_FFinal:
            if isinstance(row_FFinal, str):
                try:
                    row_FFinal = datetime.strptime(row_FFinal, "%Y-%m-%d").date()
                except Exception:
                    row_FFinal = None
        
        if row_FInicial and row_FInicial < FInicial:
            FInicial = row_FInicial
        if row_FFinal:
            if FFinal is None or row_FFinal > FFinal:
                FFinal = row_FFinal
        
        series.append(serie)
        titulos.append(titulo)
    
    # Contar la frecuencia de cada serie y obtener la más frecuente
    if series:
        mostFrequentSerie = Counter(series).most_common(1)[0][0]
    else:
        mostFrequentSerie = ""
    
    # Crear la clase PDF con encabezado
    class PDF(FPDF):
        def header(self):
            try:
                self.image("static/img/Caja AYC-GDO-FR-18 top.png", 0, 0, 175)
            except Exception as e:
                app.logger.error("Error al cargar la imagen del header: %s", e)
    
    # Crear el objeto PDF (formato: Vertical, unidades en mm, tamaño personalizado)
    pdf = PDF('P', 'mm', (216, 330))
    pdf.set_title(f"{caja} Caja")
    pdf.add_page()
    pdf.alias_nb_pages()
    pdf.set_font('Arial', '', 9)
    
    # Imprimir Serie y Sub-serie
    pdf.set_xy(47.3, 84)
    pdf.multi_cell(87, 6.1, mostFrequentSerie, 0)
    pdf.set_xy(47.3, 95)
    pdf.multi_cell(87, 6.8, subSerie, 0)
    
    # Imprimir listado de títulos y numeración
    posY = 117  # Posición Y inicial
    lineHeight = 5
    contador = 1
    for titulo in titulos:
        # Ajustar el texto en líneas de máximo 62 caracteres
        titulo_lines = textwrap.wrap(titulo, 62)
        for line in titulo_lines:
            pdf.set_xy(45.5, posY)
            # Corregido: usamos 'L' (alineación izquierda) en lugar de 1
            pdf.multi_cell(103.4, lineHeight, line, 1, 'L')
            pdf.set_xy(149, posY)
            pdf.multi_cell(17.8, lineHeight, str(contador), 1, 'C')
            contador += 1
            posY += lineHeight
    
    # Etiqueta "CONTENIDO"
    pdf.set_xy(10, 117)
    pdf.multi_cell(30.8, (posY - 117), "CONTENIDO", 1, 'C')
    
    # Ajuste dinámico para la imagen inferior según la cantidad de registros
    ajusteImagen = 0
    if contador == 5:
        ajusteImagen -= 20
    elif contador == 6:
        ajusteImagen -= 15
    elif contador == 7:
        ajusteImagen -= 10
    elif contador == 8:
        ajusteImagen -= 5
    elif contador == 9:
        ajusteImagen += 0
    elif contador == 10:
        ajusteImagen += 5
    elif contador == 11:
        ajusteImagen += 10
    elif contador == 12:
        ajusteImagen += 15
    
    try:
        pdf.image("static/img/Caja AYC-GDO-FR-18 below.png", 0, ajusteImagen, 175)
    except Exception as e:
        app.logger.error("Error al cargar la imagen inferior: %s", e)
    
    # Procesar las fechas para imprimir
    try:
        Iano, Imes, Idia = FInicial.isoformat().split('-')
    except Exception:
        Iano = Imes = Idia = ""
    try:
        Fano, Fmes, Fdia = FFinal.isoformat().split('-') if FFinal else ("", "", "")
    except Exception:
        Fano = Fmes = Fdia = ""
    
    pdf.set_font('Arial', '', 9)
    # Fecha Inicial
    pdf.set_xy(62.2, posY)
    pdf.multi_cell(14.4, 4.5, Iano, 0, 'C')
    pdf.set_xy(74.7, posY)
    pdf.multi_cell(14.4, 4.5, Imes, 0, 'C')
    pdf.set_xy(88.2, posY)
    pdf.multi_cell(14.4, 4.5, Idia, 0, 'C')
    # Fecha Final
    pdf.set_xy(125, posY)
    pdf.multi_cell(12.8, 4.5, Fano, 0, 'C')
    pdf.set_xy(138.9, posY)
    pdf.multi_cell(12.8, 4.5, Fmes, 0, 'C')
    pdf.set_xy(151.7, posY)
    pdf.multi_cell(12.8, 4.5, Fdia, 0, 'C')
    
    # Imprimir número de caja y carpeta
    posYFinal = posY + 8
    pdf.set_font('Arial', '', 14)
    pdf.set_xy(57.3, posYFinal)
    pdf.multi_cell(24.1, 6.6, str(caja), 0, 'C')
    posYFinal += 10
    pdf.set_xy(42.3, posYFinal)
    pdf.multi_cell(24.1, 10, str(numeroCarpeta), 0, 'C')
    
    # Generar el PDF en un stream de bytes (pdf.output ya devuelve un bytearray)
    pdf_output = pdf.output(dest='S')
    
    # Enviar el PDF para visualizarlo en el navegador
    return send_file(
        io.BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"Caja {caja}.pdf"
    )




if __name__ == '__main__':
    app.run(debug=True)
