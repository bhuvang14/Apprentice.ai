import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, path: str, file_obj: BinaryIO) -> str:
        pass
    
    @abstractmethod
    def get(self, path: str) -> BinaryIO:
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        pass


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_BASE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _full_path(self, path: str) -> Path:
        return self.base_path / path
    
    def save(self, path: str, file_obj: BinaryIO) -> str:
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file_obj, f)
        return path
    
    def get(self, path: str) -> BinaryIO:
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return open(full_path, "rb")
    
    def delete(self, path: str) -> bool:
        full_path = self._full_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()
    
    def get_url(self, path: str) -> str:
        return f"/api/files/{path}"


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, region: str = "us-east-1"):
        try:
            import boto3
            self.s3 = boto3.client("s3", region_name=region)
            self.bucket = bucket
        except ImportError:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")
    
    def save(self, path: str, file_obj: BinaryIO) -> str:
        self.s3.upload_fileobj(file_obj, self.bucket, path)
        return path
    
    def get(self, path: str) -> BinaryIO:
        import io
        obj = self.s3.get_object(Bucket=self.bucket, Key=path)
        return io.BytesIO(obj["Body"].read())
    
    def delete(self, path: str) -> bool:
        self.s3.delete_object(Bucket=self.bucket, Key=path)
        return True
    
    def exists(self, path: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def get_url(self, path: str) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path},
            ExpiresIn=3600,
        )


def get_storage() -> StorageBackend:
    if settings.STORAGE_TYPE == "s3":
        return S3Storage(bucket=os.getenv("S3_BUCKET", "faculty-assistant"))
    return LocalStorage()