#!/usr/bin/bash
set -e


# Check if three arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <tarball1> <tarball2> <output_tarball>"
    echo "Example: $0 libcuvs_12_amd64.tar.gz libcuvs_13_amd64.tar.gz libcuvs_combined.tar.gz"
    echo ""
    echo "Tarball naming pattern: libcuvs_<ver>_<arch>.tar.gz"
    echo "  where <ver> is the CUDA version (e.g., 12, 13)"
    echo "  and <arch> is the architecture (e.g., amd64, arm64)"
    exit 1
fi

TARBALL1="$1"
TARBALL2="$2"
OUTPUT_TARBALL="$3"

# Validate that both tarballs exist
if [ ! -f "$TARBALL1" ]; then
    echo "Error: Tarball '$TARBALL1' not found"
    exit 1
fi

if [ ! -f "$TARBALL2" ]; then
    echo "Error: Tarball '$TARBALL2' not found"
    exit 1
fi

# Extract CUDA versions from filenames
# Pattern 1: libcuvs[_c]_<ver>_<arch>.tar.gz (e.g., libcuvs_12_amd64.tar.gz -> 12, libcuvs_c_12_amd64.tar.gz -> 12)
# Pattern 2: libcuvs[_c]_<ver>.tar.gz (e.g., libcuvs_c_13.0.1.tar.gz -> 13.0.1, libcuvs_13.0.1.tar.gz -> 13.0.1)
extract_cuda_version() {
    local filename=$(basename "$1")
    # Try pattern 2 first: libcuvs[_c]_<version>.tar.gz (no arch suffix)
    local version=$(echo "$filename" | sed -n -E 's/^libcuvs(_c)?_([0-9]+(\.[0-9]+)*)\.tar\.gz$/\2/p')
    if [ -n "$version" ]; then
        echo "$version"
        return
    fi
    # Try pattern 1: libcuvs[_c]_<version>_<arch>.tar.gz (with arch suffix)
    version=$(echo "$filename" | sed -n -E 's/^libcuvs(_c)?_([0-9]+(\.[0-9]+)*)_.*\.tar\.gz$/\2/p')
    echo "$version"
}

CUDA_VER1=$(extract_cuda_version "$TARBALL1")
CUDA_VER2=$(extract_cuda_version "$TARBALL2")

echo "Detected CUDA versions:"
echo "  $TARBALL1 -> CUDA $CUDA_VER1"
echo "  $TARBALL2 -> CUDA $CUDA_VER2"

# Validate that versions were extracted
if [ -z "$CUDA_VER1" ]; then
    echo "Error: Could not extract CUDA version from '$TARBALL1'"
    echo "Expected format: libcuvs_[c_]<ver>_<arch>.tar.gz (e.g., libcuvs_12_amd64.tar.gz)"
    exit 1
fi

if [ -z "$CUDA_VER2" ]; then
    echo "Error: Could not extract CUDA version from '$TARBALL2'"
    echo "Expected format: libcuvs_[c_]<ver>_<arch>.tar.gz (e.g., libcuvs_13_amd64.tar.gz)"
    exit 1
fi

# Validate that versions are different
if [ "$CUDA_VER1" == "$CUDA_VER2" ]; then
    echo "Error: Both tarballs have the same CUDA version ($CUDA_VER1)"
    echo "Please provide tarballs with different CUDA versions"
    exit 1
fi

echo ""

# Create temporary directories
TEMP_DIR1=$(mktemp -d -t cuda${CUDA_VER1}-XXXXXXXXXX)
TEMP_DIR2=$(mktemp -d -t cuda${CUDA_VER2}-XXXXXXXXXX)
TEMP_OUTPUT=$(mktemp -d -t output-XXXXXXXXXX)

echo "Created temporary directories:"
echo "  TEMP_DIR1 (CUDA $CUDA_VER1): $TEMP_DIR1"
echo "  TEMP_DIR2 (CUDA $CUDA_VER2): $TEMP_DIR2"
echo "  TEMP_OUTPUT: $TEMP_OUTPUT"

# Cleanup function to remove temp directories on exit
cleanup() {
    echo "Cleaning up temporary directories..."
    rm -rf "$TEMP_DIR1" "$TEMP_DIR2" "$TEMP_OUTPUT"
}
trap cleanup EXIT

# Extract first tarball
echo "Extracting $TARBALL1 to $TEMP_DIR1..."
tar -xzf "$TARBALL1" -C "$TEMP_DIR1"

# Extract second tarball
echo "Extracting $TARBALL2 to $TEMP_DIR2..."
tar -xzf "$TARBALL2" -C "$TEMP_DIR2"


echo "Extraction complete!"
echo ""

# Find all header files in both directories
echo "Finding header files..."
HEADERS1=($(find "$TEMP_DIR1" -name "*.h" | sort))
HEADERS2=($(find "$TEMP_DIR2" -name "*.h" | sort))

