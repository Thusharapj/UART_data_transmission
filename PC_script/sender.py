import serial
import time

HEADER = 0xAA   # Header byte for the data packet
END = 0xBB      # End byte
ACK = 0x06      # Ack byte
NACK = 0x15     # Nack byte
HANDSHAKE_REQ = 0xB1  # Handshake request byte
HANDSHAKE_RESP = 0x55 # Handshake response byte
MAX_RETRIES = 3  # Maximum number of retries for ACK/NACK and Handshake
TIMEOUT = 1.0  # seconds for waiting ACK/NACK

# CRC-8 (polynomial 0x07)
def calc_crc8(data: bytes) -> int:  # Calculate CRC-8 checksum
    crc = 0x00   # Initial CRC value
    for b in data: # Iterate each byte in the data
        crc ^= b  # XOR each byte with the CRC value
        for _ in range(8): # iterating thorugh each bit in the input bytes
            if crc & 0x80:  # 0x80 is 1000000 in binary
                crc = ((crc << 1) & 0xFF) ^ 0x07  # Shift left and XOR with 0x07 if MSB is 1
            else:
                crc = (crc << 1) & 0xFF  # Shift left if MSB is 0
    return crc

# Build the packet: HEADER | LEN | DATA | CRC | END
def build_packet(msg: str) -> bytes:   # defines a function build_packet that takes a string msg and returns a bytes object
    data = msg.encode('ascii') # encode the message to ascii bytes
    total_len = 1 + 1 + len(data) + 1 + 1  # header + len + data + crc + end  total data packet length
    crc = calc_crc8(data)  # Calculate CRC-8 checksum
    packet = bytearray([HEADER, total_len])  # Create a bytearray with header and total length
    packet.extend(data) # Add data bytes to the packet
    packet.append(crc) # Add CRC byte to the packet
    packet.append(END) # Add end byte to the packet
    return bytes(packet) # converts the bytearray to a bytes object and return it

# Perform handshake with ESP32
def handshake(ser: serial.Serial) -> bool:      # Defines a function handshake that takes a serial.Serial object (ser) as input.
    """Perform a handshake with the ESP32.

    This function sends a handshake request byte (HANDSHAKE_REQ) to the ESP32 and waits for a response.
    If a valid response (HANDSHAKE_RESP) is received, the handshake is considered successful.
    If no response is received within the timeout period, the function retries up to MAX_RETRIES times.

    Args:
        ser (serial.Serial): The serial port object used to communicate with the ESP32.

    Returns:
        bool: True if the handshake is successful, False otherwise.
    """
    for attempt in range(1, MAX_RETRIES + 1):  # try the handshake from 1 to 3 (MAX_RETRIES)
        print(f"Handshake attempt {attempt}: Sending 0x{HANDSHAKE_REQ:02X}")
        ser.write(bytes([HANDSHAKE_REQ]))
        ser.flush() # flush the serial port buffer

        start_time = time.time()  # Record the start time for timeout
        while time.time() - start_time < TIMEOUT:  # wait for the response for 1 second from esp32
            if ser.in_waiting > 0:  # if there is data in the serial port buffer
                resp = ser.read(1)[0]  # read 1 byte from the serial port buffer
                if resp == HANDSHAKE_RESP: 
                    print("Handshake successful!\n")
                    return True
        print("No handshake response. Retrying...\n")
    print("Failed to handshake with ESP32.\n")
    return False

# Send a packet and wait for ACK/NACK
def send_packet(ser: serial.Serial, msg: str) -> bool:
    """Send a packet to the ESP32 and wait for ACK/NACK.

    This function builds a packet using the build_packet function, sends it to the ESP32,
    and waits for a response (ACK or NACK) within a timeout period. If a valid response is
    received, the function returns True. If no response is received after MAX_RETRIES attempts,
    the function returns False.

    Args:
        ser (serial.Serial): The serial port object used to communicate with the ESP32.
        msg (str): The message to be sent to the ESP32.

    Returns:
        bool: True if the packet is successfully delivered (ACK received), False otherwise.
    """
    packet = build_packet(msg) # build the packet
    for attempt in range(1, MAX_RETRIES + 1):  # try the packet send from 1 to 3 (MAX_RETRIES)
        print(f"Attempt {attempt}: Sending packet: {packet.hex()}")  # print the packet in hex format
        ser.write(packet)   # write the packet to the serial port
        ser.flush()  # flush the serial port buffer

        start_time = time.time()    # Record the start time for timeout
        while time.time() - start_time < TIMEOUT:  # wait for the response for 1 second from esp32
            if ser.in_waiting > 0:  # if there is data in the serial port buffer
                resp = ser.read(1)[0]  # read 1 byte from the serial port buffer
                if resp == ACK: 
                    print("ACK received. Packet delivered successfully.\n")
                    return True
                elif resp == NACK:
                    print("NACK received. Retrying...\n")
                    break    # break the loop if NACK is received
        else:
            print("No response. Retrying...\n")      # print if no response is received
    print("Failed to send packet after max retries.\n") 
    return False

if __name__ == "__main__":
    ser = serial.Serial("COM7", 115200, timeout=0.1)
    time.sleep(2)  # Give ESP32 time to initialize

    if not handshake(ser):  # if handshake fails
        ser.close() #   close serial port
        exit()

    # Now send data packets
    messages = ["Hello", "ESP32", "UART Test"] 
    for msg in messages:
        success = send_packet(ser, msg) 
        if not success:
            print(f"Failed to send message: {msg}")

    ser.close()
