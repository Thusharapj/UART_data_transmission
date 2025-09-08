# UART Communication: ESP32 ↔ PC

This project demonstrates reliable **UART communication** between an **ESP32** and a **PC** using custom packet framing, CRC error detection, and handshake/acknowledgment mechanisms.  

The PC sends packets to the ESP32, and the ESP32 validates them using CRC and responds with **ACK/NACK**. A handshake mechanism ensures proper synchronization before any data transmission begins.

---

## 📌 Features
- Custom packet structure: | HEADER | LEN | DATA | CRC | END |
- CRC-8 checksum validation (Polynomial **0x07**).
- Handshake protocol before data transmission.
- ACK/NACK mechanism for reliable communication.
- Debug logging on ESP32 for received packets.

## ⚙️ Hardware Setup
- **ESP32 pins**  
- TX → GPIO 17  
- RX → GPIO 16  
- Connect ESP32 to PC via USB (for power + programming).
- UART2 used for communication.

## 🖥️ Packet Structure
| Field     | Size (bytes) | Description                           |
|-----------|--------------|---------------------------------------|
| `HEADER`  | 1            | Start of packet (0xAA)               |
| `LEN`     | 1            | Total packet length (including all fields) |
| `DATA`    | N            | Payload (ASCII message)              |
| `CRC`     | 1            | CRC-8 checksum of `DATA`             |
| `END`     | 1            | End of packet (0xBB)                 |

✅ Example: Sending `"Hello"` 
AA 08 48 65 6C 6C 6F 92 BB

## 🤝 Handshake Protocol
1. PC → ESP32: Send `0xB1` (**HANDSHAKE_REQ**)  
2. ESP32 → PC: Responds with `0x55` (**HANDSHAKE_RESP**)  
3. Once successful, packet transmission begins.
