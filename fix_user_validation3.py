import os
for root, _, files in os.walk('users/migrations'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            if 'django.core.validators.RegexValidator' in content and 'import django' not in content:
                content = 'import django.core.validators\n' + content
                with open(path, 'w') as f:
                    f.write(content)
