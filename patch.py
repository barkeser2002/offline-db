import os
import sys

def patch():
    filepath = "core/storage.py"
    with open(filepath, "r") as f:
        content = f.read()

    # We want to make sure self.base_path ends with os.path.sep in __init__

    old_init = """    def __init__(self):
        self.base_path = os.path.abspath(settings.MEDIA_ROOT)
        self.base_url = settings.MEDIA_URL"""

    new_init = """    def __init__(self):
        self.base_path = os.path.abspath(settings.MEDIA_ROOT)
        if not self.base_path.endswith(os.path.sep):
            self.base_path += os.path.sep
        self.base_url = settings.MEDIA_URL"""

    content = content.replace(old_init, new_init)

    with open(filepath, "w") as f:
        f.write(content)

if __name__ == "__main__":
    patch()
