FROM nvidia/cuda:12.9.0-devel-ubuntu22.04@sha256:02b7c7eda5c4c8f431a1fbcb88720bf563817fb753513979e6d373c07ac32d6e

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

ENV CUDAHOSTCXX=g++ \
    CXX=g++ \
    CC=gcc \
    TARGET_ARCH=arm64

