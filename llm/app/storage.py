import os
import boto3
from pathlib import Path
from app.config import settings

class StorageManager:
    def __init__(self):
        self.mode = settings.storage_mode
        
        if self.mode == "s3":
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket = settings.s3_bucket
        else:
            # Local storage
            self.local_path = Path(settings.local_storage_path)
            self.local_path.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file_bytes, file_path):
        """Upload file to storage"""
        if self.mode == "s3":
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=file_path,
                Body=file_bytes
            )
            return f"s3://{self.bucket}/{file_path}"
        else:
            # Local storage
            full_path = self.local_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(file_bytes)
            
            return str(full_path)
    
    def get_file_url(self, file_path):
        """Get public URL for file"""
        if self.mode == "s3":
            if file_path.startswith("s3://"):
                file_path = file_path.replace(f"s3://{self.bucket}/", "")
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_path},
                ExpiresIn=3600  # 1 hour
            )
            return url
        else:
            return file_path
    
    def download_file(self, file_path):
        """Download file from storage"""
        if self.mode == "s3":
            if file_path.startswith("s3://"):
                file_path = file_path.replace(f"s3://{self.bucket}/", "")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=file_path
            )
            return response['Body'].read()
        else:
            with open(file_path, 'rb') as f:
                return f.read()

storage = StorageManager()