echo "Found ${#HEADERS1[@]} headers in $TARBALL1"
echo "Found ${#HEADERS2[@]} headers in $TARBALL2"
echo ""

# Validate that headers are the same
echo "Validating that all headers are identical..."
DIFF_COUNT=0

for header1 in "${HEADERS1[@]}"; do
    # Get relative path
    rel_path="${header1#$TEMP_DIR1/}"
    header2="$TEMP_DIR2/$rel_path"

    if [ ! -f "$header2" ]; then
        echo "ERROR: Header $rel_path exists in tarball1 but not in tarball2"
        DIFF_COUNT=$((DIFF_COUNT + 1))
        continue
    fi

    # Compare the files
    if ! diff -q "$header1" "$header2" > /dev/null; then
        echo "ERROR DIFFERENCE FOUND: $rel_path"
        DIFF_COUNT=$((DIFF_COUNT + 1))
    fi
done

# Check for headers in tarball2 that don't exist in tarball1
for header2 in "${HEADERS2[@]}"; do
    rel_path="${header2#$TEMP_DIR2/}"
    header1="$TEMP_DIR1/$rel_path"

    if [ ! -f "$header1" ]; then
        echo "ERROR: Header $rel_path exists in tarball2 but not in tarball1"
        DIFF_COUNT=$((DIFF_COUNT + 1))
    fi
done

echo ""
if [ $DIFF_COUNT -eq 0 ]; then
    echo "✓ SUCCESS: All headers are identical!"
else
    echo "✗ FAILURE: Found $DIFF_COUNT differences in headers"
    exit 1
fi

echo "Combining tarballs:"
echo "  CUDA $CUDA_VER1: $TARBALL1"
echo "  CUDA $CUDA_VER2: $TARBALL2"

# Create output directories
mkdir -p "$TEMP_OUTPUT/cuvs/lib64/"
mkdir -p "$TEMP_OUTPUT/include"

# Copy lib64 from first tarball
mkdir -p "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER1"
if [ -d "$TEMP_DIR1/lib64" ]; then
    echo "Copying CUDA $CUDA_VER1 lib64..."
    cp -r "$TEMP_DIR1/lib64/"* "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER1/"
elif [ -d "$TEMP_DIR1/lib" ]; then
    echo "Copying CUDA $CUDA_VER1 lib (not lib64)..."
    cp -r "$TEMP_DIR1/lib/"* "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER1/"
else
    echo "✗ FAILURE: No lib64 or lib directory found in CUDA $CUDA_VER1 tarball"
    exit 1
fi

# Copy lib64 from second tarball
mkdir -p "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER2"
if [ -d "$TEMP_DIR2/lib64" ]; then
    echo "Copying CUDA $CUDA_VER2 lib64..."
    cp -r "$TEMP_DIR2/lib64/"* "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER2/"
elif [ -d "$TEMP_DIR2/lib" ]; then
    echo "Copying CUDA $CUDA_VER2 lib (not lib64)..."
    cp -r "$TEMP_DIR2/lib/"* "$TEMP_OUTPUT/cuvs/lib64/$CUDA_VER2/"
else
    echo "✗ FAILURE: No lib64 or lib directory found in CUDA $CUDA_VER2 tarball"
    exit 1
fi

# Copy include from second tarball (headers should be identical between versions)
if [ -d "$TEMP_DIR2/include" ]; then
    echo "Copying include directory from CUDA $CUDA_VER2..."
    cp -r "$TEMP_DIR2/include/"* "$TEMP_OUTPUT/include/"
else
    echo "✗ FAILURE: No include directory found in CUDA $CUDA_VER2 tarball"
    exit 1
fi

# Copy License files from second tarball
if [ -e "$TEMP_DIR2/LICENSE" ]; then
    echo "Copying LICENSE files from CUDA $CUDA_VER2..."
    cp -r "$TEMP_DIR2/LICENSE" "$TEMP_OUTPUT/LICENSE.txt"
elif [ -e "$TEMP_DIR2/LICENSE.txt" ]; then
    echo "Copying LICENSE files from CUDA $CUDA_VER2..."
    cp -r "$TEMP_DIR2/LICENSE.txt" "$TEMP_OUTPUT/LICENSE.txt"
else
    echo "Copying backup LICENSE file"
    cp -r "/home/rmaynard/Work/cuvs/LICENSE" "$TEMP_OUTPUT/LICENSE.txt"
fi


# Create the combined tarball
echo "Creating combined tarball: $OUTPUT_TARBALL"
tar czf "$OUTPUT_TARBALL" -C "$TEMP_OUTPUT" .

# Show the structure
echo ""
echo "Combined tarball structure:"
tar tf "$OUTPUT_TARBALL" | grep -v '/$'

echo "✓ SUCCESS: Created combined tarball with CUDA $CUDA_VER1 and CUDA $CUDA_VER2: $OUTPUT_TARBALL"


