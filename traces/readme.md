# Traces

This document goes over how to obtain the pre-recorded traces, and details the required setup to collect your own EM side-channel traces to reproduce the results in the paper.


## Pre-recorded traces

The pre-recorded traces can be downloaded from the following data repository: https://rdr.kuleuven.be/dataset.xhtml?persistentId=doi:10.48804/AHTI1A

As this repository does not provide a way to download all traces at once, we provide a small Python script to download and extract them automatically. Run the Python script and follow the instructions to select which directories to download.

```bash
$ conda activate spectrem
$ python download-traces.py
```

The traces are compressed and split into 5 GiB partitions. To extract the raw traces manually, combine the different parts and extract the raw traces from the tar archive.

```bash
$ cd 0-base-experiments/
$ cat 0-base-experiments.tar.bz2.part* | tar xvfj -
```

### File structure

The extracted traces follow the structure as described in the table below. Each directory contains the traces for a specific set of experiments.

Folder                    | Description                                         | Section                | Download size | Extracted size |
--------------------------|-----------------------------------------------------|------------------------|:-------------:|:--------------:|
0-base-experiments/       | SpectrEM and MeltEMdown evaluation                  | Table 1 & Section 6.2  | 33 GB         |  59 GB         |
1-additional-experiments/ | Number of training packets and `udiv` instructions  | Figure 5 & Figure 7    | 39 GB         |  71 GB         |
2-reducing-assumptions/   | Reducing evaluation assumptions                     | Section 7              | 21 GB         |  37 GB         |
3-case-study/             | OpenSSH case study                                  | Section 8              |  2 GB         |   4 GB         |
4-mlp-data/               | Data for MLP training and evaluation                |                        | 89 GB         | 163 GB         |


### Reproducing results

To reproduce the results presented in our paper, we provide scripts that automatically group the results. More information can be found [here](../scripts/readme.md).


### License

The pre-recorded traces are licensed under CC-BY-4.0.


## Collecting traces

We now describe the required setup and steps to perform to collect your own side-channel traces to evaluate the SpectrEM and MeltEMdown POCs.

### Measurement setup

To measure the electromagnetic emanations resulting from the transient instructions, the following components are required.


  * Target platform  
    All experiments are built around the Arm Cortex-A72. Remove the integrated heat spreader to allow the EM probe close access to the IC.
  * EM probe  
    An EM probe with a sufficiently high spatial locality. For instance, the probes used in the paper are the [Langer HH500-6](https://www.langer-emv.de/en/product/near-field-microprobes-icr-hh-h-field/26/icr-hh500-6-near-field-microprobe-2-mhz-to-6-ghz/108) (setup A) and the [Langer RF-R 0.3-3](https://www.langer-emv.de/en/product/rf-passive-30-mhz-up-to-3-ghz/35/rf-r-0-3-3-h-field-probe-mini-30-mhz-up-to-3-ghz/18) (setup B). Set up your EM probe to measure the normal EM field (i.e., the field perpendicular to the IC surface) and place it near the optimal position for a specific core (e.g., core 1), as indicated in Figure 4. Please note that different probes may result in different observed results.
  * Amplifiers  
    If required, add amplifiers between the scope and the probe to boost the measured signal. In our setups, we used either a 20 dB (setup A) or a 50 dB (setup B) amplification.
  * Oscilloscope  
    An oscilloscope with a sufficiently high sampling rate and bandwidth. In our experiments, we used the Tektronix DPO70604C with an analog bandwidth of 6 GHz and a sampling rate of 25 GS/s.

### Setting up the target device

Please refer to the [following file](../poc/readme.md) on how to compile and run the POCs. The linked document also describes the simplifications introduced for evaluation purposes and how to set them up.

### Collecting traces

We provide a [jupyter notebook](../scripts/collect/collect-traces.ipynb) that details how to collect traces from the POCs. 
The gadgets implemented in our POCs are accessible over a UDP interface. To access the gadget, simply provide the bit index to access to the specified UDP port (10000 by default).

