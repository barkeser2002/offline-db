find frontend/src -type f -name "*.tsx" -exec awk '
/isIconOnly/ {
    line=$0;
    file=FILENAME;
    if (line !~ /aria-label/ && line !~ /title/ && line !~ /\/\//) {
        print file ":" line;
    }
}' {} +
