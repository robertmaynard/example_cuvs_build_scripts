FROM nvidia/cuda:12.9.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      gpg \
      wget \
      git \
      python3 \
      ninja-build

RUN test -f /usr/share/doc/kitware-archive-keyring/copyright || \
wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null && \
echo 'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ jammy main' | tee /etc/apt/sources.list.d/kitware.list >/dev/null && \
apt-get update && \
apt-get install -y cmake


RUN wget https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda-repo-cross-sbsa-ubuntu2204-12-9-local_12.9.0-1_all.deb && \
    dpkg -i cuda-repo-cross-sbsa-ubuntu2204-12-9-local_12.9.0-1_all.deb && \
    cp /var/cuda-repo-cross-sbsa-ubuntu2204-12-9-local/cuda-*-keyring.gpg /usr/share/keyrings/
RUN apt-get update && apt-get install -y --no-install-recommends \
    cuda-cross-sbsa-12-9 \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu

ENV CUDAHOSTCXX=aarch64-linux-gnu-g++ \
    CXX=aarch64-linux-gnu-g++ \
    CC=aarch64-linux-gnu-gcc \
    TARGET_ARCH=arm64
