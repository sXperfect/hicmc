# High-Efficiency Contact Matrix Compressor (HiCMC)

This is the open-source software **HiCMC**.
Through sophisticated biological modeling we enable highly efficient compression of Hi-C contact matrices.

## Quick start

For a smooth quick start, we provide a test file that can be downloaded and extracted.
We have tested this software on `Ubuntu` operating system with `conda` software.

First, clone the repository and enter the directory:

```shell
git clone https://github.com/sXperfect/hicmc
cd hicmc
```

Create a virtual environment using `conda` and install necessary libraries
```shell
conda create -y -n hicmc python=3.11
conda activate hicmc
conda install -y -c conda-forge cmake gxx_linux-64 gcc_linux-64 zlib curl
```

Install cython and python libraries
```shell
pip install -r requirements.txt
pip install --pre bitstream
```

Run setup script `setup.sh`:

```shell
bash setup.sh
```

First, download the necessary input file from `Gene Expression Omnibus` with accession code `GSE63525` of filename ``:
```bash
wget https://ftp.ncbi.nlm.nih.gov/geo/series/GSE63nnn/GSE63525/suppl/GSE63525%5FGM12878%5Finsitu%5Fprimary%2Ehic
```

```shell
wget https://www.tnt.uni-hannover.de/staff/adhisant/hicmc/quickstart-data.tar.gz
tar -xvzf quickstart-data.tar.gz
```

Encode the data with **HiCMC**:

```shell
$input_file="quickstart-data.cool"
$resolution=50
$output_directory="quickstart_output"
HiCMC ENCODE ${input_file} ${resolution} ${output_directory}
```

## Usage policy

The open-source HiCMC codec is made available before scientific publication.

This pre-publication software is preliminary and may contain errors.
The software is provided in good faith, but without any express or implied warranties.
We refer the reader to our [license](LICENSE).

The goal of our policy is that early release should enable the progress of science.
We kindly ask to refrain from publishing analyses that were conducted using this software while its development is in progress.

## Dependencies

Python 3.8 or higher is required.
It is recommended that you create a virtual environment using conda.
For conda users, the `cmake`, `gcc`, `zlib`, `curl`, and `gxx` libraries are required and can be installed through this link:
```shell
conda install -c conda-forge cmake gxx_linux-64 gcc_linux-64 zlib curl
```
See [requirements.txt](requirements.txt) for the list of required Python libraries.

## Building

Clone this repository:

    git clone https://github.com/sXperfect/hicmc

Create a virtual environment using conda
```shell
conda create -n hicmc python=3.8
```

Install necessary libraries
```shell
conda install -c conda-forge cmake gxx_linux-64 gcc_linux-64 zlib curl
```

Install python libraries
```shell
python -m pip install -r requirements.txt
```

Run setup script `setup.sh`

```shell
bash setup.sh
```

This step will install and compile all dependencies automatically.

## Usage

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
