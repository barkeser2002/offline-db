import re

with open('users/views.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    '''    def patch(self, request):
        user = request.user
        data = request.data

        # We will handle validation in step 3.
        # This will be refined.
        if 'bio' in data:
            user.bio = data['bio']

        if 'username' in data:
            user.username = data['username']

        user.save()
        return Response({'status': 'success'})''',
    '''    def patch(self, request):
        import bleach
        import re
        from django.db import IntegrityError

        user = request.user
        data = request.data

        if 'bio' in data:
            bio_text = data['bio']
            # Sanitize HTML input using bleach
            user.bio = bleach.clean(bio_text, tags=[], strip=True)

        if 'username' in data:
            username = data['username']
            # Only allow alphanumeric + _-
            if not re.match(r'^[a-zA-Z0-9_-]+$', username):
                return Response(
                    {"error": "Username can only contain alphanumeric characters, underscores, and hyphens."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.username = username

        try:
            user.save()
            return Response({'status': 'success'})
        except IntegrityError:
            return Response(
                {"error": "Username is already taken."},
                status=status.HTTP_400_BAD_REQUEST
            )'''
)

with open('users/views.py', 'w') as f:
    f.write(new_content)
