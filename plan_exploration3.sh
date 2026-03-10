find frontend/src -type f -name "*.tsx" -exec awk '
/type="email"/ || /type="password"/ || /type="text"/ || /type="search"/ {
    print FILENAME ":" $0;
}' {} +
