import os
from contextlib import contextmanager
from dotenv import load_dotenv
from functools import wraps

import pymysql
from pymysql.cursors import DictCursor
from flask import Flask, abort, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'solo-desarrollo-cambiar-esta-clave')


@contextmanager
def db():
    connection = pymysql.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ.get('DB_PORT', '3306')),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'],
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False,
        ssl={
            'ca': os.environ['DB_SSL_CA']
        }
    )

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

@app.route('/test-db')
def test_db():
    try:
        with db() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() AS version")
                result = cursor.fetchone()

        return {
            "status": "ok",
            "message": "Conexión a MySQL exitosa",
            "mysql_version": result["version"]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('usuario_id'):
            return redirect(url_for('inicio_sesion'))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('usuario_id'):
            return redirect(url_for('inicio_sesion'))
        if session.get('rol') != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapper

def funcionario_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('usuario_id'):
            return redirect(url_for('inicio_sesion'))

        if session.get('rol') not in ('admin', 'funcionario'):
            abort(403)

        return view(*args, **kwargs)

    return wrapper


@app.route('/')
def inicio():
    return render_template('cliente/index.html', usuario=session.get('usuario'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')

        #Como no estan dificil saltarse las validaciones de la pagina, los modificare directamente en este apartado con lo que quiero que pida
        #Este codigo es reciclado de cuando intente hacer una pagina propia jaja, si quieres modifica alguna parte que no te guste
        if not nombre or not correo or not password:
            return render_template('cliente/registro.html', error='Completa todos los campos.'), 400

        if len(password) < 8:
            return render_template('cliente/registro.html', error='La contraseña debe tener al menos 8 caracteres.'), 400

        if not any(c.isupper() for c in password):
            return render_template('cliente/registro.html', error='La contraseña debe contener al menos una mayuscula.'), 400

        if not any(c.islower() for c in password):
            return render_template('cliente/registro.html', error='La contraseña debe contener al menos una minuscula.'), 400

        if not any(c.isdigit() for c in password):
            return render_template('cliente/registro.html', error='La contraseña debe contener al menos un numero.'), 400

        if not any(not c.isalnum() for c in password):
            return render_template('cliente/registro.html', error='La contraseña debe contener al menos un simbolo.'), 400

        try:
            with db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('INSERT INTO usuarios (nombre, correo, `contraseña`) VALUES (%s, %s, %s)',
                                   (nombre, correo, generate_password_hash(password)))
        except pymysql.err.IntegrityError:
            return render_template('cliente/registro.html', error='Ese correo ya esta registrado.'), 409

        return redirect(url_for('inicio_sesion', registrado='1'))

    return render_template('cliente/registro.html')


@app.route('/inicio-sesion', methods=['GET', 'POST'])
def inicio_sesion():
    if session.get('usuario_id'):
        return redirect(url_for('inicio_cliente'))

    if request.method == 'POST':
        with db() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT id_usuario, correo, `contraseña` AS password_hash, rol FROM usuarios WHERE correo = %s',
                    (request.form.get('correo', '').strip().lower(),)
                )
                usuario = cursor.fetchone()

        if usuario and check_password_hash(
            usuario['password_hash'],
            request.form.get('password', '')
        ):
            session.clear()
            session.update(
                usuario_id=usuario['id_usuario'],
                usuario=usuario['correo'],
                rol=usuario['rol']
            )
            return redirect(url_for('inicio_cliente'))

        return render_template(
            'cliente/inicio_sesion.html',
            error='Correo o contraseña incorrectos.'
        ), 401

    return render_template(
        'cliente/inicio_sesion.html',
        registrado=request.args.get('registrado')
    )



@app.route('/cliente/inicio')
@login_required
def inicio_cliente():
    return render_template('cliente/inicio.html')


@app.route('/cliente/cerrar-sesion')
def cerrar_sesion():
    session.clear()
    return redirect(url_for('inicio'))


@app.route('/cliente/obtener-turno')
@login_required
def obtener_turno():
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT f.id_fila AS id, CONCAT(s.nombre, ' — ', u.nombre) AS nombre
                              FROM filas f JOIN servicios s ON s.id_servicio=f.id_servicio
                              JOIN sucursales u ON u.id_sucursal=s.id_sucursal
                              WHERE f.estado='activa' AND s.estado='activo' AND u.estado='activa'
                              ORDER BY u.nombre,s.nombre,f.id_fila""")
            servicios = cursor.fetchall()
    return render_template('cliente/obtener_turno.html', servicios=servicios)


@app.route('/cliente/turno-generado', methods=['POST'])
@login_required
def turno_generado():
    try:
        servicio_id = int(request.form.get('servicio', ''))
    except ValueError:
        abort(400)
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT s.nombre, s.duracion_estimada FROM filas f
                              JOIN servicios s ON s.id_servicio=f.id_servicio
                              JOIN sucursales u ON u.id_sucursal=s.id_sucursal
                              WHERE f.id_fila=%s AND f.estado='activa'
                              AND s.estado='activo' AND u.estado='activa'""", (servicio_id,))
            servicio = cursor.fetchone()
            if not servicio:
                abort(400)
            cursor.execute('INSERT INTO turnos (id_usuario, id_fila) VALUES (%s, %s)',
                           (session['usuario_id'], servicio_id))
            turno_id = cursor.lastrowid
            numero_turno = f"A{turno_id:03d}"
            cursor.execute('UPDATE turnos SET numero = %s WHERE id_turno = %s', (numero_turno, turno_id))
            cursor.execute('''INSERT INTO notificaciones (id_usuario,id_turno,mensaje)
                              VALUES (%s,%s,%s)''',
                           (session['usuario_id'], turno_id, f'Turno {numero_turno} registrado.'))
    return render_template('cliente/turno_generado.html', numero_turno=numero_turno, servicio=servicio['nombre'])


@app.route('/cliente/gestion-turnos')
@login_required
def gestion_turnos():
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT t.numero, s.nombre AS servicio, t.estado
                              FROM turnos t JOIN filas f ON f.id_fila=t.id_fila JOIN servicios s ON s.id_servicio=f.id_servicio
                              WHERE t.id_usuario = %s ORDER BY t.id_turno''', (session['usuario_id'],))
            turnos = cursor.fetchall()
    return render_template('cliente/gestion_turnos.html', turnos=turnos)


@app.route('/cliente/consultar-turno')
@login_required
def consultar_turno():
    numero_turno = request.args.get('turno', '').strip().upper()
    turno = None
    posicion = personas_antes = tiempo_estimado = None
    if numero_turno:
        with db() as connection:
            with connection.cursor() as cursor:
                cursor.execute('''SELECT t.id_turno, t.id_fila, t.numero, t.estado, s.nombre AS servicio, s.duracion_estimada
                                  FROM turnos t JOIN filas f ON f.id_fila=t.id_fila JOIN servicios s ON s.id_servicio=f.id_servicio
                                  WHERE t.numero = %s AND t.id_usuario = %s''',
                               (numero_turno, session['usuario_id']))
                turno = cursor.fetchone()
                if turno and turno['estado'] == 'Pendiente':
                    cursor.execute('''SELECT COUNT(*) AS anteriores FROM turnos
                                      WHERE estado = 'Pendiente' AND id_fila = %s AND id_turno < %s''',
                                   (turno['id_fila'], turno['id_turno']))
                    personas_antes = cursor.fetchone()['anteriores']
                    posicion = personas_antes + 1
                    tiempo_estimado = personas_antes * turno['duracion_estimada']
    return render_template('cliente/consultar_turno.html', numero_turno=numero_turno,
                           turno=turno, posicion=posicion, personas_antes=personas_antes,
                           tiempo_estimado=tiempo_estimado)


@app.route('/cliente/modificar-turno/<numero_turno>', methods=['GET', 'POST'])
@login_required
def modificar_turno(numero_turno):
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT t.id_turno, t.id_fila, t.numero, t.estado, s.nombre AS servicio, s.duracion_estimada
                              FROM turnos t JOIN filas f ON f.id_fila=t.id_fila JOIN servicios s ON s.id_servicio=f.id_servicio
                              WHERE t.numero = %s AND t.id_usuario = %s''',
                           (numero_turno, session['usuario_id']))
            turno = cursor.fetchone()
            if not turno or turno['estado'] != 'Pendiente':
                abort(404)
            if request.method == 'POST':
                try:
                    servicio_id = int(request.form.get('servicio', ''))
                except ValueError:
                    abort(400)
                cursor.execute("""SELECT f.id_fila FROM filas f JOIN servicios s ON s.id_servicio=f.id_servicio
                                  JOIN sucursales u ON u.id_sucursal=s.id_sucursal
                                  WHERE f.id_fila=%s AND f.estado='activa' AND s.estado='activo' AND u.estado='activa'""", (servicio_id,))
                if not cursor.fetchone():
                    abort(400)
                cursor.execute('UPDATE turnos SET id_fila = %s WHERE id_turno = %s',
                               (servicio_id, turno['id_turno']))
                return redirect(url_for('gestion_turnos'))
            cursor.execute("""SELECT f.id_fila AS id, CONCAT(s.nombre, ' — ', u.nombre) AS nombre
                                  FROM filas f JOIN servicios s ON s.id_servicio=f.id_servicio
                                  JOIN sucursales u ON u.id_sucursal=s.id_sucursal
                                  WHERE f.estado='activa' AND s.estado='activo' AND u.estado='activa'
                                  ORDER BY u.nombre,s.nombre,f.id_fila""")
            servicios = cursor.fetchall()
    return render_template('cliente/modificar_turno.html', turno=turno, servicios=servicios)


