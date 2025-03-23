package common

import (
	"encoding/csv"
	"io"
	"strings"
)

func (c *Client) readBetsFromFile(csvReader *csv.Reader, maxAmount int) []Bet {
	totalBytes := 0
	var bets []Bet
	
	for {
		record, err := csvReader.Read()
		if err != nil {
			if err == io.EOF {
				break
			}
			log.Errorf("action: read_csv | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return nil
		}

		recordStr := strings.Join(record, ",") + "\n"
		recordBytes := len(recordStr)
		
		totalBytes += recordBytes
		
		bet := NewBet(c.config.ID, record[0], record[1], record[2], record[3], record[4])
		bets = append(bets, *bet)
		
		if totalBytes >= BATCH_MAX_AMOUNT_BYTES {
			break
		}
		
	}
	return bets
}