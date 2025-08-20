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
    ln, err := net.Listen("tcp", host)
    if err != nil {
        panic(err)
    }
    defer ln.Close()
    fmt.Println("Server listening on", host)

    conn, err := ln.Accept()
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    fmt.Println("Connected by", conn.RemoteAddr())

    buf := make([]byte, 1024) // buffer to read data
    n, err := conn.Read(buf)
    if err != nil {
        panic(err)
    }

    var msg Message
    if err := json.Unmarshal(buf[:n], &msg); err != nil {
        panic(err)
    }

    fmt.Printf("Received JSON: %+v\n", msg)
}