@app.route('/cliente/eliminar-turno/<numero_turno>', methods=['POST'])
@login_required
def eliminar_turno(numero_turno):
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''UPDATE turnos SET estado = 'Cancelado'
                              WHERE numero = %s AND id_usuario = %s AND estado = 'Pendiente' ''',
                           (numero_turno, session['usuario_id']))
    return redirect(url_for('gestion_turnos'))

@app.route('/cliente/perfil')
@login_required
def perfil_cliente():

    with db() as connection:

        with connection.cursor() as cursor:

            cursor.execute('''
                SELECT id_usuario, nombre, correo, rol, fecha_registro
                FROM usuarios
                WHERE id_usuario = %s
            ''', (session['usuario_id'],))

            usuario = cursor.fetchone()

    if not usuario:
        abort(404)

    return render_template(
        'cliente/perfil_cliente.html',
        usuario=usuario
    )



#-------------------------------------------------------------------- Admin -------------------------------------------------------------------------------
@app.route('/admin/panel')
@funcionario_required
def panel_admin():
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT t.numero, s.nombre AS servicio, t.estado
                              FROM turnos t JOIN filas f ON f.id_fila=t.id_fila JOIN servicios s ON s.id_servicio=f.id_servicio ORDER BY t.id_turno''')
            turnos = cursor.fetchall()
    return render_template('admin/panel_admin.html', turnos=turnos)


