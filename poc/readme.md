# Proof-of-concept implementations

This folder contains the proof-of-concept (POC) implementations of the
SpectrEM and MeltEMdown attacks. 

## Target device

We performed our experiments on the Raspberry Pi 4 model B (2 GB, Rev 1.1). All POCs in this directory are implemented specifically for this device.
All experiments were performed while running Ubuntu 20.04 LTS (64-bit) with kernel version 5.4.0-1088-raspi.

## Setting up the target

To evaluate the POC implementations, we introduced a few simplifications in our paper to ease the evaluation process.
1. We lock the clock frequency at 600 MHz. When running Ubuntu on the Raspberry Pi, this can be done as follows:
```bash
$ sudo su
$ echo "600000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
$ echo "600000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
$ exit 
```
2. We lock the core to one specific core and optimize the probe position for that specific core. In our experiments, we used either core 0 or 1 as these cores exhibited the most leakage. By default, the makefile assigns the POC to core 1.
3. We add a trigger signal to the POC. By default, this will trigger GPIO pin 16 on the Raspberry Pi.

## Build

To build the POCs:  
`make all`  


## Run

To run one of the three POCs:  
`make start_spectrem_cf`  
`make start_spectrem_ins`  
`make start_meltemdown`  

To stop a running POC:  
`make stop_spectrem_cf`  
`make stop_spectrem_ins`  
`make stop_meltemdown`  

## Collecting traces  

This section gives an overview of how to interface with the POC gadgets. For an example implementation, see [collect-traces.ipynb](../scripts/collect/collect_traces.ipynb).

### SpectrEM  
A UDP interface exposes the gadgets in the POC implementations of the Spectre
attack. The following code can be used to access a given bit index of the array.  

```python
import socket
import struct

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(5)

addr = ("IP_OF_VICTIM", 10000)

def access_bit(index: int):
  message = struct.pack("<I", index)  # Note: assumes little-endianness
    
  client_socket.sendto(message, addr)
  data, _ = client_socket.recvfrom(1024)
    
  assert message == data  # Server should return the same message
```  
  
The POC implementation will clear GPIO pin 16 after each access to the gadget.
This allows the oscilloscope to be triggered.

