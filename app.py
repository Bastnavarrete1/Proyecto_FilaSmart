from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "filasmart-clave-temporal"


usuarios = []

turnos = []

servicios = ["Atencion general", "Servicio tecnico", "Consulta"]

contador_turno = 0

# Hasta que tengamos bien la BD lo hare de forma local
# facil para ver que va incrementando, despues lo asocio
# a funciones reales


@app.route("/")
def inicio():
    return render_template(
        "cliente/index.html",
        usuario=session.get("usuario")
    )


# Dejare el registro de usuarios de forma local hasta que tengamos la BD

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")

        usuario = {
            "nombre": nombre,
            "correo": correo,
            "password": password
        }

        usuarios.append(usuario)

        return redirect(
            url_for("inicio_sesion", registrado="1")
        )

    return render_template("cliente/registro.html")


# Vamos a dejar que tiene que iniciar sesion para poder pedir turno,
# despues agrego las validaciones

@app.route("/inicio-sesion", methods=["GET", "POST"])
def inicio_sesion():

    if session.get("usuario"):
        return redirect(url_for("inicio"))

    if request.method == "POST":

        correo = request.form.get("correo")
        password = request.form.get("password")

        for usuario in usuarios:

            if (
                usuario["correo"] == correo
                and usuario["password"] == password
            ):

                session["usuario"] = usuario["correo"]

                return redirect(url_for("inicio"))

        return render_template(
            "cliente/inicio_sesion.html",
            error="Correo o contraseña incorrectos."
        )

    registrado = request.args.get("registrado")

    return render_template(
        "cliente/inicio_sesion.html",
        registrado=registrado
    )


# ---------------------------------------------------------
# CLIENTE
# ---------------------------------------------------------

@app.route("/cliente/obtener-turno")
def obtener_turno():
    return render_template("cliente/obtener_turno.html", servicios=servicios)


@app.route("/cliente/turno-generado")
def turno_generado():

    global contador_turno

    contador_turno += 1

    # Aca lo dejare en numeros enteros porque en tiendas siempre
    # he visto que son 3 digitos
    # Aunque si apuntamos a establecimientos pequeños y medianos
    # no se si pasaran los 100 jajaj revisaremos esto despues

    numero_turno = f"A{contador_turno:03d}"

    servicio = request.args.get("servicio")

    turno = {
        "numero": numero_turno,
        "servicio": servicio,
        "estado": "Pendiente"
    }

    turnos.append(turno)

    return render_template(
        "cliente/turno_generado.html",
        numero_turno=numero_turno,
        servicio=servicio
    )


@app.route("/cliente/gestion-turnos")
def gestion_turnos():
    return render_template(
        "cliente/gestion_turnos.html",
        turnos=turnos
    )


@app.route("/cliente/consultar-turno")
def consultar_turno():

    numero_turno = request.args.get("turno")

    turno_encontrado = None
    posicion = None
    personas_antes = None
    tiempo_estimado = None

    if numero_turno:

        for i, turno in enumerate(turnos):

            if turno["numero"] == numero_turno:

                turno_encontrado = turno

                # La posicion empieza desde el 1°
                posicion = i + 1

                # Cantidad de turnos que estan antes de la persona
                personas_antes = i

                # Tiempo aproximado: 10 minutos por persona
                tiempo_estimado = personas_antes * 10

                break

    return render_template(
        "cliente/consultar_turno.html",
        numero_turno=numero_turno,
        turno=turno_encontrado,
        posicion=posicion,
        personas_antes=personas_antes,
        tiempo_estimado=tiempo_estimado
    )


@app.route("/cliente/cerrar-sesion")
def cerrar_sesion():
    session.clear()

    return redirect(url_for("inicio"))


# Se me ocurrio por si la gente se equivoca de servicio que quiere
# o se aburre de esperar y se va

@app.route(
    "/cliente/modificar-turno/<numero_turno>",
    methods=["GET", "POST"]
)
def modificar_turno(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            if request.method == "POST":

                nuevo_servicio = request.form.get("servicio")

                turno["servicio"] = nuevo_servicio

                return redirect(url_for("gestion_turnos"))

            return render_template(
                "cliente/modificar_turno.html",
                turno=turno
            )

    return redirect(url_for("gestion_turnos"))


@app.route("/cliente/eliminar-turno/<numero_turno>")
def eliminar_turno(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            turnos.remove(turno)

            break

    return redirect(url_for("gestion_turnos"))


# Despues haremos las conexiones para dejar el index
# como inicio de sesion pero por ahora dejaremos asi
# hasta tener bien la BD


# ---------------------------------------------------------
# ADMIN
# ---------------------------------------------------------

@app.route("/admin/panel")
def panel_admin():
    return render_template(
        "admin/panel_admin.html",
        turnos=turnos
    )


@app.route("/admin/llamar-siguiente")
def llamar_siguiente():

    for turno in turnos:

        if turno["estado"] == "Pendiente":

            turno["estado"] = "En atencion"

            break

    return redirect(url_for("panel_admin"))


@app.route("/admin/finalizar-atencion/<numero_turno>")
def finalizar_atencion(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            if turno["estado"] == "En atencion":

                turno["estado"] = "Finalizado"

            break

    return redirect(url_for("panel_admin"))


@app.route("/admin/cancelar-turno/<numero_turno>")
def cancelar_turno_admin(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            if turno["estado"] == "Pendiente":
                turno["estado"] = "Cancelado"

            break

    return redirect(url_for("panel_admin"))


@app.route("/admin/servicios")
def gestion_servicios():

    return render_template(
        "admin/gestion_servicios.html",
        servicios=servicios
    )


@app.route("/admin/agregar-servicio", methods=["POST"])
def agregar_servicio():

    nuevo_servicio = request.form.get("servicio")

    if nuevo_servicio and nuevo_servicio not in servicios:
        servicios.append(nuevo_servicio)

    return redirect(url_for("gestion_servicios"))



#Prioridades a idea del profe
#O la podemos cambiar para que sea lo de la venta de puestos de fila ;)

prioridad_actual = "llegada"


@app.route("/admin/configuracion-prioridad", methods=["GET", "POST"])
def configuracion_prioridad():

    global prioridad_actual

    if request.method == "POST":

        prioridad_actual = request.form.get("prioridad")

    return render_template(
        "admin/configuracion_prioridad.html",
        prioridad=prioridad_actual
    )



if __name__ == "__main__":
    app.run(debug=True)