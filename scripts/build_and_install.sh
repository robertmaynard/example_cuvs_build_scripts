#!/usr/bin/bash
set -e
set -x

# Build the cuvs C++ library and dependencies as static
cmake -S /code/cuvs/cpp -B "/code/cuvs/cpp/build/${CUDA_MAJOR}/${TARGET_ARCH}" \
      -DCMAKE_CUDA_FLAGS=-w \
      -DCMAKE_CUDA_ARCHITECTURES=RAPIDS \
      -DBUILD_SHARED_LIBS=OFF \
      -DCUTLASS_ENABLE_TESTS=OFF \
      -DDISABLE_OPENMP=ON \
      -DBUILD_TESTS=OFF \
      -DBUILD_SHARED_LIBS=ON \
      -DCUVS_STATIC_RAPIDS_LIBRARIES=ON
cmake --build "/code/cuvs/cpp/build/${CUDA_MAJOR}/${TARGET_ARCH}" -j16

cmake -S /code/cuvs/c -B "/code/cuvs/c/build/${CUDA_MAJOR}/${TARGET_ARCH}" \
      -DCMAKE_CUDA_FLAGS=-w \
      -DCUVSC_STATIC_CUVS_LIBRARY=ON \
      -DCMAKE_PREFIX_PATH="/code/cuvs/cpp/build/${CUDA_MAJOR}/${TARGET_ARCH}" \
      -DBUILD_TESTS=OFF

cmake --build "/code/cuvs/c/build/${CUDA_MAJOR}/${TARGET_ARCH}" -j16
cmake --install "/code/cuvs/c/build/${CUDA_MAJOR}/${TARGET_ARCH}" --prefix /tmp/rapids/

tar czf /code/.out/libcuvs_${CUDA_MAJOR}_${TARGET_ARCH}.tar.gz -C /tmp/rapids/ .