### MeltEMdown  
The MeltEMdown POC is based on
[spec_poc_arm](https://github.com/lgeek/spec_poc_arm) by Cosmin Gorgovan. This
POC was modified to leak the contents of the system registers through the
electromagnetic covert channel leveraging instructions with operand-dependent
timings.
```python
import socket
import struct

sregs = {"ACTLR_EL1" : b"\x23\x10\x38\xd5", "ACTLR_EL2" : b"\x23\x10\x3c\xd5", "ACTLR_EL3" : b"\x23\x10\x3e\xd5", "AIDR_EL1" : b"\xe3\x00\x39\xd5", "AFSR0_EL1" : b"\x03\x51\x38\xd5", "AFSR0_EL2" : b"\x03\x51\x3c\xd5", "AFSR0_EL3" : b"\x03\x51\x3e\xd5", "AFSR1_EL1" : b"\x23\x51\x38\xd5", "AFSR1_EL2" : b"\x23\x51\x3c\xd5", "AFSR1_EL3" : b"\x23\x51\x3e\xd5", "AMAIR_EL1" : b"\x03\xa3\x38\xd5", "AMAIR_EL2" : b"\x03\xa3\x3c\xd5", "AMAIR_EL3" : b"\x03\xa3\x3e\xd5", "CCSIDR_EL1" : b"\x03\x00\x39\xd5", "CLIDR_EL1" : b"\x23\x00\x39\xd5", "CPACR_EL1" : b"\x43\x10\x38\xd5", "CPTR_EL2" : b"\x43\x11\x3c\xd5", "CPTR_EL3" : b"\x43\x11\x3e\xd5", "CSSELR_EL1" : b"\x03\x00\x3a\xd5", "CTR_EL0" : b"\x23\x00\x3b\xd5", "DISR_EL1" : b"\x23\xc1\x38\xd5", "ERRIDR_EL1" : b"\x03\x53\x38\xd5", "ERRSELR_EL1" : b"\x23\x53\x38\xd5", "ERXADDR_EL1" : b"\x63\x54\x38\xd5", "ERXCTLR_EL1" : b"\x23\x54\x38\xd5", "ERXFR_EL1" : b"\x03\x54\x38\xd5", "ERXMISC0_EL1" : b"\x03\x55\x38\xd5", "ERXMISC1_EL1" : b"\x23\x55\x38\xd5", "ERXSTATUS_EL1" : b"\x43\x54\x38\xd5", "ESR_EL1" : b"\x03\x52\x38\xd5", "ESR_EL2" : b"\x03\x52\x3c\xd5", "ESR_EL3" : b"\x03\x52\x3e\xd5", "HACR_EL2" : b"\xe3\x11\x3c\xd5", "HCR_EL2" : b"\x03\x11\x3c\xd5", "ID_AFR0_EL1" : b"\x63\x01\x38\xd5", "ID_DFR0_EL1" : b"\x43\x01\x38\xd5", "ID_ISAR0_EL1" : b"\x03\x02\x38\xd5", "ID_ISAR1_EL1" : b"\x23\x02\x38\xd5", "ID_ISAR2_EL1" : b"\x43\x02\x38\xd5", "ID_ISAR3_EL1" : b"\x63\x02\x38\xd5", "ID_ISAR4_EL1" : b"\x83\x02\x38\xd5", "ID_ISAR5_EL1" : b"\xa3\x02\x38\xd5", "ID_ISAR6_EL1" : b"\xe3\x02\x38\xd5", "ID_MMFR0_EL1" : b"\x83\x01\x38\xd5", "ID_MMFR1_EL1" : b"\xa3\x01\x38\xd5", "ID_MMFR2_EL1" : b"\xc3\x01\x38\xd5", "ID_MMFR3_EL1" : b"\xe3\x01\x38\xd5", "ID_MMFR4_EL1" : b"\xc3\x02\x38\xd5", "ID_PFR0_EL1" : b"\x03\x01\x38\xd5", "ID_PFR1_EL1" : b"\x23\x01\x38\xd5", "ID_AA64DFR0_EL1" : b"\x03\x05\x38\xd5", "ID_AA64ISAR0_EL1" : b"\x03\x06\x38\xd5", "ID_AA64ISAR1_EL1" : b"\x23\x06\x38\xd5", "ID_AA64MMFR0_EL1" : b"\x03\x07\x38\xd5", "ID_AA64MMFR1_EL1" : b"\x23\x07\x38\xd5", "ID_AA64MMFR2_EL1" : b"\x43\x07\x38\xd5", "ID_AA64PFR0_EL1" : b"\x03\x04\x38\xd5", "IFSR32_EL2" : b"\x23\x50\x3c\xd5", "LORC_EL1" : b"\x63\xa4\x38\xd5", "LORID_EL1" : b"\xe3\xa4\x38\xd5", "LORN_EL1" : b"\x43\xa4\x38\xd5", "MDCR_EL3" : b"\x23\x13\x3e\xd5", "MIDR_EL1" : b"\x03\x00\x38\xd5", "MPIDR_EL1" : b"\xa3\x00\x38\xd5", "PAR_EL1" : b"\x03\x74\x38\xd5", "RVBAR_EL3" : b"\x23\xc0\x3e\xd5", "REVIDR_EL1" : b"\xc3\x00\x38\xd5", "SCTLR_EL1" : b"\x03\x10\x38\xd5", "SCTLR_EL3" : b"\x03\x10\x3e\xd5", "TCR_EL1" : b"\x43\x20\x38\xd5", "TCR_EL2" : b"\x43\x20\x3c\xd5", "TCR_EL3" : b"\x43\x20\x3e\xd5", "TTBR0_EL1" : b"\x03\x20\x38\xd5", "TTBR0_EL2" : b"\x03\x20\x3c\xd5", "TTBR0_EL3" : b"\x03\x20\x3e\xd5", "TTBR1_EL1" : b"\x23\x20\x38\xd5", "TTBR1_EL2" : b"\x23\x20\x3c\xd5", "VDISR_EL2" : b"\x23\xc1\x3c\xd5", "VSESR_EL2" : b"\x63\x52\x3c\xd5", "VTCR_EL2" : b"\x43\x21\x3c\xd5", "VTTBR_EL2" : b"\x03\x21\x3c\xd5", "AFSR0_EL12" : b"\x03\x51\x3d\xd5", "AFSR1_EL12" : b"\x23\x51\x3d\xd5", "AMAIR_EL12" : b"\x03\xa3\x3d\xd5", "CNTFRQ_EL0" : b"\x03\xe0\x3b\xd5", "CNTHCTL_EL2" : b"\x03\xe1\x3c\xd5", "CNTHP_CTL_EL2" : b"\x23\xe2\x3c\xd5", "CNTHP_CVAL_EL2" : b"\x43\xe2\x3c\xd5", "CNTHP_TVAL_EL2" : b"\x03\xe2\x3c\xd5", "CNTHV_CTL_EL2" : b"\x23\xe3\x3c\xd5", "CNTHV_CVAL_EL2" : b"\x43\xe3\x3c\xd5", "CNTHV_TVAL_EL2" : b"\x03\xe3\x3c\xd5", "CNTKCTL_EL1" : b"\x03\xe1\x38\xd5", "CNTKCTL_EL12" : b"\x03\xe1\x3d\xd5", "CNTP_CTL_EL0" : b"\x23\xe2\x3b\xd5", "CNTP_CTL_EL02" : b"\x23\xe2\x3d\xd5", "CNTP_CVAL_EL0" : b"\x43\xe2\x3b\xd5", "CNTP_CVAL_EL02" : b"\x43\xe2\x3d\xd5", "CNTP_TVAL_EL0" : b"\x03\xe2\x3b\xd5", "CNTP_TVAL_EL02" : b"\x03\xe2\x3d\xd5", "CNTPCT_EL0" : b"\x23\xe0\x3b\xd5", "CNTPS_CTL_EL1" : b"\x23\xe2\x3f\xd5", "CNTPS_CVAL_EL1" : b"\x43\xe2\x3f\xd5", "CNTPS_TVAL_EL1" : b"\x03\xe2\x3f\xd5", "CNTV_CTL_EL0" : b"\x23\xe3\x3b\xd5", "CNTV_CTL_EL02" : b"\x23\xe3\x3d\xd5", "CNTV_CVAL_EL0" : b"\x43\xe3\x3b\xd5", "CNTV_CVAL_EL02" : b"\x43\xe3\x3d\xd5", "CNTV_TVAL_EL0" : b"\x03\xe3\x3b\xd5", "CNTV_TVAL_EL02" : b"\x03\xe3\x3d\xd5", "CNTVCT_EL0" : b"\x43\xe0\x3b\xd5", "CNTVOFF_EL2" : b"\x63\xe0\x3c\xd5", "CONTEXTIDR_EL1" : b"\x23\xd0\x38\xd5", "CONTEXTIDR_EL12" : b"\x23\xd0\x3d\xd5", "CONTEXTIDR_EL2" : b"\x23\xd0\x3c\xd5", "CPACR_EL12" : b"\x43\x10\x3d\xd5", "DACR32_EL2" : b"\x03\x30\x3c\xd5", "ESR_EL12" : b"\x03\x52\x3d\xd5", "FAR_EL1" : b"\x03\x60\x38\xd5", "FAR_EL12" : b"\x03\x60\x3d\xd5", "FAR_EL2" : b"\x03\x60\x3c\xd5", "FAR_EL3" : b"\x03\x60\x3e\xd5", "FPEXC32_EL2" : b"\x03\x53\x3c\xd5", "HPFAR_EL2" : b"\x83\x60\x3c\xd5", "HSTR_EL2" : b"\x63\x11\x3c\xd5", "ID_AA64AFR0_EL1" : b"\x83\x05\x38\xd5", "ID_AA64AFR1_EL1" : b"\xa3\x05\x38\xd5", "ID_AA64DFR1_EL1" : b"\x23\x05\x38\xd5", "ID_AA64PFR1_EL1" : b"\x23\x04\x38\xd5", "ISR_EL1" : b"\x03\xc1\x38\xd5", "LOREA_EL1" : b"\x23\xa4\x38\xd5", "LORSA_EL1" : b"\x03\xa4\x38\xd5", "MAIR_EL1" : b"\x03\xa2\x38\xd5", "MAIR_EL12" : b"\x03\xa2\x3d\xd5", "MAIR_EL2" : b"\x03\xa2\x3c\xd5", "MAIR_EL3" : b"\x03\xa2\x3e\xd5", "MDCR_EL2" : b"\x23\x11\x3c\xd5", "MVFR0_EL1" : b"\x03\x03\x38\xd5", "MVFR1_EL1" : b"\x23\x03\x38\xd5", "MVFR2_EL1" : b"\x43\x03\x38\xd5", "RMR_EL3" : b"\x43\xc0\x3e\xd5", "SCR_EL3" : b"\x03\x11\x3e\xd5", "SCTLR_EL12" : b"\x03\x10\x3d\xd5", "SCTLR_EL2" : b"\x03\x10\x3c\xd5", "SDER32_EL3" : b"\x23\x11\x3e\xd5", "TCR_EL12" : b"\x43\x20\x3d\xd5", "TPIDR_EL0" : b"\x43\xd0\x3b\xd5", "TPIDR_EL1" : b"\x83\xd0\x38\xd5", "TPIDR_EL2" : b"\x43\xd0\x3c\xd5", "TPIDR_EL3" : b"\x43\xd0\x3e\xd5", "TPIDRRO_EL0" : b"\x63\xd0\x3b\xd5", "TTBR0_EL12" : b"\x03\x20\x3d\xd5", "TTBR1_EL12" : b"\x23\x20\x3d\xd5", "VBAR_EL1" : b"\x03\xc0\x38\xd5", "VBAR_EL12" : b"\x03\xc0\x3d\xd5", "VBAR_EL2" : b"\x03\xc0\x3c\xd5", "VBAR_EL3" : b"\x03\xc0\x3e\xd5", "VMPIDR_EL2" : b"\xa3\x00\x3c\xd5", "VPIDR_EL2" : b"\x03\x00\x3c\xd5"}

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(5)

addr = ("IP_OF_VICTIM", 10000)

def access_bit(index: int, register_name: str):
  msg = struct.pack("<I", index) + sregs[regsiter_name]
    
  client_socket.sendto(msg, addr)
  data, _ = client_socket.recvfrom(1024)

  assert msg == data  # Server should return the same message
```  
The POC implementation will set GPIO pin 16 before executing the leaking instructions.
This allows the oscilloscope to be triggered.
