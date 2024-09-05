package common

import (
	"net"
	"time"
	"github.com/op/go-logging"
	"bytes"
	"encoding/csv"
	"fmt"
	"encoding/binary"
	"os"
)
const (
	SERVER_ACK string = "ACK"
	BATCH_MAX_AMOUNT_BYTES int = 8 * 1024
	DNI_LEN int = 1 // 1 byte
	EOF_MSG_TRUE uint8 = 1
	EOF_MSG_FALSE uint8 = 0
	WINNERS_NUM_BYTES int = 1
)
var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchMaxAmount int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	conn_closed bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	c.conn_closed = false
	return nil
}

func (c *Client) sendAll(data []byte) error {
	totalSent := 0
	for totalSent < len(data) {
		n, err := c.conn.Write(data[totalSent:])
		if err != nil {
			return err
		}
		totalSent += n
	}
	return nil
}

func (c *Client) sendMsg(buffer []byte, ) error {

	err := c.sendAll(buffer)
	if err != nil {
		log.Criticalf("action: send_bet | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	log.Infof("action: send_batch | result: success | client_id: %v | batch_size_bytes: %v",
		c.config.ID,
		len(buffer),
	)
	return nil
}

func (c *Client) readAll(length int) ([]byte, error) {
	buffer := make([]byte, length)
	totalRead := 0
	for totalRead < length {
		
		n, err := c.conn.Read(buffer[totalRead:])
		if err != nil {
			return nil, err
		}
		totalRead += n
		if n == 0 {
			break
		}
	}
	return buffer, nil
}
func (c *Client) readMsg(length int) (string, error) {
	buffer, err := c.readAll(length)
	if err != nil {
		log.Criticalf("action: receive_msg | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return "", err
	}
	msg := string(buffer)
	log.Infof("action: receive_msg | result: success | client_id: %v | msg: %v",
		c.config.ID,
		msg,
	)
	return msg, nil
}

func (c *Client) serialize_batch(bets []Bet, eof_flag uint8) ([]byte, error) {
	var buffer bytes.Buffer
	for _, bet := range bets {
		betBuffer, err := bet.serialize()
		if err != nil {
			log.Criticalf("action: serialize | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return nil, err
		}
		if _, err := buffer.Write(betBuffer); err != nil {
			return nil, err
		}
	}
	totalLength := uint8(len(bets))
	var finalBuffer bytes.Buffer
	binary.Write(&finalBuffer, binary.BigEndian, eof_flag)

	if err := binary.Write(&finalBuffer, binary.BigEndian, totalLength); err != nil {
        return nil, err
    }

	finalBuffer.Write(buffer.Bytes())
	return finalBuffer.Bytes(), nil
}

func (c *Client) prepareBatchForSending(bets []Bet) ([]Bet, []byte, error) {

	batch := chunkBets(bets, c.config.BatchMaxAmount)

	buffer, err := c.serialize_batch(batch, func() uint8 {
		if len(batch) == len(bets) {
			return EOF_MSG_TRUE
		}
		return EOF_MSG_FALSE
	}())
		

	if err != nil {
		return batch, nil, err
	}

	for len(buffer) > BATCH_MAX_AMOUNT_BYTES {
		batchSize := len(batch) * 3 / 4
		if batchSize < 1 {
			return nil, nil, fmt.Errorf("batch size too small to continue")
		}
		batch = chunkBets(bets, batchSize)
		if len(batch) == len(bets) {
			buffer, err = c.serialize_batch(batch, EOF_MSG_TRUE)
		} else {	
			buffer, err = c.serialize_batch(batch, EOF_MSG_FALSE)
		}
		if err != nil {
			return batch, nil, err
		}
	}
	return batch, buffer, nil
}


func chunkBets(bets []Bet, maxAmount int) []Bet {
	batches := make([]Bet, 0, maxAmount)

	if len(bets) <= maxAmount {

		return bets
	}
	for i := 0; i < maxAmount; i++ {
		batches = append(batches, bets[i])
	}
	return batches
}
func (c *Client) receiveWinners() ([]string, error) {
	var winners []string
	
	msg, err := c.readAll(WINNERS_NUM_BYTES)
	if err != nil {
		log.Errorf("action: receive_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return nil, err
	}
	winners_num := int(msg[0])
	
	for i := 0; i < winners_num; i++ {
		dni_msg, err := c.readMsg(DNI_LEN)
		if err != nil {
			log.Errorf("action: receive_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return nil, err
		}
		winners = append(winners, dni_msg)
	}
	if err != nil {
		log.Errorf("action: receive_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return nil, err
	}
	log.Infof("action: receive_winners | result: success | client_id: %v | winners_num: %d", c.config.ID, len(winners))

	return winners, nil
}
// StartClient sends message to the server and wait for the response
func (c *Client) StartClient() {
	file, err_opening_file := os.Open(fmt.Sprintf("/dataset/agency-%s.csv", c.config.ID))
	if err_opening_file != nil {
		log.Errorf("action: open_csv | result: fail | client_id: %v | error: %v", c.config.ID, err_opening_file)
		return
	}
	defer file.Close()
	csvReader := csv.NewReader(file)
	records, err := csvReader.ReadAll()
	if err != nil {
		log.Errorf("action: read_csv | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	bets := make([]Bet, 0, len(records))

	for _, record := range records {
		bet := NewBet(c.config.ID, record[0], record[1], record[2], record[3], record[4])
		bets = append(bets, *bet)
	}
	c.createClientSocket()

	for len(bets) > 0 {
		batchToSend, bytesToSend, err := c.prepareBatchForSending(bets)
		if err != nil || bytesToSend == nil {
			log.Errorf("action: serialize_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}
		err = c.sendMsg(bytesToSend)
		if err != nil {
			c.StopClient()
			return
		}

		msg, err := c.readMsg(len(SERVER_ACK + "\n"))
		if err != nil || msg != SERVER_ACK+"\n" {
			c.StopClient()
			return
		}
		bets = bets[len(batchToSend):]
		time.Sleep(c.config.LoopPeriod)
	}

	winners, err := c.receiveWinners()
	if err != nil {
		c.StopClient()
		return
	}
	msg, err := c.readMsg(len(SERVER_ACK + "\n"))
	if err != nil || msg != SERVER_ACK+"\n" {
		c.StopClient()
		return
	}
	log.Infof("action: receive_final_ack | result: success | client_id: %v | winners: %v", c.config.ID, winners)

	c.conn.Close()
	c.conn_closed = true
}

func (c *Client) StopClient() {
	if c.conn_closed {
		log.Infof("action: close_connection | result: success | client_id: %v", c.config.ID)
		return
	}
	err := c.conn.Close()
	if err != nil {
		log.Errorf("action: close_connection | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	log.Infof("action: close_connection | result: success | client_id: %v", c.config.ID)
}