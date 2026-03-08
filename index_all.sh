#!/bin/bash
# Batch-index all precedent PDFs and Markdown files in the precedents/ directory.
# Usage: ./index_all.sh
# Optional: override model and directories via env vars:
#   MODEL=Qwen/Qwen3.5-35B-A3B PRECEDENTS_DIR=./my_docs ./index_all.sh

MODEL="${MODEL:-Qwen/Qwen3.5-35B-A3B}"
PRECEDENTS_DIR="${PRECEDENTS_DIR:-./precedents}"

echo "====================================="
echo "PageIndex Batch Indexer"
echo "Model:          $MODEL"
echo "Precedents dir: $PRECEDENTS_DIR"
echo "====================================="

# Check precedents directory exists
if [ ! -d "$PRECEDENTS_DIR" ]; then
    echo "Error: Directory '$PRECEDENTS_DIR' not found."
    echo "Create it and add your precedent files first."
    exit 1
fi

# Count files
PDF_COUNT=$(find "$PRECEDENTS_DIR" -maxdepth 1 -name "*.pdf" | wc -l)
MD_COUNT=$(find "$PRECEDENTS_DIR" -maxdepth 1 \( -name "*.md" -o -name "*.markdown" \) | wc -l)
TOTAL=$((PDF_COUNT + MD_COUNT))

if [ "$TOTAL" -eq 0 ]; then
    echo "No PDF or Markdown files found in '$PRECEDENTS_DIR'. Exiting."
    exit 1
fi

echo "Found $PDF_COUNT PDF(s) and $MD_COUNT Markdown file(s) to index."
echo ""

INDEXED=0
FAILED=0
COUNTER=0

# Index PDFs
for pdf in "$PRECEDENTS_DIR"/*.pdf; do
    [ -f "$pdf" ] || continue
    COUNTER=$((COUNTER + 1))
    echo "[$COUNTER/$TOTAL] [PDF] Indexing: $(basename "$pdf")"

    if python3 run_pageindex.py --pdf_path "$pdf" --model "$MODEL"; then
        echo "  ✓ Done"
        INDEXED=$((INDEXED + 1))
    else
        echo "  ✗ Failed"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# Index Markdown files
for md in "$PRECEDENTS_DIR"/*.md "$PRECEDENTS_DIR"/*.markdown; do
    [ -f "$md" ] || continue
    COUNTER=$((COUNTER + 1))
    echo "[$COUNTER/$TOTAL] [MD] Indexing: $(basename "$md")"

    if python3 run_pageindex.py --md_path "$md" --model "$MODEL"; then
        echo "  ✓ Done"
        INDEXED=$((INDEXED + 1))
    else
        echo "  ✗ Failed"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "====================================="
echo "Indexing complete."
echo "  Succeeded: $INDEXED"
echo "  Failed:    $FAILED"
echo "  Results:   ./results/"
echo "====================================="
