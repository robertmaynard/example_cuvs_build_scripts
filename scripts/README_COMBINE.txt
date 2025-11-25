# Python Implementation of validate_and_combine

This directory contains a tarball validation and combination tool.

## Files

- **validate_and_combine.py**: Python 3 implementation
- **test_validate_and_combine.py**: test suite

### Usage

```bash
# Example
python3 validate_and_combine.py libcuvs_c_12.9.1.tar.gz libcuvs_c_13.0.1.tar.gz
```

The script will automatically:
1. Extract package name from first tarball
2. Validate headers are identical and install one set
3. install the lib64 from both tarballs into cuda versioned subdirectories
4. package LICENSE files into the output tarball
5. Combine into a single tarball with format: `<package>-linux-<arch>-<version>.tar.gz`


### Output Format

The output filename is automatically generated as:
```
${package}-${os}-${arch}-${version}.tar.gz
```

Where:
- **package**: Extracted from first tarball (e.g., `libcuvs` or `libcuvs_c`)
- **os**: Always `linux`
- **arch**: Detected from DSO files (`x86_64` or `sbsa`)
- **version**: Extracted from DSO version strings (e.g., `25.12.00`)

