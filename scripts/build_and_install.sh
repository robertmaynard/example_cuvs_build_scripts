#!/usr/bin/bash
set -e
set -x

cmake -S /code/raft/cpp -B "/code/raft/cpp/build/${TARGET_ARCH}" \
      -GNinja \
      -DCMAKE_CUDA_ARCHITECTURES=RAPIDS \
      -DBUILD_SHARED_LIBS=OFF \
      -DCUTLASS_ENABLE_TESTS=OFF \
      -DBUILD_TESTS=OFF

cmake --build "/code/raft/cpp/build/${TARGET_ARCH}" -j16
cmake --install "/code/raft/cpp/build/${TARGET_ARCH}" --prefix /tmp/rapids/

cmake -S /code/cuvs/cpp -B "/code/cuvs/cpp/build/${TARGET_ARCH}" \
      -GNinja \
      -DCMAKE_CUDA_ARCHITECTURES=RAPIDS \
      -DCUVS_COMPILE_DYNAMIC_ONLY=ON \
      -DDISABLE_OPENMP=ON \
      -DCMAKE_PREFIX_PATH=/tmp/rapids \
      -DBUILD_TESTS=OFF
cmake --build "/code/cuvs/cpp/build/${TARGET_ARCH}" -j16
cmake --install "/code/cuvs/cpp/build/${TARGET_ARCH}" --prefix /tmp/rapids/

# remove cutlass test infra that is installed unconditionally
rm -rf /tmp/rapids/test/
tar czf /code/.out/libcuvs_$TARGET_ARCH.tar.gz -C /tmp/rapids/ .
