import socket
import logging
import time
from multiprocessing import Lock, Process
from common.client_connection_handler import ClientConnectionHandler


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._is_running = True
        self.client_sock = None
        self.processes = []

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        bests_file_lock = Lock()

        while self._is_running:
            try:
                self.client_sock, addr = self.__accept_new_connection()
                if self.client_sock is None or not self._is_running:
                    break
                
                process = Process(target=ClientConnectionHandler.New, args=(self.client_sock, addr, bests_file_lock))
                process.start()
                self.processes.append(process)

            except OSError as e:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
                if self.client_sock is not None:
                    self.client_sock.close()
                self._server_socket.close()     

        logging.info("JOINEO TODOS LOS PROCESOS")
        for process in self.processes:
            process.join()     


    def handle_sigterm(self, signum, frame):
        """
        Handle SIGTERM signal

        Function that handles the SIGTERM signal. It closes the server
        socket.
        """

        logging.info("action: socket_close | result: in_progress")
        self._is_running = False
        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()

        for process in self.processes:
            process.terminate()
            process.join()

        logging.info("action: socket_close | result: success")
        time.sleep(1)





    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c, addr
        except OSError as e:
            if not self._is_running:
                logging.info('action: accept_connections | result: success | ip: None')
            else:
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return None, None
        
        
