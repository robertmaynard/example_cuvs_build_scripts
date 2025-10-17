#!/usr/bin/bash

set -e
set -x

docker run -it --rm --ipc=host \
  -v $(pwd)/cuvs/:/code/cuvs \
  -v $(pwd)/scripts/:/code/scripts \
  -v $(pwd)/:/code/.out \
  -w /code/ \
  --platform linux/$1 \
  libcuvs_base_$1 \
  /bin/bash /code/scripts/build_and_install.sh

