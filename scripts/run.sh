#!/usr/bin/bash
set -e
set -x

cmake -S /code/raft/cpp -B /code/raft/cpp/build \
      -DCMAKE_CUDA_ARCHITECTURES=RAPIDS \
      -DBUILD_SHARED_LIBS=OFF \
      -DCUTLASS_ENABLE_TESTS=OFF
      -DBUILD_TESTS=OFF

cmake --build /code/raft/cpp/build -j16
cmake --install /code/raft/cpp/build --prefix /tmp/rapids/

cmake -S /code/cuvs/cpp -B /code/cuvs/cpp/build \
      -DCMAKE_CUDA_ARCHITECTURES=RAPIDS \
      -DCUVS_COMPILE_DYNAMIC_ONLY=ON \
      -DCMAKE_PREFIX_PATH=/tmp/rapids \
      -DBUILD_TESTS=OFF
cmake --build /code/cuvs/cpp/build -j16
cmake --install /code/cuvs/cpp/build --prefix /tmp/rapids/

# remove cutlass test infra that is installed unconditionally
rm -rf /tmp/rapids/test/
tar czf /code/.out/libcuvs.tar.gz /tmp/rapids/
