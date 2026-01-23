"""
Storage Gateway Module

Provides a unified interface for multiple storage backends including:
- Amazon S3 (and compatible services)
- FTP
- SFTP (SSH File Transfer Protocol)
- WebDAV

Configuration is done via environment variables in .env file.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class StorageManager(ABC):
    """
    Abstract base class for storage backends.
    All storage implementations must inherit from this class.
    """
    
    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> str:
        """
        Upload a file to the storage backend.
        
        Args:
            local_path: Path to the local file
            remote_path: Destination path on the remote storage
            
        Returns:
            The URL or path to access the uploaded file
        """
        pass
    
    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """
        Delete a file from the storage backend.
        
        Args:
            remote_path: Path to the file on remote storage
            
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """
        Generate a streaming URL for the file.
        
        Args:
            remote_path: Path to the file on remote storage
            expires_in: URL expiration time in seconds (for signed URLs)
            
        Returns:
            URL to stream/access the file
        """
        pass
    
    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """Check if a file exists on the storage backend."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the storage backend is accessible.
        
        Returns:
            True if the storage is healthy
        """
        pass


class S3Storage(StorageManager):
    """
    Amazon S3 (and S3-compatible) storage backend.
    
    Required environment variables:
        - S3_ACCESS_KEY_ID
        - S3_SECRET_ACCESS_KEY
        - S3_BUCKET_NAME
        - S3_ENDPOINT_URL (optional, for S3-compatible services)
        - S3_REGION (optional, defaults to 'us-east-1')
    """
    
    def __init__(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        endpoint_url = os.getenv('S3_ENDPOINT_URL')
        region = os.getenv('S3_REGION', 'us-east-1')
        
        config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
            endpoint_url=endpoint_url,
            region_name=region,
            config=config
        )
        
        self.resource = boto3.resource(
            's3',
            aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
            endpoint_url=endpoint_url,
            region_name=region,
        )
        
        self.cdn_url = os.getenv('S3_CDN_URL', '')
        
        # Auto-configure CORS for WebGL (Anime4K) support
        if os.getenv('S3_AUTO_CORS', 'False') == 'True':
            self.setup_cors()

    def setup_cors(self):
        """
        Configures CORS for the S3 bucket to allow all origins (required for WebGL/Anime4K).
        """
        try:
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }]
            }
            self.client.put_bucket_cors(Bucket=self.bucket_name, CORSConfiguration=cors_configuration)
            logger.info(f"S3: CORS configured for bucket {self.bucket_name}")
        except Exception as e:
            logger.warning(f"S3: Failed to configure CORS: {e}")
    
    def upload(self, local_path: str, remote_path: str) -> str:
        try:
            self.client.upload_file(local_path, self.bucket_name, remote_path)
            logger.info(f"S3: Uploaded {local_path} to {remote_path}")
            return self.get_stream_url(remote_path)
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise StorageError(f"S3 upload failed: {e}")
    
    def delete(self, remote_path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=remote_path)
            logger.info(f"S3: Deleted {remote_path}")
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        if self.cdn_url:
            return urljoin(self.cdn_url, remote_path)
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': remote_path},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"S3 presigned URL generation failed: {e}")
            raise StorageError(f"Failed to generate stream URL: {e}")
    
    def exists(self, remote_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except:
            return False
    
    def health_check(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except:
            return False


class FTPStorage(StorageManager):
    """
    FTP storage backend.
    
    Required environment variables:
        - FTP_HOST
        - FTP_USER
        - FTP_PASSWORD
        - FTP_PORT (optional, defaults to 21)
        - FTP_BASE_URL (URL prefix for accessing files)
    """
    
    def __init__(self):
        import ftplib
        
        self.host = os.getenv('FTP_HOST')
        self.user = os.getenv('FTP_USER')
        self.password = os.getenv('FTP_PASSWORD')
        self.port = int(os.getenv('FTP_PORT', 21))
        self.base_url = os.getenv('FTP_BASE_URL', '')
    
    def _get_connection(self):
        import ftplib
        ftp = ftplib.FTP()
        ftp.connect(self.host, self.port)
        ftp.login(self.user, self.password)
        return ftp
    
    def _ensure_directory(self, ftp, path: str):
        """Create directory tree if it doesn't exist"""
        dirs = path.rsplit('/', 1)[0].split('/')
        current = ''
        for d in dirs:
            if d:
                current += f'/{d}'
                try:
                    ftp.mkd(current)
                except:
                    pass  # Directory might already exist
    
    def upload(self, local_path: str, remote_path: str) -> str:
        try:
            ftp = self._get_connection()
            self._ensure_directory(ftp, remote_path)
            
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_path}', f)
            
            ftp.quit()
            logger.info(f"FTP: Uploaded {local_path} to {remote_path}")
            return self.get_stream_url(remote_path)
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            raise StorageError(f"FTP upload failed: {e}")
    
    def delete(self, remote_path: str) -> bool:
        try:
            ftp = self._get_connection()
            ftp.delete(remote_path)
            ftp.quit()
            logger.info(f"FTP: Deleted {remote_path}")
            return True
        except Exception as e:
            logger.error(f"FTP delete failed: {e}")
            return False
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        return urljoin(self.base_url, remote_path)
    
    def exists(self, remote_path: str) -> bool:
        try:
            ftp = self._get_connection()
            ftp.size(remote_path)
            ftp.quit()
            return True
        except:
            return False
    
    def health_check(self) -> bool:
        try:
            ftp = self._get_connection()
            ftp.quit()
            return True
        except:
            return False


class SFTPStorage(StorageManager):
    """
    SFTP (SSH File Transfer Protocol) storage backend.
    
    Required environment variables:
        - SFTP_HOST
        - SFTP_USER
        - SFTP_PASSWORD or SFTP_KEY_FILE
        - SFTP_PORT (optional, defaults to 22)
        - SFTP_BASE_URL (URL prefix for accessing files)
    """
    
    def __init__(self):
        try:
            import paramiko
        except ImportError:
            raise ImportError("paramiko is required for SFTP storage. Install with: pip install paramiko")
        
        self.host = os.getenv('SFTP_HOST')
        self.user = os.getenv('SFTP_USER')
        self.password = os.getenv('SFTP_PASSWORD')
        self.key_file = os.getenv('SFTP_KEY_FILE')
        self.port = int(os.getenv('SFTP_PORT', 22))
        self.base_url = os.getenv('SFTP_BASE_URL', '')
    
    def _get_connection(self):
        import paramiko
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.key_file:
            key = paramiko.RSAKey.from_private_key_file(self.key_file)
            ssh.connect(self.host, port=self.port, username=self.user, pkey=key)
        else:
            ssh.connect(self.host, port=self.port, username=self.user, password=self.password)
        
        return ssh, ssh.open_sftp()
    
    def _ensure_directory(self, sftp, path: str):
        """Create directory tree if it doesn't exist"""
        dirs = path.rsplit('/', 1)[0].split('/')
        current = ''
        for d in dirs:
            if d:
                current += f'/{d}'
                try:
                    sftp.mkdir(current)
                except:
                    pass  # Directory might already exist
    
    def upload(self, local_path: str, remote_path: str) -> str:
        try:
            ssh, sftp = self._get_connection()
            self._ensure_directory(sftp, remote_path)
            sftp.put(local_path, remote_path)
            sftp.close()
            ssh.close()
            logger.info(f"SFTP: Uploaded {local_path} to {remote_path}")
            return self.get_stream_url(remote_path)
        except Exception as e:
            logger.error(f"SFTP upload failed: {e}")
            raise StorageError(f"SFTP upload failed: {e}")
    
    def delete(self, remote_path: str) -> bool:
        try:
            ssh, sftp = self._get_connection()
            sftp.remove(remote_path)
            sftp.close()
            ssh.close()
            logger.info(f"SFTP: Deleted {remote_path}")
            return True
        except Exception as e:
            logger.error(f"SFTP delete failed: {e}")
            return False
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        return urljoin(self.base_url, remote_path)
    
    def exists(self, remote_path: str) -> bool:
        try:
            ssh, sftp = self._get_connection()
            sftp.stat(remote_path)
            sftp.close()
            ssh.close()
            return True
        except:
            return False
    
    def health_check(self) -> bool:
        try:
            ssh, sftp = self._get_connection()
            sftp.close()
            ssh.close()
            return True
        except:
            return False


class WebDAVStorage(StorageManager):
    """
    WebDAV storage backend.
    
    Required environment variables:
        - WEBDAV_URL (base URL of WebDAV server)
        - WEBDAV_USER
        - WEBDAV_PASSWORD
        - WEBDAV_BASE_URL (optional, URL prefix for accessing files)
    """
    
    def __init__(self):
        try:
            from webdav3.client import Client
        except ImportError:
            raise ImportError("webdavclient3 is required for WebDAV storage. Install with: pip install webdavclient3")
        
        options = {
            'webdav_hostname': os.getenv('WEBDAV_URL'),
            'webdav_login': os.getenv('WEBDAV_USER'),
            'webdav_password': os.getenv('WEBDAV_PASSWORD'),
        }
        
        self.client = Client(options)
        self.base_url = os.getenv('WEBDAV_BASE_URL', os.getenv('WEBDAV_URL', ''))
    
    def upload(self, local_path: str, remote_path: str) -> str:
        try:
            # Ensure directory exists
            dir_path = remote_path.rsplit('/', 1)[0]
            if dir_path:
                self.client.mkdir(dir_path)
            
            self.client.upload_sync(remote_path=remote_path, local_path=local_path)
            logger.info(f"WebDAV: Uploaded {local_path} to {remote_path}")
            return self.get_stream_url(remote_path)
        except Exception as e:
            logger.error(f"WebDAV upload failed: {e}")
            raise StorageError(f"WebDAV upload failed: {e}")
    
    def delete(self, remote_path: str) -> bool:
        try:
            self.client.clean(remote_path)
            logger.info(f"WebDAV: Deleted {remote_path}")
            return True
        except Exception as e:
            logger.error(f"WebDAV delete failed: {e}")
            return False
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        return urljoin(self.base_url, remote_path)
    
    def exists(self, remote_path: str) -> bool:
        try:
            return self.client.check(remote_path)
        except:
            return False
    
    def health_check(self) -> bool:
        try:
            self.client.list()
            return True
        except:
            return False


class LocalStorage(StorageManager):
    """
    Local filesystem storage backend (for development).
    
    Uses Django's MEDIA_ROOT for storage.
    """
    
    def __init__(self):
        self.base_path = settings.MEDIA_ROOT
        self.base_url = settings.MEDIA_URL
    
    def upload(self, local_path: str, remote_path: str) -> str:
        import shutil
        
        dest_path = os.path.join(self.base_path, remote_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(local_path, dest_path)
        logger.info(f"Local: Copied {local_path} to {dest_path}")
        return self.get_stream_url(remote_path)
    
    def delete(self, remote_path: str) -> bool:
        try:
            full_path = os.path.join(self.base_path, remote_path)
            os.remove(full_path)
            logger.info(f"Local: Deleted {full_path}")
            return True
        except Exception as e:
            logger.error(f"Local delete failed: {e}")
            return False
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        return urljoin(self.base_url, remote_path)
    
    def exists(self, remote_path: str) -> bool:
        return os.path.exists(os.path.join(self.base_path, remote_path))
    
    def health_check(self) -> bool:
        return os.path.exists(self.base_path) and os.access(self.base_path, os.W_OK)


# Storage type mapping
STORAGE_BACKENDS = {
    's3': S3Storage,
    'ftp': FTPStorage,
    'sftp': SFTPStorage,
    'webdav': WebDAVStorage,
    'local': LocalStorage,
}


class StorageGateway:
    """
    Unified storage gateway with failover support.
    
    Configuration via environment variables:
        - STORAGE_TYPE: Primary storage type (s3, ftp, sftp, webdav, local)
        - BACKUP_STORAGE_TYPE: Backup storage type (optional)
    
    Usage:
        gateway = StorageGateway()
        url = gateway.upload('/path/to/file.mp4', 'videos/episode_1.mp4')
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        primary_type = os.getenv('STORAGE_TYPE', 'local').lower()
        backup_type = os.getenv('BACKUP_STORAGE_TYPE', '').lower()
        
        if primary_type not in STORAGE_BACKENDS:
            raise ValueError(f"Unknown storage type: {primary_type}")
        
        self.primary: StorageManager = STORAGE_BACKENDS[primary_type]()
        self.backup: Optional[StorageManager] = None
        
        if backup_type and backup_type in STORAGE_BACKENDS:
            try:
                self.backup = STORAGE_BACKENDS[backup_type]()
                logger.info(f"Backup storage configured: {backup_type}")
            except Exception as e:
                logger.warning(f"Failed to initialize backup storage: {e}")
        
        self._initialized = True
        logger.info(f"Storage Gateway initialized with primary: {primary_type}")
    
    def upload(self, local_path: str, remote_path: str) -> str:
        """Upload file with automatic failover to backup storage"""
        try:
            return self.primary.upload(local_path, remote_path)
        except StorageError as e:
            if self.backup:
                logger.warning(f"Primary storage failed, trying backup: {e}")
                return self.backup.upload(local_path, remote_path)
            raise
    
    def delete(self, remote_path: str) -> bool:
        """Delete file from primary storage"""
        return self.primary.delete(remote_path)
    
    def get_stream_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Get streaming URL with failover"""
        try:
            if self.primary.exists(remote_path):
                return self.primary.get_stream_url(remote_path, expires_in)
        except:
            pass
        
        if self.backup and self.backup.exists(remote_path):
            return self.backup.get_stream_url(remote_path, expires_in)
        
        # Default to primary
        return self.primary.get_stream_url(remote_path, expires_in)
    
    def health_check(self) -> dict:
        """Check health of all storage backends"""
        return {
            'primary': self.primary.health_check(),
            'backup': self.backup.health_check() if self.backup else None,
        }


# Singleton instance
def get_storage() -> StorageGateway:
    """Get the storage gateway singleton"""
    return StorageGateway()
