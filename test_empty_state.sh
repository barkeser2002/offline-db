find frontend/src -type f -name "*.tsx" -exec awk '
/length === 0/ || /length == 0/ || /!.*length/ {
    print FILENAME ":" $0;
}' {} +
