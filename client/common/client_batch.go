package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
)


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