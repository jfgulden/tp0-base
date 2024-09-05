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
