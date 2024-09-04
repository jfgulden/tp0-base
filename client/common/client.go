package common

import (
	"net"
	"time"
	"github.com/op/go-logging"
)
const (
	SERVER_ACK = "ACK"
)
var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
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

func (c *Client) sendMsg(bet *Bet) error {
	buffer, err := bet.serialize()
	if err != nil {
		log.Criticalf("action: serialize | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	err = c.sendAll(buffer)
	if err != nil {
		log.Criticalf("action: send_bet | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	log.Infof("action: send_bet | result: success | client_id: %v | msg: %v",
		c.config.ID,
		bet.String(),
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
	}
	return buffer, nil
}
func (c *Client) readMsg(length int) (string, error) {
	buffer, err := c.readAll(length)
	if err != nil {
		log.Criticalf("action: receive_ack | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return "", err
	}
	msg := string(buffer)
	log.Infof("action: receive_ack | result: success | client_id: %v | msg: %v",
		c.config.ID,
		msg,
	)
	return msg, nil
}

// StartClient sends message to the server and wait for the response
func (c *Client) StartClient() {

	c.createClientSocket()

	bet, err := FromEnvBet()
	if err != nil {
		log.Criticalf("action: create_bet | result: fail | client_id: %v | error: %v",	
			c.config.ID,
			err,
		)
		c.StopClient()
		return
	}

	err = c.sendMsg(bet)
	if err != nil {	
		c.StopClient()
		return
	}
	msg, err := c.readMsg(len(SERVER_ACK + "\n"))
	if err != nil || msg != SERVER_ACK + "\n" {
		c.StopClient()
		return
	}

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