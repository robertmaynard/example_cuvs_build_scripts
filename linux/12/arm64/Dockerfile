FROM nvidia/cuda:12.9.1-devel-rockylinux8.04@sha256:16427be1897c6947f17a7772043ea91552220aa54cae0337cf9788b9eef31389

ARG TOOLSET_VERSION=14
ARG CMAKE_VERSION=3.31.8
ARG CMAKE_ARCH=aarch64

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
    CUDA_MAJOR=12\
    TARGET_ARCH=arm64
