// Aca dejamos el script para la generacion de alertas segun el turno del usuario, revisar que todo funcione bien

document.addEventListener('DOMContentLoaded', function () {

    function revisarEstadoTurno() {

        fetch('/cliente/estado-turno')
            .then(response => response.json())
            .then(data => {
                if (!data.tiene_turno) {
                    return;
                }
                if (data.alerta === 'proximo') {
                    mostrarNotificacion(
                        'Atento! Tu turno esta proximo a ser atendido',
                        data.mensaje
                    );
                }

                if (data.alerta === 'turno') {
                    mostrarNotificacion(
                        'Es tu turno, por favor dirijase al mostrador designado',
                        data.mensaje
                    );
                }
            })
            .catch(error => {
                console.error('Error al consultar el estado del turno:', error);
            });
    }

    function mostrarNotificacion(titulo, mensaje) {
        if (Notification.permission === 'granted') {
            new Notification(titulo, {
                body: mensaje,
                icon: '/static/img/logo-alerta.png'
            });
        
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission()
                .then(permission => {
                    if (permission === 'granted') {
                        new Notification(titulo, {
                            body: mensaje,
                            icon: '/static/img/logo-alerta.png'
                        });
                    }
                });
        }
    }


    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }


    revisarEstadoTurno();

    setInterval(revisarEstadoTurno, 10000);
});