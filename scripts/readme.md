# Post-processing scripts

This directory contains all scripts to extract an encoded bit from an EM side-channel trace. 

## Getting started

To get started, first [obtain some side-channel traces](../traces/readme.md) to evaluate (either by downloading the pre-recoded traces or by collecting your own traces).

## Reproducing paper results

We provide Python scripts to reproduce the results in our paper. Note that these scripts assume the working directory is the root directory of this repository.

### Resource usage

The following table summarizes the approximate resource usage for each script.

Script                        | Description                                         | Section                | Memory   |   Disk    | Run Time |
------------------------------|-----------------------------------------------------|------------------------|:--------:|:---------:|:--------:|
`0-base-experiments.py`       | SpectrEM and MeltEMdown evaluation                  | Table 1 & Section 6.2  | 4.2 GB   |   92 GB   |  20 min. |
`1-additional-experiments.py` | Number of training packets and `udiv` instructions  | Figure 5 & Figure 7    | 4.5 GB   |  110 GB   |  20 min. |
`2-reducing-assumptions.py`   | Reducing evaluation assumptions                     | Section 7              |  12 GB   |   58 GB   | 120 min. |
`3-case-study.py`             | OpenSSH case study                                  | Section 8              | 2.8 GB   |    6 GB   |   2 min. | 


### Troubleshooting

If one of the scripts does not work, please make sure the variable `PRERECORDED_TRACES_DIR` in `reproduce/utils.py` points to the downloaded traces.
By default, they assume the traces have been downloaded into the `traces` directory.

The results of the GMM evaluation may fluctuate slightly. This is because the GMM clustering algorithm initializes its state randomly.

### Base experiment

The first set of experiments evaluates the baseline performance of SpectrEM and MeltEMdown by considering 32 batches for each setup and each gadget. These results are captured in Table 1 (for SpectrEM) and Section 6.1 (for MeltEMdown).

To reproduce these results, first download and extracts the traces in the directory `0-base-experiments/`. The script `reproduce/0-base-experiments.py` will evaluate all batches and print the bit error rates. The estimated runtime of this experiment is around 20 minutes.

<details>
<summary>Expected output</summary>

```
SpectrEM
 -> Control flow gadget
 --> Setup A: GMM: 3.566249% BER (17605 errors in 493656 traces)
 --> Setup A: MLP: 2.608990% BER (12577 errors in 482064 traces)
 --> Setup B: GMM: 2.441396% BER (11900 errors in 487426 traces)
 --> Setup B: MLP: 1.037112% BER (5116 errors in 493293 traces)

 -> Instruction gadget
 --> Setup A: GMM: 0.350081% BER (1758 errors in 502169 traces)
 --> Setup A: MLP: 0.166729% BER (868 errors in 520606 traces)
 --> Setup B: GMM: 0.011030% BER (56 errors in 507726 traces)
 --> Setup B: MLP: 0.007636% BER (40 errors in 523820 traces)

MeltEmdown
 -> Instruction gadget
 --> Setup B: GMM: 0.024760% BER (123 errors in 496773 traces)
 --> Setup B: MLP: 0.006870% BER (36 errors in 524048 traces)
 ```

</details>

 ### Additional experiments

 This set of experiments aims at reproducing Figure 5 (displaying the dependency on the number of training packets) and Figure 7 (showing the dependency on the number of `udiv` instructions for the instruction gadget).

To reproduce these results, first download and extracts the traces in the directory `1-additional-experiments/`. The script `reproduce/1-additional-experiments.py` will evaluate all batches and print the bit error rates. The estimated runtime of this experiment is around 20 minutes. The script will output the raw BERs (see below) and will also generate two figures, saved to `figure5.png` and `figure7.png` (saved in the current working directory)

<details>
<summary>Expected output</summary>

