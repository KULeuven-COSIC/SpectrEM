# SpectrEM: Exploiting Electromagnetic Emanations During Transient Execution

This repository contains the proof-of-concept implementations and post-processing scripts for the paper *SpectrEM: Exploiting Electromagnetic Emanations During Transient Execution*.

## Structure

The directory `poc/` contains the proof-of-concept (POC) implementations used to evaluate the performance of the attacks as performed in Section 6. The construction of these POCs is discussed in detail in Section 5. 

The scripts used to evaluate the recorded traces are located in `scripts/`. These Jupyter notebooks walk through the steps we used to train the MLP network, and evaluate a trace using both evaluation methods. This directory also contains scripts that will programmatically go through all evaluation traces to reproduce the results in our paper.

The directory `traces/` contains more information about using either the pre-recorded traces or collecting your own traces. The scripts included in this repository will assume the traces are located within this directory.

## Pre-Recorded Traces

We provide a [repository of pre-recorded traces](https://rdr.kuleuven.be/dataset.xhtml?persistentId=doi:10.48804/AHTI1A) to enable the reproduction of our results without requiring a similar EM side-channel setup as was used in the paper. These pre-recorded traces cover all experiments in Sections 6 through 8 as well as Appendix C.

Instructions detailing how to download and use these traces can be found [here](./traces/readme.md).


## Getting Started

To get started, first create a new Python environment (python>=3.11) and install all dependencies. For instance, when using Anaconda:

```bash
$ conda create -n spectrem "python>=3.11" ipython
$ conda activate spectrem
$ conda install --file ./requirements.txt
$ pip install tensorflow
```

To start the Jupyter notebook server:
```bash
$ conda activate spectrem
$ jupyter notebook
```

To get started with the evaluation, visit [this notebook](./scripts/evaluate/evaluate_extraction_methods.ipynb) which explains how to access the traces and how to evaluate them.

More information on how to reproduce our results can be found [here](./scripts/readme.md).


## How to cite this work

```
@inproceedings{demeulemeester2023spectrem,
  author    = {De Meulemeester, Jesse and Purnal, Antoon and Wouters, Lennert and Beckers, Arthur and Verbauwhede, Ingrid},
  title     = {{SpectrEM}: Exploiting Electromagnetic Emanations During Transient Execution},
  booktitle = {USENIX Security Symposium},
  year      = {2023},
}
```
