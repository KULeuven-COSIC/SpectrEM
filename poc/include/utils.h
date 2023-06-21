// Help functions to set up the UDP interface
//
// Last Modified: 2023-06-19
//
// Parts of this code are adapted from Transient Fail (https://transient.fail/):
// 
// Copyright (C) 2023 Jesse De Meulemeester
// Copyright (C) 2020 Graz University of Technology

#ifndef UTILS_H_
#define UTILS_H_

#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>

#define NOP1    asm volatile("nop");
#define NOP2    NOP1   NOP1
#define NOP4    NOP2   NOP2
#define NOP8    NOP4   NOP4
#define NOP16   NOP8   NOP8
#define NOP32   NOP16  NOP16
#define NOP64   NOP32  NOP32
#define NOP128  NOP64  NOP64
#define NOP256  NOP128 NOP128
#define NOP512  NOP256 NOP256
#define NOP1024 NOP512 NOP512

#define INS1    asm volatile("udiv x10, x15, x11");
#define INS2    INS1   INS1
#define INS4    INS2   INS2
#define INS8    INS4   INS4
#define INS16   INS8   INS8
#define INS32   INS16  INS16
#define INS64   INS32  INS32
#define INS128  INS64  INS64
#define INS256  INS128 INS128
#define INS512  INS256 INS256
#define INS1024 INS512 INS512

int sockfd;
socklen_t serv_addr_len = sizeof(struct sockaddr_in);
struct sockaddr_in serv_addr;
char buffer[4];

/**
 * Flush the given address from the cache.
 * 
 * @param addr The memory location to flush from the cache.
 */
void flush(void *addr) {
  asm volatile("DC CIVAC, %0" : : "r"(addr));
  asm volatile("DSB ISH");
}

/**
 * Initialize the UDP server.
 * 
 * @param port The port on which to listen.
 */
void initSockServer(uint16_t port) {
  sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

  if (sockfd == -1) {
    perror("Error while opening socket.");
    exit(EXIT_FAILURE);
  }

  memset(&serv_addr, 0, sizeof(serv_addr));

  serv_addr.sin_family = AF_INET;
  serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  serv_addr.sin_port = htons(port);

  if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) == -1) {
    perror("Error while binding socket.");
    exit(EXIT_FAILURE);
  }
}

/**
 * Receive data into the given buffer.
 * 
 * @param buf The buffer into which to copy the data.
 * @param size The length of the buffer.
 */
void receive_buf(unsigned char *buf, ssize_t size) {
  if (recvfrom(sockfd, buf, size, 0, (struct sockaddr *) &serv_addr, &serv_addr_len) == -1) {
    perror("Error while receiving message.");
  }
}

/**
 * Receive an integer.
 * 
 * @param index Pointer to the variable into which to copy the second received
 *              integer.
 */
void receive(int *index) {
  if (recvfrom(sockfd, buffer, sizeof(buffer), 0, (struct sockaddr *) &serv_addr, &serv_addr_len) == -1) {
    perror("Error while receiving message.");
  }

  memcpy(index, buffer, sizeof(int));
}

/**
 * Receive two integers. One is returned, one is copied to the provided address.
 * 
 * @param index Pointer to the variable into which to copy the second received
 *              integer.
 */
int receive2(int *option) {
  int received;
  if (recvfrom(sockfd, buffer, sizeof(buffer), 0, (struct sockaddr *) &serv_addr, &serv_addr_len) == -1) {
    perror("Error while receiving message.");
  }

  memcpy(&received, &buffer[0], sizeof(int));
  memcpy(option, &buffer[4], sizeof(int));

  return received;
}

/**
 * Send the contents of the buffer.
 * 
 * @param buf The buffer containing the data to send.
 * @param size The length of the data in the buffer.
 */
void reply_buf(unsigned char *buf, ssize_t size) {
  if (sendto(sockfd, buf, size, 0, (struct sockaddr *) &serv_addr, serv_addr_len) == -1) {
    perror("Error while sending UDP packet.");
  }
}

/**
 * Send back the last received message.
 */
void reply() {
  if (sendto(sockfd, buffer, sizeof(buffer), 0, (struct sockaddr *) &serv_addr, serv_addr_len) == -1) {
    perror("Error while sending UDP packet.");
  }
}

#endif  // UTILS_H_
