CUVS tar.gz Proof of Concept
****************************

This directory contains example scripts that can be made to make a cuvs tar.gz that can be relocated to other machines

Docker
------

The ``<os>/<arch>/`` directories contain Docker specifications that allow anyone to produce libcuvs binaries.

* ``linux/arm64/``: Linux on ``aarch64`` architectures.
* ``linux/amd64/``: Linux on ``x86_64`` architectures.


.. code-block:: console

    $ git clone https://github.com/rapidsai/cuvs.git
    $ git clone https://github.com/rapidsai/raft.git
    $ docker build --tag=libcuvs_base_amd64 \
        -f linux/amd64/Dockerfile .
    $ bash ./build_libcuvs.sh libcuvs_base_amd64
    $ ls -l libcuvs


.. code-block:: console

    $ git clone https://github.com/rapidsai/cuvs.git
    $ git clone https://github.com/rapidsai/raft.git
    $ docker build --tag=libcuvs_base_arm64 \
        -f linux/arm64/Dockerfile .
    $ bash ./build_libcuvs.sh libcuvs_base_arm64
    $ ls -l libcuvs
