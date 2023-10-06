readonly git_root_directory="$(git rev-parse --show-toplevel)"
echo "root directory: ${git_root_directory}"

readonly third_party_directory="${git_root_directory}/third-party"

#? JBIG
readonly jbig_directory="${third_party_directory}/jbigkit-2.1"
(
    cd ${third_party_directory}
    tar xzvf jbigkit-2.1.tar.gz
    cd "${jbig_directory}"
    make --jobs
)

# readonly bsc_directory="${third_party_directory}/bsc-3.2.4"
# (
#     unzip bsc-3.2.4-src.zip -d ${bsc_directory}
#     cd ${bsc_directory}
#     make install PREFIX="./build"
#     make clean
# )

#? 7zip
readonly szip_directory="${third_party_directory}/szip-x64"
(
    cd ${third_party_directory}
    mkdir ${szip_directory} && tar xfv 7z-linux-x64.tar.xz -C ${szip_directory}
)