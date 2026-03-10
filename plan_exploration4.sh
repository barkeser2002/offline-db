find frontend/src -type f -name "*.tsx" -exec awk '
/<input/ {
    line=$0;
    file=FILENAME;
    if (line !~ /aria-label/) {
        print file ":" line;
    }
}' {} +
