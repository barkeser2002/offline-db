import pytest
from core.storage import LocalStorage, StorageError
import os

def test_path_traversal():
    storage = LocalStorage()
    try:
        storage.upload('dummy.txt', '../../../../etc/passwd')
        print("Vulnerable to upload path traversal!")
    except Exception as e:
        print("Upload error:", type(e))

    try:
        storage.delete('../../../../etc/passwd')
        print("Vulnerable to delete path traversal!")
    except Exception as e:
        print("Delete error:", type(e))

test_path_traversal()
