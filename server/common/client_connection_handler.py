
import logging
from common.utils import Bet, store_bets
from common.utils import search_lottery_winners
from common.utils import serialize_winners
from common.utils import EOF_MSG
from common.utils import EOF_MSG_SIZE
from common.utils import SERVER_ANSWER
from common.utils import MSG_SIZE
from common.utils import BATCH_MSG_SIZE
from common.utils import AGENCY_NUM_BYTES
from common.utils import Bet
from multiprocessing import Lock, Process



class ClientConnectionHandler:
    def __init__(self, client_sock, client_address, bets_file_lock):
        self.client_sock = client_sock
        self.client_address = client_address
        self.bets_file_lock = bets_file_lock    


    def handle_client_connection(self):
        try:
            addr = self.client_sock.getpeername()
            while self.client_sock:
                msg_header = self.__read_all(EOF_MSG_SIZE)
                if not msg_header:
                    return
                eof_flag = int.from_bytes(msg_header, byteorder='big')
                logging.info(f'action: receive_message | result: in_progress | flag: {eof_flag}')

                bets = self.handle_bets_comm()

                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                self.bets_file_lock.acquire()
                store_bets(bets)
                self.bets_file_lock.release()

                logging.info(f'action: apuesta_almacenada | result: success | cantidad: {len(bets)}')

                self.__send_all((SERVER_ANSWER + '\n').encode('utf-8'))
                logging.info(f'action: send_ack | result: success | ip: {addr[0]} | msg: {SERVER_ANSWER}')

                if eof_flag == EOF_MSG:
                    self.handle_agency_winners()

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            self.client_sock.close()

    def handle_bets_comm(self):
        msg_header = self.__read_all(BATCH_MSG_SIZE)
        bets_num = int.from_bytes(msg_header, byteorder='big')

        logging.info(f'action: receive_message | result: in_progress | msg_length: {bets_num} ')
        bets = self.__receive_bets(bets_num)
        if not bets:
            return None
        return bets

    def handle_agency_winners(self):
        self.__read_all(AGENCY_NUM_BYTES)
        current_agency = int.from_bytes(self.__read_all(AGENCY_NUM_BYTES), byteorder='big')
        self.send_winners(current_agency)

    def __receive_bets(self, bets_num):
        bets = []
        for i in range(bets_num):
            msg_header_bet = self.__read_all(MSG_SIZE)
            if not msg_header_bet:
                logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                return None
            msg_len_bet = int.from_bytes(msg_header_bet, byteorder='big')
            encoded_msg = self.__read_all(msg_len_bet)
            if not encoded_msg:
                return None
            bet = Bet.parse(encoded_msg)

            bets.append(bet)
        return bets
        
    
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
                break
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
                logging.error("action: send_message | result: fail | error: Socket connection broken")
                raise RuntimeError("Socket connection broken")
            total_sent += sent

    def send_winners(self, agency):
        """
        Sends the winners to the client.
        """
        self.bets_file_lock.acquire()
        winners = search_lottery_winners(agency)
        self.bets_file_lock.release()

        encoded_winners = serialize_winners(winners)
        winners_buff = bytes([len(encoded_winners)]) + encoded_winners
        #I assume that len(winners) is less than 256
        self.__send_all(winners_buff)
        logging.info(f'action: enviar_ganadores | result: success | cantidad: {len(winners)}')
        self.__send_all((SERVER_ANSWER + '\n').encode('utf-8'))
        logging.info(f'action: send_ack | result: success | ip: {self.client_sock.getpeername()[0]} | msg: {SERVER_ANSWER}')

    

    @staticmethod
    def New(client_socket, client_address, bets_file_lock):
        return ClientConnectionHandler(client_socket, client_address, bets_file_lock).handle_client_connection()