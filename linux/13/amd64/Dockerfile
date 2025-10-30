FROM nvidia/cuda:13.0.1-devel-rockylinux8.04@sha256:f4aec580fa6c2e4fca93512c2f6b1e54b236f86bb95b258e091121f093125e93

ARG TOOLSET_VERSION=14
ARG CMAKE_VERSION=3.31.8
ARG CMAKE_ARCH=x86_64

RUN dnf install -y \
      gcc-toolset-${TOOLSET_VERSION} \
      git \
      make \
      patch \
      python39 \
      tar \
      wget

RUN echo "source scl_source enable gcc-toolset-${TOOLSET_VERSION}" >> /etc/bashrc;
ENV BASH_ENV=/etc/bashrc

# Fetch and install CMake.
RUN cd /usr/local && wget --quiet https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-${CMAKE_ARCH}.tar.gz && \
   tar zxf cmake-${CMAKE_VERSION}-linux-${CMAKE_ARCH}.tar.gz && \
   rm cmake-${CMAKE_VERSION}-linux-${CMAKE_ARCH}.tar.gz && \
   ln -s /usr/local/cmake-${CMAKE_VERSION}-linux-${CMAKE_ARCH}/bin/cmake /usr/local/bin/cmake

ENV CUDAHOSTCXX=g++ \
    CXX=g++ \
    CC=gcc \
    CUDA_MAJOR=13\
    TARGET_ARCH=amd64
