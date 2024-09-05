package common

import (
	"fmt"
	"bytes"
	"encoding/binary"
	"os"
	"strings"

)

const(
	SEPARATOR string = ","
	MSG_LEN int = 4
)
type Bet struct {
	agency string
	first_name string
	last_name string
	identification string
	birthdate string
	number string
}

func NewBet(agency string, first_name string, last_name string, identification string, birthdate string, number string) *Bet {
	bet := &Bet{
		agency: agency,
		first_name: first_name,
		last_name: last_name,
		identification: identification,
		birthdate: birthdate,
		number: number,
	}
	return bet
}

func FromEnvBet() (*Bet, error) {

	bet := NewBet(
		os.Getenv("AGENCY"),
		os.Getenv("FIRST_NAME"),
		os.Getenv("LAST_NAME"),
		os.Getenv("IDENTIFICATION"),
		os.Getenv("BIRTH_DATE"),
		os.Getenv("NUMBER"),
	)
	if bet.agency == "" || bet.first_name == "" || bet.last_name == "" || bet.identification == "" || bet.birthdate == "" || bet.number == "" {
		return nil, fmt.Errorf("Not found required environment variables")
	}
	return bet, nil

}

func (b *Bet) String() string {
    return fmt.Sprintf("%s, %s, %s, %s, %s, %s", b.agency, b.first_name, b.last_name, b.identification, b.birthdate, b.number)
}
func (b *Bet) serialize() ([]byte, error)  {
	var buffer bytes.Buffer
	var msg_len uint32 // 4 bytes

    parts := []string{
        b.agency, b.first_name, b.last_name, b.identification, b.birthdate, b.number,
    }
    
    msg := strings.Join(parts, SEPARATOR)
	msg_encoded := []byte(msg)
	msg_len = uint32(len(msg_encoded))

	if err := binary.Write(&buffer, binary.BigEndian, msg_len); err != nil {
        return nil, err
    }
	buffer.Write(msg_encoded)

	return buffer.Bytes(), nil
}


