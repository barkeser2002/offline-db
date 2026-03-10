# Search for native HTML button elements in Next.js frontend missing aria-label or focus-visible:ring-2
find frontend/src -type f -name "*.tsx" -exec awk '
/<button/ {
    found=1;
    line=$0;
    file=FILENAME;
    while (found && !/>/) {
        getline;
        line = line " " $0;
    }
    if (line !~ /aria-label/ || line !~ /focus-visible:ring-2/) {
        print file ":" line;
    }
}' {} +
