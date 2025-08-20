package main

import (
	"encoding/json"
	"fmt"
	"net"
)

type Message struct {
	User string `json:"user"`
	Text string `json:"text"`
}

func main() {
	host := "127.0.0.1:5000"
	conn, err := net.Dial("tcp", host)
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	// create some placeholder JSON data
	msg := Message{
		User: "Alice",
		Text: "Hello server!",
	}

	data, err := json.Marshal(msg)
	if err != nil {
		panic(err)
	}

	// send JSON as binary
	_, err = conn.Write(data)
	if err != nil {
		panic(err)
	}

	fmt.Println("JSON sent!")
}
