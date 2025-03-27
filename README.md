# TP0: Docker + Comunicaciones + Concurrencia

## Parte 1: Docker

### Ejercicio 1

Para generar el archivo de docker-compose con una cantidad determinada de clientes, se debe correr el siguiente comando:

```bash
bash generar-compose.sh <docker-compose-dev.yaml> <clients_num>
```

### Ejercicio 2

Para evitar tener que hacer un nuevo build de las imágenes de Docker cada vez que se quiera cambiar la configuración del cliente o del servidor, se modificó el archivo docker-compose, así como también el script `generar-compose.sh`. Para esto se agregaron bind mounts a los servicios de cliente y servidor.

Al mapear el archivo de configuración local (config.yaml o config.ini) con un archivo dentro del contenedor, los cambios en el archivo local se reflejan inmediatamente dentro del contenedor sin tener que hacer un nuevo build.

A su vez, se añadió un archivo `.dockerignore` con el siguiente contenido para evitar que se copien los archivos de configuración al contenedor:

```
client/config.yaml
server/config.ini
```

### Ejercicio 3

Para verificar el correcto funcionamiento del servidor, se creó un script de bash `validar-echo-server.sh` que utiliza el comando netcat para interactuar con el mismo.
Para poder ejecutar el script, se debe correr el siguiente comando:

```bash
./validar-echo-server.sh
```

Es importante tener en cuenta que el servidor debe estar corriendo para poder realizar la validación, por lo que se debe levantar el contenedor del servidor antes de ejecutar el script. Para esto, correr el siguiente comando previamente:

```bash
make docker-compose-up
```
