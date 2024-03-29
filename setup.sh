readonly git_root_directory="$(git rev-parse --show-toplevel)"
echo "root directory: ${git_root_directory}"

readonly third_party_directory="${git_root_directory}/third-party"

#? JBIG
readonly jbig_directory="${third_party_directory}/jbigkit-2.1"
(
    cd ${third_party_directory}
    rm -rf jbigkit-2.1
    tar xzvf jbigkit-2.1.tar.gz
    cd "${jbig_directory}"
    cd libjbig && make && cd ..
    cd pbmtools && make
)

#? 7zip
readonly szip_directory="${third_party_directory}/szip-x64"
(
    cd ${third_party_directory}
    rm -rf szip-x64
    mkdir ${szip_directory}
    tar xfv 7z-linux-x64.tar.xz -C ${szip_directory}
)