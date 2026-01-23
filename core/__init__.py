import pymysql
from aniscrap_core.celery import app as celery_app

# Monkeypatch version to satisfy Django
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()

# Safe import wrapper for optional cryptographic libraries
try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad
except ImportError:
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad
    except ImportError:
        import warnings
        warnings.warn(
            "pycryptodome (or pycrypto) is not installed; cryptographic helpers will be unavailable.",
            RuntimeWarning,
        )
        AES = None
        pad = unpad = None

__all__ = ('celery_app',)
