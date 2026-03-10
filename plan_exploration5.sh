find frontend/src -type f -name "*.tsx" -exec awk '
/Input/ {
    found=1;
    line=$0;
    file=FILENAME;
    while (found && !/>/) {
        getline;
        line = line " " $0;
    }
    if (line !~ /aria-label/ && line !~ /label=/ && line !~ /id=/ && line !~ /import/ && line !~ /\/\//) {
        print file ":" line;
    }
}' {} +
