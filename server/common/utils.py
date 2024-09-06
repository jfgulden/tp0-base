import csv
import datetime
import logging

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 4540
BET_SEPARATOR = ','
BATCH_MSG_SIZE = 1 # 1 byte is designed to store a number from 0 to 255, which is enough to know how many bets are going to be sent
MSG_SIZE = 4 
SERVER_ANSWER = 'ACK'
EOF_MSG = 1
EOF_MSG_SIZE = 1
WINNERS_NUM_BYTES = 1
AGENCY_NUM_BYTES = 1


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

    @staticmethod
    def parse(msg: bytes) -> 'Bet':
        """
        Parses a message into a Bet object.
        """
        if not msg:
            return None
        
        msg = msg.decode('utf-8').split(BET_SEPARATOR)
        bet_agency, name, last_name, document, birthdate, number = msg[0], msg[1], msg[2], msg[3], msg[4], msg[5]

        return Bet(bet_agency, name, last_name, document, birthdate, number)
    
    

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Searches for the winning bets in the STORAGE_FILEPATH file.
"""
def search_lottery_winners(agency: int) -> list[Bet]:
    winner_bets = []
    for bet in load_bets():
        if has_won(bet) and int(bet.agency) == agency:
            winner_bets.append(bet)
    return winner_bets

def serialize_winners(winners: list[Bet]) -> bytes:
    """
    Serializes a list of winners into a byte array.
    """
    serialized = []
    for winner in winners:
        serialized.append(winner.document)

    return ','.join(serialized).encode('utf-8')


"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])

