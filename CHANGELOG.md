# Changelog

## [Unreleased] - 2025-10-04

### Fixed
- **AWS Bedrock Knowledge Base Integration** - Complete rewrite of KB query mechanism
  - Added proper boto3 integration with AWS SigV4 authentication
  - Previously attempted unauthenticated HTTP requests, now uses AWS SDK correctly
  - Auto-detects Bedrock KB endpoints and uses appropriate API
  - Uses Bedrock Agent Runtime `retrieve` API instead of generic HTTP POST

### Added
- **Error Propagation to Agent** - Detailed error messages now passed to the agent
  - AWS error codes (e.g., AccessDenied, ValidationException) are relayed
  - HTTP status codes included in error responses
  - Meaningful error messages instead of generic "no results found"
  
- **New Function: `_query_bedrock_kb()`** - Dedicated handler for AWS Bedrock KB queries
  - Extracts KB ID and region from endpoint URL
  - Creates boto3 bedrock-agent-runtime client
  - Properly formats retrieval results with scores and metadata
  
- **Environment Variable: `KB_DIRECT_ENDPOINT`** - New configuration variable
  - Maps to existing KNOWLEDGE_BASE_ENDPOINT
  - Used by agentcore_app.py for direct API queries
  
- **Test Script: `test_kb_bedrock.py`** - Quick validation of Bedrock KB integration
  - Tests boto3 authentication
  - Validates query/response flow
  - Useful for debugging KB issues

### Changed
- **Updated `_query_via_direct_api()`** - Now detects and routes Bedrock endpoints
  - Checks if endpoint contains "bedrock-agent-runtime" and "amazonaws.com"
  - Routes Bedrock requests to `_query_bedrock_kb()`
  - Maintains backward compatibility with generic HTTP APIs
  
- **Enhanced `query_knowledge_base_via_gateway()`** - Better error handling
  - Checks for error dict in results before extracting content
  - Returns error details to calling code
  - Improved logging for debugging

- **Updated `.env.example`** - Better documentation of KB configuration
  - Added KB_DIRECT_ENDPOINT example
  - Clarified relationship between KNOWLEDGE_BASE_ENDPOINT and KB_DIRECT_ENDPOINT
  - Added inline comments for clarity

### Documentation
- **New Guide: `docs/BEDROCK_KB_SETUP.md`** - Comprehensive setup guide
  - Configuration requirements
  - AWS credentials setup
  - Troubleshooting common errors
  - Required IAM permissions
  - Example queries

## Technical Details

### Before (Broken)
```python
# Made unauthenticated HTTP POST request
response = requests.post(
    f"{kb_endpoint}/query",
    json=payload,
    headers={"Authorization": ""}  # Empty auth header!
)
# Result: 403 Forbidden - Authorization header cannot be empty
```

### After (Working)
```python
# Uses boto3 with proper AWS authentication
client = boto3.client('bedrock-agent-runtime', region_name=region)
response = client.retrieve(
    knowledgeBaseId=kb_id,
    retrievalQuery={'text': query},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': max_results
        }
    }
)
# Result: ✅ Successful retrieval with AWS SigV4 auth
```

### Dependencies Used
- `boto3>=1.34.0` - AWS SDK for Python (already in dependencies)
- `botocore` - Core functionality for boto3

### AWS APIs Used
- **Service**: Amazon Bedrock Agent Runtime
- **API**: `Retrieve` 
- **Endpoint**: `https://bedrock-agent-runtime.{region}.amazonaws.com`
- **Auth**: AWS Signature Version 4

### Error Handling Improvements
| Error Type | Before | After |
|------------|--------|-------|
| Auth failure | "No results found" | "AWS Error: AccessDenied - User not authorized..." |
| Invalid KB | "No results found" | "AWS Error: ResourceNotFoundException - Knowledge base not found" |
| Network issue | Exception raised | "Connection error: [details]" |
| No matches | "No results found" | "No matching documents found in knowledge base" |

## Testing Performed
- ✅ Boto3 client initialization
- ✅ AWS authentication with credentials file
- ✅ Knowledge base query execution
- ✅ Result parsing and formatting
- ✅ Error handling for various failure modes
- ✅ Integration with Strands agent tools

## Migration Notes
If you have an existing `.env` file, add this line:
```bash
KB_DIRECT_ENDPOINT=<same value as KNOWLEDGE_BASE_ENDPOINT>
```
