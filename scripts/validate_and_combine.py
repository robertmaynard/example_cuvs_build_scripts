#!/usr/bin/env python3
"""
Validate and combine two CUDA version tarballs into a single multi-CUDA tarball.

This script validates that headers are identical between two tarballs containing
different CUDA versions, then combines them into a single tarball with versioned
lib64 directories.

Usage:
    python validate_and_combine.py <tarball1> <tarball2>

Output filename format:
    <package>-<os>-<arch>-<version>.tar.gz
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class TarballCombinerError(Exception):
    """Base exception for tarball combiner errors."""
    pass


def extract_package_name(filename: str) -> Optional[str]:
    """
    Extract package name from filename.

    Examples:
        libcuvs.tar.gz -> libcuvs
        libcuvs_c.12.0.tar.gz -> libcuvs_c
        libcuvs_12_amd64.tar.gz -> libcuvs
        libcuvs_c_12_amd64.tar.gz -> libcuvs_c

    Args:
        filename: Path to tarball

    Returns:
        Package name (libcuvs or libcuvs_c) or None if not found
    """
    basename = os.path.basename(filename)
    # Remove .tar.gz extension
    name = basename.replace('.tar.gz', '')

    # Check for libcuvs_c first (more specific)
    if re.match(r'^libcuvs_c([_.]|$)', name):
        return 'libcuvs_c'
    elif re.match(r'^libcuvs([_.]|$)', name):
        return 'libcuvs'
    return None


def extract_cuda_version(filename: str) -> Optional[str]:
    """
    Extract CUDA version from filename.

    Patterns:
        libcuvs[_c]_<ver>_<arch>.tar.gz -> <ver>
        libcuvs[_c]_<ver>.tar.gz -> <ver>

    Args:
        filename: Path to tarball

    Returns:
        CUDA version string or None if not found
    """
    basename = os.path.basename(filename)

    # Try pattern 2 first: libcuvs[_c]_<version>.tar.gz (no arch suffix)
    match = re.match(r'^libcuvs(_c)?_([0-9]+(?:\.[0-9]+)*)\.tar\.gz$', basename)
    if match:
        return match.group(2)

    # Try pattern 1: libcuvs[_c]_<version>_<arch>.tar.gz (with arch suffix)
    match = re.match(r'^libcuvs(_c)?_([0-9]+(?:\.[0-9]+)*)_.*\.tar\.gz$', basename)
    if match:
        return match.group(2)

    return None


def detect_architecture(directory: Path) -> str:
    """
    Detect architecture from DSO files in a directory.

    Args:
        directory: Path to directory containing .so files

    Returns:
        'x86_64' or 'sbsa'

    Raises:
        TarballCombinerError: If no .so files found or unknown architecture
    """
    # Find .so files (not symlinks)
    so_files = [f for f in directory.rglob('*.so*') if f.is_file() and not f.is_symlink()]
    if not so_files:
        raise TarballCombinerError(f"No .so files found in {directory}")

    so_file = so_files[0]

    # Use file command to detect architecture
    try:
        result = subprocess.run(
            ['file', str(so_file)],
            capture_output=True,
            text=True,
            check=True
        )
        file_output = result.stdout
    except subprocess.CalledProcessError as e:
        raise TarballCombinerError(f"Failed to run file command: {e}")

    if 'x86-64' in file_output or 'x86_64' in file_output:
        return 'x86_64'
    elif 'ARM aarch64' in file_output or 'aarch64' in file_output:
        return 'sbsa'
    else:
        raise TarballCombinerError(
            f"Unknown architecture in {so_file}: {file_output}"
        )


def extract_version_from_dso(directory: Path) -> str:
    """
    Extract version from DSO files.

    Examples:
        libcuvs_c.so.1.25.12.00 -> 25.12.00
        libcuvs_c.so.2.26.02.02 -> 26.02.02

    Args:
        directory: Path to directory containing .so files

    Returns:
        Version string

    Raises:
        TarballCombinerError: If version cannot be extracted
    """
    # Find DSO files matching pattern libcuvs*.so.*
    so_files = list(directory.rglob('libcuvs*.so.*'))

    for so_file in so_files:
        basename = so_file.name
        # Pattern: libcuvs*.so.[0-9]+.XX.XX.XX
        match = re.search(r'\.so\.[0-9]+\.([0-9]+\.[0-9]+\.[0-9]+)$', basename)
        if match:
            return match.group(1)

    raise TarballCombinerError(
        f"Could not extract version from DSO files in {directory}"
    )


def validate_headers(dir1: Path, dir2: Path, tarball1: str, tarball2: str) -> int:
    """
    Validate that all headers are identical between two directories.

    Args:
        dir1: First directory
        dir2: Second directory
        tarball1: Name of first tarball (for error messages)
        tarball2: Name of second tarball (for error messages)

    Returns:
        Number of differences found
    """
    print("Finding header files...")
    headers1 = sorted(dir1.rglob('*.h'))
    headers2 = sorted(dir2.rglob('*.h'))

    print(f"Found {len(headers1)} headers in {tarball1}")
    print(f"Found {len(headers2)} headers in {tarball2}")
    print()

    print("Validating that all headers are identical...")
    diff_count = 0

    # Check headers in dir1
    for header1 in headers1:
        rel_path = header1.relative_to(dir1)
        header2 = dir2 / rel_path

        if not header2.exists():
            print(f"ERROR: Header {rel_path} exists in tarball1 but not in tarball2")
            diff_count += 1
            continue

        # Compare the files
        if header1.read_bytes() != header2.read_bytes():
            print(f"ERROR DIFFERENCE FOUND: {rel_path}")
            diff_count += 1

    # Check for headers in dir2 that don't exist in dir1
    for header2 in headers2:
        rel_path = header2.relative_to(dir2)
        header1 = dir1 / rel_path

        if not header1.exists():
            print(f"ERROR: Header {rel_path} exists in tarball2 but not in tarball1")
            diff_count += 1

    return diff_count


def copy_tree_contents(src: Path, dst: Path):
    """
    Copy contents of src directory to dst directory.

    Args:
        src: Source directory
        dst: Destination directory
    """
    for item in src.iterdir():
        if item.is_dir():
            shutil.copytree(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)


def find_lib_directory(temp_dir: Path) -> Optional[Path]:
    """
    Find lib64 or lib directory in extracted tarball.

    Args:
        temp_dir: Directory to search

    Returns:
        Path to lib directory or None if not found
    """
    lib64_dir = temp_dir / 'lib64'
    if lib64_dir.exists():
        return lib64_dir

    lib_dir = temp_dir / 'lib'
    if lib_dir.exists():
        return lib_dir

    return None


def combine_tarballs(tarball1: str, tarball2: str) -> str:
    """
    Main function to combine two tarballs.

    Args:
        tarball1: Path to first tarball
        tarball2: Path to second tarball

    Returns:
        Path to output tarball

    Raises:
        TarballCombinerError: If any validation or processing step fails
    """
    # Extract package name from first tarball
    package_name = extract_package_name(tarball1)
    if not package_name:
        raise TarballCombinerError(
            f"Could not extract package name from '{tarball1}'\n"
            "Expected format: libcuvs[_c]_<ver>.tar.gz"
        )
    print(f"Package name: {package_name}")
    print()

    # Extract CUDA versions
    cuda_ver1 = extract_cuda_version(tarball1)
    cuda_ver2 = extract_cuda_version(tarball2)

    print("Detected CUDA versions:")
    print(f"  {tarball1} -> CUDA {cuda_ver1}")
    print(f"  {tarball2} -> CUDA {cuda_ver2}")

    if not cuda_ver1:
        raise TarballCombinerError(
            f"Could not extract CUDA version from '{tarball1}'\n"
            "Expected format: libcuvs_[c_]<ver>_<arch>.tar.gz (e.g., libcuvs_12_amd64.tar.gz)"
        )

    if not cuda_ver2:
        raise TarballCombinerError(
            f"Could not extract CUDA version from '{tarball2}'\n"
            "Expected format: libcuvs_[c_]<ver>_<arch>.tar.gz (e.g., libcuvs_13_amd64.tar.gz)"
        )

    if cuda_ver1 == cuda_ver2:
        raise TarballCombinerError(
            f"Both tarballs have the same CUDA version ({cuda_ver1})\n"
            "Please provide tarballs with different CUDA versions"
        )

    print()

    # Create temporary directories
    temp_dir1 = Path(tempfile.mkdtemp(prefix=f'cuda{cuda_ver1}-'))
    temp_dir2 = Path(tempfile.mkdtemp(prefix=f'cuda{cuda_ver2}-'))
    temp_output = Path(tempfile.mkdtemp(prefix='output-'))

    print("Created temporary directories:")
    print(f"  TEMP_DIR1 (CUDA {cuda_ver1}): {temp_dir1}")
    print(f"  TEMP_DIR2 (CUDA {cuda_ver2}): {temp_dir2}")
    print(f"  TEMP_OUTPUT: {temp_output}")

    try:
        # Extract tarballs
        print(f"Extracting {tarball1} to {temp_dir1}...")
        with tarfile.open(tarball1, 'r:gz') as tar:
            tar.extractall(temp_dir1)

        print(f"Extracting {tarball2} to {temp_dir2}...")
        with tarfile.open(tarball2, 'r:gz') as tar:
            tar.extractall(temp_dir2)

        print("Extraction complete!")
        print()

        # Detect architecture
        print("Detecting architecture...")
        arch = detect_architecture(temp_dir1)
        print(f"Architecture: {arch}")

        # Verify architecture is the same in both tarballs
        arch2 = detect_architecture(temp_dir2)
        if arch != arch2:
            raise TarballCombinerError(
                f"Architecture mismatch between tarballs: {arch} vs {arch2}"
            )

        # Extract version from DSO files
        print("Extracting version from DSO files...")
        version = extract_version_from_dso(temp_dir1)
        print(f"Version: {version}")

        # Verify version is the same in both tarballs
        version2 = extract_version_from_dso(temp_dir2)
        if version != version2:
            raise TarballCombinerError(
                f"Version mismatch between tarballs: {version} vs {version2}"
            )

        # Generate output filename
        os_name = "linux"
        output_tarball = f"{package_name}-{os_name}-{arch}-{version}.tar.gz"
        print(f"Output tarball will be: {output_tarball}")
        print()

        # Validate headers
        diff_count = validate_headers(temp_dir1, temp_dir2, tarball1, tarball2)

        print()
        if diff_count == 0:
            print("✓ SUCCESS: All headers are identical!")
        else:
            raise TarballCombinerError(f"Found {diff_count} differences in headers")

        print("Combining tarballs:")
        print(f"  CUDA {cuda_ver1}: {tarball1}")
        print(f"  CUDA {cuda_ver2}: {tarball2}")

        # Create output directories
        output_lib_dir = temp_output / 'cuvs' / 'lib64'
        output_lib_dir.mkdir(parents=True)
        (temp_output / 'include').mkdir()

        # Copy lib64 from first tarball
        lib_dir1 = find_lib_directory(temp_dir1)
        if not lib_dir1:
            raise TarballCombinerError(
                f"No lib64 or lib directory found in CUDA {cuda_ver1} tarball"
            )

        cuda_lib_dir1 = output_lib_dir / cuda_ver1
        cuda_lib_dir1.mkdir()
        print(f"Copying CUDA {cuda_ver1} lib64...")
        copy_tree_contents(lib_dir1, cuda_lib_dir1)

        # Copy lib64 from second tarball
        lib_dir2 = find_lib_directory(temp_dir2)
        if not lib_dir2:
            raise TarballCombinerError(
                f"No lib64 or lib directory found in CUDA {cuda_ver2} tarball"
            )

        cuda_lib_dir2 = output_lib_dir / cuda_ver2
        cuda_lib_dir2.mkdir()
        print(f"Copying CUDA {cuda_ver2} lib64...")
        copy_tree_contents(lib_dir2, cuda_lib_dir2)

        # Copy include from second tarball (headers should be identical)
        include_dir2 = temp_dir2 / 'include'
        if not include_dir2.exists():
            raise TarballCombinerError(
                f"No include directory found in CUDA {cuda_ver2} tarball"
            )

        print(f"Copying include directory from CUDA {cuda_ver2}...")
        copy_tree_contents(include_dir2, temp_output / 'include')

        # Copy LICENSE files from second tarball
        license_file = temp_dir2 / 'LICENSE'
        license_txt = temp_dir2 / 'LICENSE.txt'

        if license_file.exists():
            print(f"Copying LICENSE files from CUDA {cuda_ver2}...")
            shutil.copy2(license_file, temp_output / 'LICENSE.txt')
        elif license_txt.exists():
            print(f"Copying LICENSE files from CUDA {cuda_ver2}...")
            shutil.copy2(license_txt, temp_output / 'LICENSE.txt')
        else:
            backup_license = Path('/home/rmaynard/Work/cuvs/LICENSE')
            if backup_license.exists():
                print("Copying backup LICENSE file")
                shutil.copy2(backup_license, temp_output / 'LICENSE.txt')

        # Create the combined tarball
        print(f"Creating combined tarball: {output_tarball}")
        with tarfile.open(output_tarball, 'w:gz') as tar:
            for item in temp_output.iterdir():
                tar.add(item, arcname=item.name)

        # Show the structure
        print()
        print("Combined tarball structure:")
        with tarfile.open(output_tarball, 'r:gz') as tar:
            for member in tar.getmembers():
                if not member.isdir():
                    print(member.name)

        print(f"✓ SUCCESS: Created combined tarball: {output_tarball}")
        print(f"  Package: {package_name}")
        print(f"  OS: {os_name}")
        print(f"  Architecture: {arch}")
        print(f"  Version: {version}")
        print(f"  CUDA versions: {cuda_ver1}, {cuda_ver2}")

        return output_tarball

    finally:
        # Cleanup temporary directories
        print("Cleaning up temporary directories...")
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)
        shutil.rmtree(temp_output, ignore_errors=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate and combine two CUDA version tarballs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s libcuvs_12_amd64.tar.gz libcuvs_13_amd64.tar.gz

Tarball naming pattern: libcuvs[_c]_<ver>[_<arch>].tar.gz
  where <ver> is the CUDA version (e.g., 12, 13)
  and <arch> is the architecture (e.g., amd64, arm64)

Output filename will be auto-generated as: <package>-linux-<arch>-<version>.tar.gz
        """
    )

    parser.add_argument('tarball1', help='First tarball (CUDA version 1)')
    parser.add_argument('tarball2', help='Second tarball (CUDA version 2)')

    args = parser.parse_args()

    # Validate that both tarballs exist
    if not os.path.isfile(args.tarball1):
        print(f"Error: Tarball '{args.tarball1}' not found", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.tarball2):
        print(f"Error: Tarball '{args.tarball2}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        combine_tarballs(args.tarball1, args.tarball2)
    except TarballCombinerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

