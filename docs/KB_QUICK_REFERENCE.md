# Quick Reference - AWS Bedrock KB Integration

## 🎯 Problem
```
❌ 403 Forbidden: Authorization header cannot be empty
```

## ✅ Solution
Added boto3 with proper AWS authentication

---

## 📋 Configuration Checklist

- [x] AWS credentials in `~/.aws/credentials`
- [x] `KB_DIRECT_ENDPOINT` in `.env`
- [x] `AWS_REGION` in `.env`
- [x] `KNOWLEDGE_BASE_ID` in `.env`
- [x] IAM permissions for `bedrock:Retrieve`

---

## 🚀 Quick Start

### 1. Update .env
```bash
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/NIZI6QLHY7/retrieve-and-generate
```

### 2. Test It
```powershell
uv run python test_kb_bedrock.py
```

### 3. Run Bot
```powershell
uv run community-bot
```

---

## 🔧 Key Functions

| Function | Purpose |
|----------|---------|
| `kb_query_tool()` | Strands tool invoked by agent |
| `_query_via_direct_api()` | Routes to appropriate KB handler |
| `_query_bedrock_kb()` | ⭐ NEW - Uses boto3 for AWS |
| `_extract_content_from_result()` | Formats results for agent |

---

## 📊 What Changed

### Before
```python
requests.post(endpoint, headers={"Authorization": ""})
# ❌ No AWS auth
```

### After
```python
boto3.client('bedrock-agent-runtime').retrieve(...)
# ✅ Proper AWS SigV4 auth
```

---

## 🐛 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 403 Forbidden | Missing/invalid credentials | Check `~/.aws/credentials` |
| AccessDenied | Missing IAM permission | Add `bedrock:Retrieve` permission |
| ResourceNotFound | Wrong KB ID or region | Verify KB_ID and AWS_REGION |
| No results | Query doesn't match docs | Try different query |

---

## 📈 Performance

- **Latency**: 1-2 seconds
- **Cost**: ~$0.00002 per query
- **Max Results**: 5 (configurable)

---

## 📚 Documentation

- `docs/BEDROCK_KB_SETUP.md` - Full setup guide
- `docs/KB_ARCHITECTURE.md` - Architecture details
- `docs/FIX_SUMMARY.md` - What was fixed
- `CHANGELOG.md` - Detailed changes

---

## ✅ Testing

```powershell
# Quick test
uv run python test_kb_bedrock.py

# Full integration
uv run community-bot
```

In Discord: `"What are word embeddings?"`

---

## 🎓 Example Query Result

**Query**: "What are word embeddings?"

**Response**: 
```
✅ Found 3 results

Result 1 (score: 0.510):
Word embeddings are dense vector representations 
of words that capture semantic meaning...

[... more results ...]
```

---

## 🔐 Required IAM Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": "bedrock:Retrieve",
        "Resource": "arn:aws:bedrock:us-east-1:*:knowledge-base/NIZI6QLHY7"
    }]
}
```

---

## 💡 Pro Tips

1. **Cache results** - Consider implementing query caching
2. **Monitor costs** - Check CloudWatch for usage
3. **Tune results** - Adjust `max_results` parameter
4. **Better queries** - More specific queries = better results
5. **Error messages** - Now visible to agent for debugging

---

**Status**: ✅ Working & Tested

**Last Updated**: October 4, 2025
