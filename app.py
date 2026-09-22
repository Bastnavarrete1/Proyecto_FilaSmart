from flask import Flask, render_template, request

app = Flask(__name__)

contador_turno = 0

#Hasta que tengamos bien la BD lo hare de forma local facil para ver que va incrementando, despues lo asocio a funciones reales

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/obtener-turno")
def obtener_turno():
    return render_template("obtener_turno.html")


@app.route("/turno-generado")
def turno_generado():

    global contador_turno
    contador_turno += 1
    numero_turno = f"A{contador_turno:03d}"

    #Aca lo dejare en numeros enteros porque en tiendas siempre he visto que son 3 digitos
    #Aunque si apuntamos a establecimientos pequeños y medianos no se si pasaran los 100 jajaj revisaremos esto despues

    return render_template(
        "turno_generado.html",
        numero_turno=numero_turno
    )


@app.route("/gestion-turnos")
def gestion_turnos():
    return render_template("gestion_turnos.html")


@app.route("/consultar-turno")
def consultar_turno():
    numero_turno = request.args.get("turno")

    return render_template(
        "consultar_turno.html",
        numero_turno=numero_turno
    )

#Despues haremos las conexiones para dejar el index como inicio de sesion pero por ahora dejaremos asi hasta tener bien la BD

@app.route("/inicio-sesion")
def inicio_sesion():
    return render_template("inicio_sesion.html")


if __name__ == "__main__":
    app.run(debug=True)