@app.route('/admin/llamar-siguiente', methods=['POST'])
@funcionario_required
def llamar_siguiente():
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_funcionario FROM funcionarios WHERE id_usuario=%s AND estado='activo'",
                           (session['usuario_id'],))
            funcionario = cursor.fetchone()
            if not funcionario:
                abort(403, 'Asocia esta cuenta a un funcionario activo antes de atender turnos.')
            cursor.execute("""SELECT t.id_turno FROM turnos t
                              JOIN filas f ON f.id_fila=t.id_fila
                              JOIN servicios s ON s.id_servicio=f.id_servicio
                              WHERE t.estado='Pendiente' AND s.id_sucursal=(
                                  SELECT id_sucursal FROM funcionarios WHERE id_funcionario=%s)
                              ORDER BY t.id_turno LIMIT 1 FOR UPDATE""", (funcionario['id_funcionario'],))
            turno = cursor.fetchone()
            if turno:
                cursor.execute("UPDATE turnos SET estado = 'En atencion' WHERE id_turno = %s", (turno['id_turno'],))
                cursor.execute('INSERT INTO atenciones (id_turno,id_funcionario) VALUES (%s,%s)',
                               (turno['id_turno'], funcionario['id_funcionario']))
                cursor.execute('''INSERT INTO notificaciones (id_usuario,id_turno,mensaje)
                                  SELECT id_usuario,id_turno,CONCAT('Turno ',numero,' llamado a atención.')
                                  FROM turnos WHERE id_turno=%s''', (turno['id_turno'],))
    return redirect(url_for('panel_admin'))


