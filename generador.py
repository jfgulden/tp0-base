from sys import argv


def generate_clients(output_file, clients_num):
    try:
        with open(output_file, 'a') as f:
            for i in range(1, clients_num+1):
                client_container = f"""
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
                
                f.write(client_container)

    except Exception as e:
        print(f"Error while trying to write file '{output_file}': {e}")
        return 1
    

def main():
    if len(argv) != 3:
        print("Usage: python3 generador.py <file> <clients>")
        return 1
    
    try:
        clients_num = int(argv[2])
        if clients_num < 1:
            raise ValueError("Number of clients must be a positive integer")
        
    except ValueError as ve:
        print(f"Error: {ve}")
        return 1

    
    output_file = argv[1]
    generate_clients(output_file, clients_num)


if __name__ == '__main__':
    main()