CUVS tar.gz Proof of Concept
****************************

This directory contains example scripts that can be made to make a cuvs tar.gz that can be relocated to other machines

Docker
------

The ``<os>/<arch>/`` directories contain Docker specifications that allow anyone to produce libcuvs binaries.

* ``linux/arm64/``: Linux on ``aarch64`` architectures.
* ``linux/amd64/``: Linux on ``x86_64`` architectures.


Make sure to have qemu installed and registered with docker:
```
docker run --privileged --rm tonistiigi/binfmt --install all
```


.. code-block:: console

    $ git clone https://github.com/rapidsai/cuvs.git
    $ docker build \
        --platform linux/amd64 \
        --tag=libcuvs_base_12_amd64  \
        -f linux/12/amd64/Dockerfile .
    $ bash ./build_libcuvs.sh amd64 12
    $ ls -l libcuvs


.. code-block:: console

    $ git clone https://github.com/rapidsai/cuvs.git
    $ docker build \
        --platform linux/arm64 \
        --tag=libcuvs_base_12_amd64 \
        -f linux/12/arm64/Dockerfile .
    $ bash ./build_libcuvs.sh amd64 12
    $ ls -l libcuvs