@app.route('/admin/finalizar-atencion/<numero_turno>', methods=['POST'])
@funcionario_required
def finalizar_atencion(numero_turno):
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE turnos t JOIN atenciones a ON a.id_turno=t.id_turno
                              JOIN funcionarios f ON f.id_funcionario=a.id_funcionario
                              SET t.estado='Finalizado', a.hora_fin=CURRENT_TIMESTAMP
                              WHERE t.numero=%s AND t.estado='En atencion' AND f.id_usuario=%s""",
                           (numero_turno, session['usuario_id']))
    return redirect(url_for('panel_admin'))


@app.route('/admin/cancelar-turno/<numero_turno>', methods=['POST'])
@funcionario_required
def cancelar_turno_admin(numero_turno):
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE turnos SET estado = 'Cancelado' WHERE numero = %s AND estado = 'Pendiente'",
                           (numero_turno,))
    return redirect(url_for('panel_admin'))


@app.route('/admin/servicios')
@admin_required
def gestion_servicios():
    with db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT f.id_fila AS id, CONCAT(s.nombre, ' — ', u.nombre) AS nombre
                                  FROM filas f JOIN servicios s ON s.id_servicio=f.id_servicio
                                  JOIN sucursales u ON u.id_sucursal=s.id_sucursal
                                  WHERE f.estado='activa' AND s.estado='activo' AND u.estado='activa'
                                  ORDER BY u.nombre,s.nombre,f.id_fila""")
            servicios = cursor.fetchall()
    return render_template('admin/gestion_servicios.html', servicios=servicios)


@app.route('/admin/agregar-servicio', methods=['POST'])
@admin_required
def agregar_servicio():
    nombre = request.form.get('servicio', '').strip()
    if nombre:
        with db() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_sucursal FROM sucursales WHERE estado='activa' ORDER BY id_sucursal LIMIT 1")
                sucursal = cursor.fetchone()
                if not sucursal:
                    abort(400, 'Primero crea una sucursal activa.')
                cursor.execute('INSERT IGNORE INTO servicios (id_sucursal,nombre) VALUES (%s,%s)',
                               (sucursal['id_sucursal'], nombre))
                cursor.execute('SELECT id_servicio FROM servicios WHERE id_sucursal=%s AND nombre=%s',
                               (sucursal['id_sucursal'], nombre))
                servicio = cursor.fetchone()
                cursor.execute("INSERT IGNORE INTO filas (id_servicio,nombre) VALUES (%s,'Fila principal')",
                               (servicio['id_servicio'],))
    return redirect(url_for('gestion_servicios'))


@app.route('/admin/configuracion-prioridad', methods=['GET', 'POST'])
@admin_required
def configuracion_prioridad():
    with db() as connection:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                prioridad = request.form.get('prioridad')
                if prioridad not in ('llegada', 'alta', 'sin_prioridad'):
                    abort(400)
                cursor.execute("UPDATE configuracion SET valor = %s WHERE clave = 'prioridad'", (prioridad,))
            cursor.execute("SELECT valor FROM configuracion WHERE clave = 'prioridad'")
            row = cursor.fetchone()
    return render_template('admin/configuracion_prioridad.html', prioridad=row['valor'] if row else 'llegada')


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
