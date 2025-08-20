package main

import (
    "bufio"
    "fmt"
    "net"
)

func main() {
    host := "127.0.0.1:5000"

    conn, err := net.Dial("tcp", host)
    if err != nil {
        panic(err)
    }
    defer conn.Close()

    msg := "Hello local server!\n"
    conn.Write([]byte(msg))

    reader := bufio.NewReader(conn)
    resp, _ := reader.ReadString('\n')
    fmt.Printf("Received: %s", resp)
}

