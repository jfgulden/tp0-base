import socket
import logging
import signal
import time
from server.common.utils import Bet
from server.common.utils import store_bets

MSG_SIZE = 1 # 1 byte is designed to store a number from 0 to 255, which is enough to know how many bets are going to be sent
SERVER_ANSWER = 'ACK'

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._is_running = True
        self.client_sock = None

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                self.client_sock = self.__accept_new_connection()
                if self.client_sock is None or not self._is_running:
                    break

                self.__handle_client_connection()
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
            finally:
                if self.client_sock is not None:
                    self.client_sock.shutdown(socket.SHUT_RDWR)
                    self.client_sock.close()                


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
        logging.info("action: socket_close | result: success")
        time.sleep(1)

    def __read_all(self, n) -> bytes:
        """
        Reads n bytes from the client socket, avoiding short reads.
        """
        buffer = b''
        while len(buffer) < n:
            try:
                packet = self.client_sock.recv(n - len(buffer))
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                return None
            if not packet:
                return None
            buffer += packet
        return buffer
    
    def __send_all(self, data):
        """
        Sends all the data through the socket, avoiding short writes.
        """
        total_sent = 0
        while total_sent < len(data):
            sent = self.client_sock.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent


    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg_header = self.__read_all(MSG_SIZE)         
            if not msg_header:
                return
            msg_len = int.from_bytes(msg_header, byteorder='big')
            
            logging.info(f'action: receive_message | result: in_progress | msg_length: {msg_len} ')
            bets = []
            for i in range(msg_len):
                encoded_msg = self.__read_all(msg_len)
                if not encoded_msg:
                    return
                bet = Bet.parse(encoded_msg)
                bets.append(bet)
            
            addr = self.client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {encoded_msg}')

            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: ${bet.document} | numero: ${bet.number}')

            self.__send_all((SERVER_ANSWER + '\n').encode('utf-8'))
            logging.info(f'action: send_message | result: success | ip: {addr[0]} | msg: {SERVER_ANSWER}')
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            self.client_sock.close()

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
            return c
        except OSError as e:
            if not self._is_running:
                logging.info('action: accept_connections | result: success | ip: None')
            else:
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return None
        
        
