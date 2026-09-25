from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "filasmart-clave-temporal"


usuarios = []

turnos = []

contador_turno = 0

#Hasta que tengamos bien la BD lo hare de forma local facil para ver que va incrementando, despues lo asocio a funciones reales


@app.route("/")
def inicio():
    return render_template("index.html", 
                           usuario=session.get("usuario"))

#Dejare el registro de usuarios de forma local hasta que tengamos la BD

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

        return redirect(url_for("inicio_sesion", registrado="1"))

    return render_template("registro.html")



#Vamos a dejar que tiene que iniciar sesion para poder pedir turno, despues agrego las validaciones
@app.route("/inicio-sesion", methods=["GET", "POST"])
def inicio_sesion():

    if session.get("usuario"):
        return redirect(url_for("inicio"))

    if request.method == "POST":

        correo = request.form.get("correo")
        password = request.form.get("password")

        for usuario in usuarios:

            if usuario["correo"] == correo and usuario["password"] == password:

                session["usuario"] = usuario["correo"]

                return redirect(url_for("inicio"))

        return render_template("inicio_sesion.html", 
                               error="Correo o contraseña incorrectos.")

    registrado = request.args.get("registrado")

    return render_template(
        "inicio_sesion.html",
        registrado=registrado
    )

 

@app.route("/obtener-turno")
def obtener_turno():
    return render_template("obtener_turno.html")



@app.route("/turno-generado")
def turno_generado():

    global contador_turno

    contador_turno += 1

    #Aca lo dejare en numeros enteros porque en tiendas siempre he visto que son 3 digitos
    #Aunque si apuntamos a establecimientos pequeños y medianos no se si pasaran los 100 jajaj revisaremos esto despues
    numero_turno = f"A{contador_turno:03d}"

    servicio = request.args.get("servicio")

    turno = {
        "numero": numero_turno,
        "servicio": servicio,
        "estado": "Pendiente"
    }

    turnos.append(turno)

    return render_template("turno_generado.html",
                           numero_turno=numero_turno,
                           servicio=servicio)


@app.route("/gestion-turnos")
def gestion_turnos():
    return render_template("gestion_turnos.html",
                           turnos=turnos)


@app.route("/consultar-turno")
def consultar_turno():

    numero_turno = request.args.get("turno")
    turno_encontrado = None

    if numero_turno:

        for turno in turnos:

            if turno["numero"] == numero_turno:
                turno_encontrado = turno
                break

    return render_template(
        "consultar_turno.html",
        numero_turno=numero_turno,
        turno=turno_encontrado
    )


@app.route("/cerrar-sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("inicio"))

#Se me ocurrio por si la gente se equivoca de servicio que quiere o se aburre de esperar y se va
@app.route("/modificar-turno/<numero_turno>", methods=["GET", "POST"])
def modificar_turno(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            if request.method == "POST":

                nuevo_servicio = request.form.get("servicio")

                turno["servicio"] = nuevo_servicio

                return redirect(url_for("gestion_turnos"))

            return render_template(
                "modificar_turno.html",
                turno=turno
            )

    return redirect(url_for("gestion_turnos"))


@app.route("/eliminar-turno/<numero_turno>")
def eliminar_turno(numero_turno):

    for turno in turnos:

        if turno["numero"] == numero_turno:

            turnos.remove(turno)
            break

    return redirect(url_for("gestion_turnos"))


#Despues haremos las conexiones para dejar el index como inicio de sesion pero por ahora dejaremos asi hasta tener bien la BD

if __name__ == "__main__":
    app.run(debug=True)