```
Number of training packets
 -> Control flow gadget
 --> Setup A
 ---> 0 training packets: GMM: 49.819737% BER (39383 errors in 79051 traces)
 ---> 0 training packets: MLP: 50.119707% BER (20725 errors in 41351 traces)
 ---> 1 training packets: GMM: 20.024380% BER (15113 errors in 75473 traces)
 ---> 1 training packets: MLP: 19.094462% BER (14461 errors in 75734 traces)
 ---> 2 training packets: GMM: 2.653297% BER (2048 errors in 77187 traces)
 ---> 2 training packets: MLP: 2.215144% BER (1697 errors in 76609 traces)
 ---> 3 training packets: GMM: 2.615720% BER (2014 errors in 76996 traces)
 ---> 3 training packets: MLP: 1.931573% BER (1469 errors in 76052 traces)
 ---> 4 training packets: GMM: 4.071128% BER (3132 errors in 76932 traces)
 ---> 4 training packets: MLP: 3.431515% BER (2591 errors in 75506 traces)
 ---> 5 training packets: GMM: 2.555861% BER (1964 errors in 76843 traces)
 ---> 5 training packets: MLP: 2.027575% BER (1550 errors in 76446 traces)

 -> Control flow gadget
 --> Setup B
 ---> 0 training packets: GMM: 49.784147% BER (39324 errors in 78989 traces)
 ---> 0 training packets: MLP: 49.810675% BER (13681 errors in 27466 traces)
 ---> 1 training packets: GMM: 19.649933% BER (14729 errors in 74957 traces)
 ---> 1 training packets: MLP: 17.635682% BER (13495 errors in 76521 traces)
 ---> 2 training packets: GMM: 2.183830% BER (1666 errors in 76288 traces)
 ---> 2 training packets: MLP: 0.768926% BER (601 errors in 78161 traces)
 ---> 3 training packets: GMM: 1.205993% BER (916 errors in 75954 traces)
 ---> 3 training packets: MLP: 0.741228% BER (575 errors in 77574 traces)
 ---> 4 training packets: GMM: 0.813511% BER (618 errors in 75967 traces)
 ---> 4 training packets: MLP: 0.330147% BER (259 errors in 78450 traces)
 ---> 5 training packets: GMM: 1.530036% BER (1165 errors in 76142 traces)
 ---> 5 training packets: MLP: 0.446059% BER (350 errors in 78465 traces)

 -> Instruction gadget
 --> Setup A
 ---> 0 training packets: GMM: 49.599616% BER (39270 errors in 79174 traces)
 ---> 0 training packets: MLP: 50.108871% BER (32218 errors in 64296 traces)
 ---> 1 training packets: GMM: 15.001644% BER (11866 errors in 79098 traces)
 ---> 1 training packets: MLP: 1.294216% BER (757 errors in 58491 traces)
 ---> 2 training packets: GMM: 0.347608% BER (272 errors in 78249 traces)
 ---> 2 training packets: MLP: 0.124591% BER (101 errors in 81065 traces)
 ---> 3 training packets: GMM: 0.355817% BER (279 errors in 78411 traces)
 ---> 3 training packets: MLP: 0.086086% BER (70 errors in 81314 traces)
 ---> 4 training packets: GMM: 0.450701% BER (349 errors in 77435 traces)
 ---> 4 training packets: MLP: 0.194651% BER (157 errors in 80657 traces)
 ---> 5 training packets: GMM: 0.272697% BER (215 errors in 78842 traces)
 ---> 5 training packets: MLP: 0.055094% BER (45 errors in 81678 traces)

 -> Instruction gadget
 --> Setup B
 ---> 0 training packets: GMM: 49.769609% BER (39424 errors in 79213 traces)
 ---> 0 training packets: MLP: 49.738326% BER (34214 errors in 68788 traces)
 ---> 1 training packets: GMM: 17.287887% BER (13933 errors in 80594 traces)
 ---> 1 training packets: MLP: 1.510312% BER (837 errors in 55419 traces)
 ---> 2 training packets: GMM: 0.005034% BER (4 errors in 79461 traces)
 ---> 2 training packets: MLP: 0.004892% BER (4 errors in 81770 traces)
 ---> 3 training packets: GMM: 0.016398% BER (13 errors in 79278 traces)
 ---> 3 training packets: MLP: 0.012242% BER (10 errors in 81683 traces)
 ---> 4 training packets: GMM: 0.010085% BER (8 errors in 79329 traces)
 ---> 4 training packets: MLP: 0.008557% BER (7 errors in 81809 traces)
 ---> 5 training packets: GMM: 0.012622% BER (10 errors in 79229 traces)
 ---> 5 training packets: MLP: 0.008552% BER (7 errors in 81851 traces)

 Number of udiv instructions
 -> Instruction gadget
 --> Setup B
 ---> 1 udiv instructions: GMM: 49.412818% BER (36985 errors in 74849 traces)
 ---> 1 udiv instructions: MLP: 46.974388% BER (1669 errors in 3553 traces)
 ---> 2 udiv instructions: GMM: 49.244479% BER (36859 errors in 74849 traces)
 ---> 2 udiv instructions: MLP: 46.971706% BER (2125 errors in 4524 traces)
 ---> 4 udiv instructions: GMM: 49.615947% BER (37013 errors in 74599 traces)
 ---> 4 udiv instructions: MLP: 48.287574% BER (1706 errors in 3533 traces)
 ---> 8 udiv instructions: GMM: 49.406487% BER (37002 errors in 74893 traces)
 ---> 8 udiv instructions: MLP: 52.300151% BER (1387 errors in 2652 traces)
 ---> 12 udiv instructions: GMM: 29.524872% BER (22495 errors in 76190 traces)
 ---> 12 udiv instructions: MLP: 19.011459% BER (1377 errors in 7243 traces)
 ---> 16 udiv instructions: GMM: 7.551176% BER (5762 errors in 76306 traces)
 ---> 16 udiv instructions: MLP: 2.054825% BER (931 errors in 45308 traces)
 ---> 24 udiv instructions: GMM: 1.346137% BER (1064 errors in 79041 traces)
 ---> 24 udiv instructions: MLP: 0.772566% BER (613 errors in 79346 traces)
 ---> 32 udiv instructions: GMM: 0.103284% BER (80 errors in 77456 traces)
 ---> 32 udiv instructions: MLP: 0.308869% BER (248 errors in 80293 traces)
 ---> 40 udiv instructions: GMM: 1.574572% BER (1235 errors in 78434 traces)
 ---> 40 udiv instructions: MLP: 0.035764% BER (29 errors in 81088 traces)
 ---> 48 udiv instructions: GMM: 0.017623% BER (14 errors in 79443 traces)
 ---> 48 udiv instructions: MLP: 0.002443% BER (2 errors in 81854 traces)
 ---> 56 udiv instructions: GMM: 0.204944% BER (161 errors in 78558 traces)
 ---> 56 udiv instructions: MLP: 0.002444% BER (2 errors in 81836 traces)
 ---> 64 udiv instructions: GMM: 0.011412% BER (9 errors in 78866 traces)
 ---> 64 udiv instructions: MLP: 0.006107% BER (5 errors in 81876 traces)
 ---> 72 udiv instructions: GMM: 0.019050% BER (15 errors in 78739 traces)
 ---> 72 udiv instructions: MLP: 0.003668% BER (3 errors in 81796 traces)
```

