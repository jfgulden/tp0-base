import socket
import logging
import signal
import time
from common.utils import Bet
from common.utils import store_bets
from common.utils import search_winner_bets
from common.utils import serialize_winners

BATCH_MSG_SIZE = 1 # 1 byte is designed to store a number from 0 to 255, which is enough to know how many bets are going to be sent
MSG_SIZE = 4 
SERVER_ANSWER = 'ACK'
EOF_MSG = 1
EOF_MSG_SIZE = 1
WINNERS_NUM_BYTES = 1
CLIENTS_NUM = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._is_running = True
        self.client_sock_running = None
        self.clients_socks = {}

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                self.client_sock_running = self.__accept_new_connection()
                if self.client_sock_running is None or not self._is_running:
                    break

                self.__handle_client_connection()

            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                if self.client_sock_running is not None:
                    self.client_sock_running.close()
                self._server_socket.close()        


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
                packet = self.client_sock_running.recv(n - len(buffer))
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                return None
            if not packet:
                break
            buffer += packet
        return buffer
    
    def __send_all(self, data):
        """
        Sends all the data through the socket, avoiding short writes.
        """
        total_sent = 0
        while total_sent < len(data):
            sent = self.client_sock_running.send(data[total_sent:])
            if sent == 0:
                logging.error("action: send_message | result: fail | error: Socket connection broken")
                raise RuntimeError("Socket connection broken")
            total_sent += sent


    def __handle_winners_sending(self):
        """
        Sends the winners to the client.
        """
        logging.info(f'action: receive_message | result: success | msg: {EOF_MSG}')
        winners = search_winner_bets()
        winners_per_agency = {}
        for winner in winners:
            if winner.agency not in winners_per_agency:
                winners_per_agency[winner.agency] = []
            winners_per_agency[winner.agency].append(winner)

        for client_sock, agency in self.clients_socks.items():
            self.client_sock_running = client_sock
            self.__send_winners_to_agency(winners_per_agency[agency])

    def __send_winners_to_agency(self, winners):
        
        encoded_winners = serialize_winners(winners)
        winners_buff = bytes([len(encoded_winners)]) + encoded_winners
            #I assume that len(winners) is less than 256
        self.__send_all(winners_buff)
        logging.info(f'action: enviar_ganadores | result: success | cantidad: {len(winners)}')
        self.__send_all((SERVER_ANSWER + '\n').encode('utf-8'))
        logging.info(f'action: send_ack | result: success | ip: {self.client_sock_running.getpeername()[0]} | msg: {SERVER_ANSWER}')

        
    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        current_agency = None
        addr = self.client_sock_running.getpeername()
        try:
            while self.client_sock_running:
                msg_header = self.__read_all(EOF_MSG_SIZE)
                if not msg_header:
                    return
                eof_flag = int.from_bytes(msg_header, byteorder='big')
                logging.info(f'action: receive_message | result: in_progress | flag: {eof_flag}')
                

                msg_header = self.__read_all(BATCH_MSG_SIZE)
                bets_num = int.from_bytes(msg_header, byteorder='big')

                
                logging.info(f'action: receive_message | result: in_progress | msg_length: {bets_num} ')
                bets = []
                for i in range(bets_num):
                    msg_header_bet = self.__read_all(MSG_SIZE)         
                    if not msg_header_bet:
                        logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                        return
                    msg_len_bet = int.from_bytes(msg_header_bet, byteorder='big')
                    encoded_msg = self.__read_all(msg_len_bet)
                    if not encoded_msg:
                        return
                    bet = Bet.parse(encoded_msg)
                    if not current_agency:
                        current_agency = bet.agency
                    bets.append(bet)
                
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                store_bets(bets)
                logging.info(f'action: apuesta_almacenada | result: success | cantidad: {len(bets)}')

                self.__send_all((SERVER_ANSWER + '\n').encode('utf-8'))
                logging.info(f'action: send_ack | result: success | ip: {addr[0]} | msg: {SERVER_ANSWER}')

                if eof_flag == EOF_MSG:
                    self.clients_socks[self.client_sock_running] = current_agency
                    if len(self.clients_socks) == CLIENTS_NUM:
                        self.__handle_winners_sending()

                    return
                
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")

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
        
        
