"""Bedrock Knowledge Base synchronization."""

from typing import Any, Dict, Optional

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from ..logging_config import get_logger


class BedrockKBSyncer:
    """Triggers Bedrock KB sync after S3 uploads."""
    
    def __init__(self, knowledge_base_id: str, data_source_id: str, region: str):
        """
        Initialize Bedrock KB syncer.
        
        Args:
            knowledge_base_id: Bedrock knowledge base ID
            data_source_id: Data source ID for the S3 bucket
            region: AWS region
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for BedrockKBSyncer. Install with: pip install boto3")
        
        self.kb_id = knowledge_base_id
        self.data_source_id = data_source_id
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=region
        )
        self.logger = get_logger("kb_syncer")
    
    async def trigger_sync(self) -> Optional[str]:
        """Trigger KB ingestion job."""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=self.data_source_id,
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            self.logger.info(f"Started KB sync job: {job_id}")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to trigger sync: {e}")
            raise
    
    async def get_sync_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a sync job."""
        try:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=self.data_source_id,
                ingestionJobId=job_id,
            )
            
            job = response['ingestionJob']
            return {
                "job_id": job_id,
                "status": job['status'],
                "started_at": job.get('startedAt'),
                "updated_at": job.get('updatedAt'),
                "statistics": job.get('statistics', {}),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sync status: {e}")
            raise
