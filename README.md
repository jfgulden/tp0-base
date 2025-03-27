# TP0: Docker + Comunicaciones + Concurrencia

## Parte 1: Docker

### Ejercicio 1

Para generar el archivo de docker-compose con una cantidad determinada de clientes, se debe correr el siguiente comando:

```bash
bash generar-compose.sh <docker-compose-dev.yaml> <clients_num>
```

Este archivo utiliza un script de Python para generar el archivo de docker-compose (`generador.py`). El script toma como parámetros el nombre del archivo de salida y la cantidad de clientes a crear, y genera los clientes en el archivo especificado.
