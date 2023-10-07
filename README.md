# High-Efficiency Contact Matrix Compressor (HiCMC)

Open Source High-Efficiency Contact Matrix

## Usage policy
---

The open source HiCMC codec is made available before scientific publication.

This pre-publication software is preliminary and may contain errors.
The software is provided in good faith, but without any express or implied warranties.
We refer the reader to our [license](LICENSE).

The goal of our policy is that early release should enable the progress of science.
We kindly ask to refrain from publishing analyses that were conducted using this software while its development is in progress.

## Dependencies
---

Python version 3.8 or later is required.
For anaconda or conda user, CMAKE, gcc and gxx libraries are required and can be installed through: `conda install -c conda-forge cmake gxx_linux-64 gcc_linux-64`.
See [requirements.txt](requirements.txt) for the list of required python libraries.

## Building
---

Clone this repository:

    git clone https://github.com/sXperfect/hicmc

Run setup script `setup.sh`

    bash setup.sh

This step will install and compile all dependencies automatically.

## Usage