</details>


### Reducing assumptions

This set of experiments evaluates the influence of removing certain simplifications from the POCs, as described in Section 7.

To reproduce these results, first download and extracts the traces in the directory `2-reducing-assumptions/`. The script `reproduce/2-reducing-assumptions.py` will evaluate all batches and print the bit error rates. The estimated runtime of this experiment is around 2 hours.

<details>
<summary>Expected output</summary>

```
Frequency scaling
 -> GMM: 5.557196% BER (25598 errors in 460628 traces)
 -> MLP: 3.236699% BER (14139 errors in 436834 traces)

Core affinity
 -> GMM: 3.758424% BER (15248 errors in 405702 traces)
 -> MLP: 1.790971% BER (7057 errors in 394032 traces)

Flushing
 -> GMM: 22.171808% BER (41487 errors in 187116 traces)
 -> MLP: 13.601243% BER (37565 errors in 276188 traces)
```

</details>


### Case study

The final set of experiments evaluates the performance of two vulnerable code patterns in OpenSSH. This case study is described in Section 8.

To reproduce these results, first download and extracts the traces in the directory `3-case-study/`. The script `reproduce/3-case-study.py` will evaluate all batches and print the bit error rates. The estimated runtime of this experiment is around 2 minutes.

<details>
<summary>Expected output</summary>

```
SSH gadget
 -> GMM: 29.653716% BER (8846 errors in 29831 traces)
 -> MLP: 7.282492% BER (3051 errors in 41895 traces)
SFTP gadget
 -> GMM: 12.842439% BER (5677 errors in 44205 traces)
 -> MLP: 3.719107% BER (2495 errors in 67086 traces)
```

</details>
