package main

import (
    "bufio"
    "fmt"
    "net"
)

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

    reader := bufio.NewReader(conn)
    for {
        msg, err := reader.ReadString('\n')
        if err != nil {
            break
        }
        fmt.Printf("Received: %s", msg)
        conn.Write([]byte(msg)) // Echo back
    }
}

