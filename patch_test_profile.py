with open('/home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/rest_framework/urlpatterns.py', 'r') as f:
    content = f.read()

content = content.replace("register_converter(suffix_converter, converter_name)", "try:\n        register_converter(suffix_converter, converter_name)\n    except ValueError:\n        pass")

with open('/home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/rest_framework/urlpatterns.py', 'w') as f:
    f.write(content)
