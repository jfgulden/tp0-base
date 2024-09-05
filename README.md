# TP0: Docker + Comunicaciones + Concurrencia

## Parte 1: Docker

### Ejercicio 1

Para ejecutar el ejercicio 1, se debe correr el siguiente comando:

```bash
bash generar-compose.sh <docker-compose-dev.yaml> <clients_num>
```

Donde `<docker-compose-dev.yaml>` es el archivo de configuración de docker-compose y `<clients_num>` es la cantidad de clientes que se quieren crear.

### Ejercicio 2

Para cumplir con el ejercicio 2, se modificó el archivo docker compose para lograr que realizar cambios en el archivo de configuración no requiera un nuevo build de las imágenes de Docker para que los mismos sean efectivos. Para esto se agregaron volúmenes a los servicios de cliente y servidor, de la siguiente manera:

```yaml
volumes:
    - ./client/config.yaml:/app/config.yaml

volumes:
    - ./server/config.ini:/app/config.ini
```

Al mapear el archivo de configuración local (config.yaml o config.ini) con un archivo dentro del contenedor, los cambios en el archivo local se reflejan inmediatamente dentro del contenedor sin tener que hacer un nuevo build. Esto evita tener que hacer un nuevo build de las imágenes de Docker cada vez que se quiera cambiar la configuración.

A su vez, se añadió un archivo .dockerignore con el siguiente contenido para evitar que se copien los archivos de configuración al contenedor:

```
client/config.yaml
server/config.ini
```

### Ejercicio 3

Para el ejercicio 3, se creó un script de bash validar-echo-server.sh que permite verificar el correcto funcionamiento del servidor utilizando el comando netcat para interactuar con el mismo.
Para poder ejecutar el script, se debe correr el siguiente comando:

```bash
./validar-echo-sever.sh
```

Tener en cuenta que el servidor debe estar corriendo para poder realizar la validación, por lo que se debe levantar el contenedor del servidor antes de ejecutar el script. Para esto, correr el siguiente comando previamente:

```bash
make docker-compose-up
```

### Ejercicio 4

En el ejercicio 4, se incluyeron dos funciones, una del lado del cliente y otra del lado del servidor, que permiten terminar la conexión entre ambos de forma segura al recibir la señal SIGTERM.

Para el cliente y el servidor se creo la funcion handleSigterm. En el cliente, maneja la señal de terminación y detiene el bucle del cliente. En el servidor, maneja la señal de terminación y cierra el socket del servidor.

handleSigterm en el cliente:

```go
func handleSigterm(client *common.Client) {
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM)
	go func() {
		sig := <-sigs
		client.StopClientLoop()
		os.Exit(0)
	}()
}
```

handleSigterm en el servidor:

```python
    def handle_sigterm(self, signum, frame):
        self._is_running = False
        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()
        time.sleep(1)
```
