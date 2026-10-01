# FilaSmart: base de datos y conexión según el MER

## Qué contiene

`schema.sql` implementa las ocho entidades del MER: `usuarios`, `sucursales`, `servicios`, `filas`, `turnos`, `funcionarios`, `atenciones` y `notificaciones`. Las claves primarias y foráneas conservan los nombres del diagrama. `configuracion` es una tabla auxiliar para conservar la pantalla de prioridades del prototipo.

Relaciones: una sucursal tiene varios servicios; cada servicio tiene varias filas; una fila recibe varios turnos; un usuario solicita varios turnos; un turno puede tener una atención y varias notificaciones; un funcionario realiza varias atenciones y pertenece a una sucursal. Una notificación también apunta al usuario destinatario. La relación 1:1 turno-atención se implementa con `UNIQUE(id_turno)` y permite que un turno pendiente aún no tenga atención.

La columna `contraseña` almacena un hash de Werkzeug. Nunca ingreses contraseñas en texto plano mediante SQL. `duracion_estimada` se expresa en minutos. El código crea una notificación como registro interno, pero todavía no envía correo, SMS ni avisos en tiempo real.

## Paso 1: crear las tablas

Requiere MySQL 8. En MySQL Workbench, abre `schema.sql` y ejecuta el archivo completo. También puedes usar una terminal:

```bash
mysql -u root -p < schema.sql
```

El script crea `filasmart`, una sucursal de ejemplo, tres servicios y una fila para cada servicio. Puedes revisar los datos con:

```sql
USE filasmart;
SHOW TABLES;
SELECT s.nombre AS servicio, f.nombre AS fila FROM servicios s
JOIN filas f ON f.id_servicio=s.id_servicio;
```

El script de creación es para una base nueva. Si ya importaste la versión anterior de FilaSmart, crea otra base o planifica una migración de datos antes de ejecutarlo; `CREATE TABLE IF NOT EXISTS` no transforma tablas antiguas.

## Paso 2: crear el usuario de conexión

Ejecuta estas instrucciones como administrador de MySQL y reemplaza la contraseña de ejemplo:

```sql
CREATE USER 'filasmart_app'@'localhost' IDENTIFIED BY 'TU_CONTRASENA_SEGURA';
GRANT SELECT, INSERT, UPDATE, DELETE ON filasmart.* TO 'filasmart_app'@'localhost';
```

## Paso 3: preparar Python

Desde la carpeta extraída, crea y activa un entorno virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En macOS/Linux activa con `source .venv/bin/activate`. Para configurar la conexión en **PowerShell**, reemplaza las claves de ejemplo:

```powershell
$env:DB_HOST='localhost'
$env:DB_PORT='3306'
$env:DB_NAME='filasmart'
$env:DB_USER='filasmart_app'
$env:DB_PASSWORD='TU_CONTRASENA_SEGURA'
$env:FLASK_SECRET_KEY='UNA_CLAVE_ALEATORIA_LARGA'
python app.py
```

Abre `http://127.0.0.1:5000`. `.env.example` documenta las variables, pero `app.py` no lee automáticamente un archivo `.env`: debes definir las variables en la terminal como arriba. Nunca subas contraseñas al repositorio.

## Paso 4: preparar una cuenta para atender

Regístrate normalmente en la web, luego sustituye el correo y asigna el rol y la sucursal desde MySQL:

```sql
USE filasmart;
UPDATE usuarios SET rol='admin' WHERE correo='tu_correo@ejemplo.com';
INSERT INTO funcionarios (id_usuario,id_sucursal,cargo)
SELECT u.id_usuario,s.id_sucursal,'Encargado de atención'
FROM usuarios u JOIN sucursales s ON s.nombre='Sucursal principal'
WHERE u.correo='tu_correo@ejemplo.com';
```

Cierra sesión y vuelve a iniciarla para actualizar el rol de la sesión. La cuenta podrá abrir `/admin/panel`, llamar turnos de su sucursal y finalizarlos. El alta pública siempre crea cuentas de cliente.

## Alcance de la interfaz actual

El prototipo permite pedir turno por servicio y sucursal, consultar la posición dentro de **su fila**, cancelar o cambiar la fila, llamar turnos y registrar el inicio y fin de la atención. El tiempo estimado es el número de turnos pendientes anteriores de esa fila multiplicado por la duración del servicio: es una aproximación, no una medición real. El panel de administrador muestra todas las filas y la acción «Llamar siguiente» toma el primer pendiente de la sucursal del funcionario; una interfaz para escoger una fila concreta queda pendiente.

Agregar un servicio desde el panel lo asigna a la primera sucursal activa y crea su «Fila principal». Para gestionar varias sucursales y filas con libertad, harán falta pantallas adicionales. La opción de prioridades se almacena en `configuracion`, pero aún no cambia el orden. Antes de publicar el sistema, agrega protección CSRF a los formularios y configura HTTPS.
