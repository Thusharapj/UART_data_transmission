#include "driver/uart.h"
#include "esp_log.h"
#include <string.h>
#include "driver/gpio.h"
#include <stdbool.h>

#define UART_PORT UART_NUM_2 // UART2 port
#define TXD_PIN GPIO_NUM_17 // TX pin
#define RXD_PIN GPIO_NUM_16 // RX pin
#define BUF_SIZE 1024 // Uart buffer size

#define HEADER 0xAA
#define END    0xBB
#define HANDSHAKE_REQ 0xB1
#define HANDSHAKE_RESP 0x55
#define ACK 0x06
#define NACK 0x15

static const char *TAG = "UART_APP";   // log identifier


// CRC-8 calculation (polynomial 0x07)
// data: pointer to the input data buffer
// len: number of bytes in the data buffer
static uint8_t calc_crc8(const uint8_t *data, size_t len) { 
    uint8_t crc = 0x00; // Initialize CRC to 0
    for (size_t i = 0; i < len; i++) { 
        crc ^= data[i]; // XOR current byte with CRC
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80) {  // if msb is 1
                crc = (crc << 1) ^ 0x07;  //left shift current crc by 1 and XOR with 0x07
            } else {
                crc <<= 1;  //left shift by 1
            }
        }
    }
    return crc;
}

// Initialize UART
static void uart_init(void){
    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };
    uart_param_config(UART_PORT, &uart_config);
    uart_set_pin(UART_PORT, TXD_PIN, RXD_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_PORT, BUF_SIZE, 0, 0, NULL, 0); 
}

// Send single byte response (ACK/NACK)
static void send_byte(uint8_t val){
    uart_write_bytes(UART_PORT, (const char *)&val, 1);  /*&val → the address in memory where that 1-byte variable is stored.

                                                        (const char *) → type cast, because uart_write_bytes() expects a pointer to a buffer of char (bytes).*/ 
}

// Wait for handshake from PC
// static bool wait_for_handshake(void){
//     uint8_t byte;  //Holds 1 incoming byte
//     while (1) {
//         int len = uart_read_bytes(UART_PORT, &byte, 1, 100 / portTICK_PERIOD_MS); // 
//         if (len > 0) {
//             if (byte == HANDSHAKE_REQ) {
//                 send_byte(HANDSHAKE_RESP);
//                 ESP_LOGI(TAG, "Handshake successful");
//                 return true;
//             }
//         }
//     }
// }

// Parse and validate a packet
static void handle_packet(uint8_t *data, int len){
    if (data[0] != HEADER || data[len - 1] != END) {
        send_byte(NACK);
        return;
    }

    uint8_t total_len = data[1];  //Extract total length of data packet
    if (len != total_len) {
        ESP_LOGW(TAG, "Length mismatch! Declared=%d, Received=%d", total_len, len);
        send_byte(NACK);
        return;
    }

    uint8_t payload_len = total_len - 4; // header+len+crc+end
    uint8_t *payload = &data[2]; // Payload starts after header and length 
    uint8_t crc_received = data[2 + payload_len];
    uint8_t crc_calculated = calc_crc8(payload, payload_len);

    if (crc_received == crc_calculated) {
        ESP_LOGI(TAG, "Valid packet: %.*s", payload_len, payload);
        send_byte(ACK);
    } else {
        ESP_LOGW(TAG, "CRC mismatch! Got=0x%02X Expected=0x%02X", crc_received, crc_calculated);
        send_byte(NACK);
    }
}

// Main application
void app_main(void){
    uart_init();
    ESP_LOGI(TAG, "UART Initialized");


    uint8_t buffer[BUF_SIZE];

    while (1) {
        int len = uart_read_bytes(UART_PORT, buffer, BUF_SIZE, 100 / portTICK_PERIOD_MS); 
        if (len > 0) {
            ESP_LOGI(TAG, "Received %d bytes", len);
            // ✅ Check if it's a handshake request
            if (len == 1 && buffer[0] == HANDSHAKE_REQ) {
                send_byte(HANDSHAKE_RESP);
                ESP_LOGI(TAG, "Handshake successful");
                continue; // skip packet parsing
            }
            for (int i = 0; i < len; i++) {
                ESP_LOGI(TAG, "Byte[%d] = 0x%02X", i, buffer[i]);   //Easy to debug
            }
            handle_packet(buffer, len);
        }
    }
}
