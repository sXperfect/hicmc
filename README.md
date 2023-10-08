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
---

Before encoding with our tools, a domain information based on a TAD caller (in this case Insulation score) is required.
Please refer to this [link](https://cooltools.readthedocs.io/en/latest/notebooks/insulation_and_boundaries.html) on how to generate the domain file.

Compress a cooler file with a specific resolution
```bash
usage: HiCMC ENCODE [-h] [--check-result] [--insulation-file INSULATION_FILE] [--insulation-window INSULATION_WINDOW] [--weights-precision WEIGHTS_PRECISION] [--domain-mask-statistic {average,sparsity,deviation}] [--domain-mask-threshold DOMAIN_MASK_THRESHOLD] [--domain-values-precision DOMAIN_VALUES_PRECISION] [--distance-table-precision DISTANCE_TABLE_PRECISION]
                    [--balancing BALANCING]
                    input_file resolution output_directory

positional arguments:
  input_file            input file path (.cool or .mcool)
  resolution
  output_directory

options:
  -h, --help            show this help message and exit
  --check-result        Check the decoded contact matrix equals the original matrix
  --insulation-file INSULATION_FILE
  --insulation-window INSULATION_WINDOW
  --weights-precision WEIGHTS_PRECISION
  --domain-mask-statistic {average,sparsity,deviation}
  --domain-mask-threshold DOMAIN_MASK_THRESHOLD
  --domain-values-precision DOMAIN_VALUES_PRECISION
                        Number of bits used for floating-point compression
  --distance-table-precision DISTANCE_TABLE_PRECISION
                        Number of bits used for floating-point compression
  --balancing BALANCING
                        Select a balancing method, default: KR
```

Decompress HiCMC encoded payload
```bash
usage: HiCMC DECODE [-h] input output

positional arguments:
  input       Path to the HiCMC encoded payload
  output      Output directory

options:
  -h, --help  show this help message and exit
```