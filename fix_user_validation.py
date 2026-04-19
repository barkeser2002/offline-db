import os
for root, _, files in os.walk('users/migrations'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            if 'users.models.UsernameValidator' in content:
                content = content.replace('users.models.UsernameValidator', 'django.contrib.auth.validators.UnicodeUsernameValidator')
                with open(path, 'w') as f:
                    f.write(content)
