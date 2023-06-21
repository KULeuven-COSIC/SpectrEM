// GPIO related functions specific to RPi4B
// 
// Last Modified: 2023-06-19
// 
// Adapted from https://www.airspayce.com/mikem/bcm2835/
// 
// Copyright (C) 2023 Jesse De Meulemeester
// Copyright (C) 2011-2013 Mike McCauley

#ifndef GPIO_H_
#define GPIO_H_

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

// Note: Specific to RPi4B
#define PERIPHERAL_BASE   0x72000000
#define PERIPHERAL_SIZE   0x01800000

#define GPIO_BASE         PERIPHERAL_BASE + 0x00200000

#define INPUT             0
#define OUTPUT            1

/*! Base of the GPIO registers.
  Available after gpio_init has been called
*/
volatile uint32_t *gpio = (uint32_t *)MAP_FAILED;

/**
 * Initialize the GPIO addresses.
 * 
 * @return EXIT_SUCCESS on success and EXIT_FAILURE on failure
*/
int gpio_init() {
  // Obtain handle to physical memory
  int fd = open ("/dev/gpiomem", O_RDWR | O_SYNC);
  
  if (fd < 0) {
    printf("[\033[31mx\033[0m] Unable to open /dev/gpiomem: %s\n", strerror(errno));
    printf("    If you get 'Permission denied', check if /dev/gpiomem has the correct permissions:\n");
    printf("        $ ls -l /dev/gpiomem\n");
    printf("        crw-rw---- 1 root dialout 239, 0 Sep  7 18:37 /dev/gpiomem\n");
    printf("    If you don't have permission:\n");
    printf("        $ sudo apt install rpi.gpio-common\n");
    printf("        $ sudo adduser your-username-here dialout\n");
    printf("        $ sudo reboot now\n");
    return EXIT_FAILURE;
  }

  gpio = (uint32_t *)mmap(NULL, PERIPHERAL_SIZE, (PROT_READ | PROT_WRITE), MAP_SHARED, fd, 0);

  if (gpio == MAP_FAILED) {
    printf("[\033[31mx\033[0m] GPIO memory map failed: %s\n", strerror(errno));
    if (fd >= 0) {
      close(fd);
    }
    return EXIT_FAILURE;
  }

  if (fd >= 0) {
    close(fd);
  }

  return EXIT_SUCCESS;
}

/**
 * Set the given GPIO pin to the given mode.
 * e.g.:
 *     gpio_fsel(17, OUTPUT);
 *     gpio_fsel(21, INPUT);
 * 
 * @param gpio_pin The GPIO pin for which to set the mode
 * @param mode The mode to set for the given GPIO pin
*/
void gpio_fsel(unsigned int gpio_pin, unsigned int mode) {
  // The function select registrers are 10 pins per 32 bit word, 3 bits per pin
  // First selecting correct function select register
  int fsel_reg = gpio_pin / 10;
  // Calculating shift within this function select register
  int shift = (gpio_pin % 10) * 3;
  // Preparing mask and value
  uint32_t mask = 0b111 << shift;
  uint32_t value = mode << shift;
  // Writing the value into the function select register
  gpio[fsel_reg] = (gpio[fsel_reg] & ~mask) | value;
}

/**
 * Set the given gpio pin to high.
 * 
 * @param gpio_pin The GPIO pin to set to high.
*/
void gpio_set(unsigned int gpio_pin) {
  // The output set registers contain 32 pins per 32 bit word, 1 bit per pin
  // First get the correct output set register
  // The first output set register is at address 0x1c = the 7th (32 bit) register
  int oset_reg = 7 + gpio_pin / 32;
  // Calculating the shift
  int shift = gpio_pin % 32;

  uint32_t value = 1 << shift;

  gpio[oset_reg] = value;
}

/**
 * Set the given gpio pin to low.
 * 
 * @param gpio_pin The GPIO pin to set to low.
*/
void gpio_clear(unsigned int gpio_pin) {
  // The output set registers contain 32 pins per 32 bit word, 1 bit per pin
  // First get the correct output clear register
  // The first output set register is at address 0x28 = the 10th (32 bit) register
  int oclear_reg = 10 + gpio_pin / 32;
  // Calculating the shift
  int shift = gpio_pin % 32;

  uint32_t value = 1 << shift;

  gpio[oclear_reg] = value;
}

#endif  // GPIO_H_
