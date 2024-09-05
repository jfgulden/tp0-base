#!/bin/bash
# Script para validar el funcionamiento del echo-server

# Mi propuesta: Instalar netcat en un container que se conecta a la network donde está el echo-server
SERVER_PORT=12345
MESSAGE="Hola mundo"

RESPONSE=$(docker run --rm --network tp0_testing_net alpine sh -c "echo \"$MESSAGE\" | nc server $SERVER_PORT")

if [ "$RESPONSE" == "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi