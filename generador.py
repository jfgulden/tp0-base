from sys import argv

file = argv[1]
clients = int(argv[2])

for i in range(1, clients+1):
    with open(file, 'a') as f:
        client = f"""
    client{i}:
        container_name: client{i}
        image: client:latest
        entrypoint: /client
        environment:
        - CLI_ID={i}
        - CLI_LOG_LEVEL=DEBUG
        networks:
        - testing_net
        depends_on:
        - server
"""
        f.write(client)

    
f.close()