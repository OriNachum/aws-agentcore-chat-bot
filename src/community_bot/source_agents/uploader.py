"""S3 uploader for knowledge base documents."""

import json
from typing import List

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from ..logging_config import get_logger
from .document import Document


class S3Uploader:
    """Manages uploading documents to S3 for Bedrock KB ingestion."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3Uploader. Install with: pip install boto3")
        
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
        self.logger = get_logger("s3_uploader")
    
    async def upload_document(self, doc: Document) -> str:
        """Upload a single document to S3."""
        s3_key = doc.to_s3_key()
        
        try:
            # Convert to Bedrock-compatible format
            content = json.dumps(doc.to_bedrock_format(), indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source_type': doc.source_type,
                    'category': doc.category,
                    'timestamp': doc.timestamp.isoformat(),
                }
            )
            
            self.logger.info(f"Uploaded document to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Failed to upload document: {e}")
            raise
    
    async def upload_batch(self, docs: List[Document]) -> List[str]:
        """Upload multiple documents."""
        keys = []
        for doc in docs:
            try:
                key = await self.upload_document(doc)
                keys.append(key)
            except Exception as e:
                self.logger.error(f"Failed to upload {doc.source_id}: {e}")
        return keys
