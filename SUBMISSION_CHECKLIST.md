# 🚀 HackRx API Submission Checklist

## ✅ **Pre-Submission Verification**

### **1. API Deployment Status**
- [ ] API is deployed on Railway
- [ ] URL: `https://web-production-84e69.up.railway.app`
- [ ] Health endpoint responds: `/health`
- [ ] Root endpoint responds: `/`

### **2. Endpoint Configuration**
- [ ] Main endpoint: `/api/v1/hackrx/run`
- [ ] Full URL: `https://web-production-84e69.up.railway.app/api/v1/hackrx/run`
- [ ] Accepts POST requests
- [ ] No authentication required (for hackathon)

### **3. Request Format**
- [ ] Accepts JSON payload
- [ ] Required fields: `documents` (string), `questions` (array)
- [ ] Example:
```json
{
  "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?...",
  "questions": [
    "What is the grace period for premium payment?",
    "What is the waiting period for pre-existing diseases?"
  ]
}
```

### **4. Response Format**
- [ ] Returns JSON response
- [ ] Contains `answers` array
- [ ] Number of answers matches number of questions
- [ ] Example:
```json
{
  "answers": [
    "The grace period is 30 days.",
    "The waiting period is 36 months."
  ]
}
```

### **5. CORS Configuration**
- [ ] CORS enabled for cross-origin requests
- [ ] OPTIONS endpoint responds correctly
- [ ] Accepts requests from hackathon domain

### **6. Performance**
- [ ] Response time < 60 seconds
- [ ] Handles multiple questions
- [ ] No timeout issues

### **7. Answer Quality**
- [ ] Answers are concise (1-2 sentences)
- [ ] No "I don't have enough information" responses
- [ ] Answers are factual and direct
- [ ] No verbose explanations

## 🧪 **Testing Commands**

### **Quick Health Check**
```bash
curl https://web-production-84e69.up.railway.app/health
```

### **Test Main Endpoint**
```bash
curl -X POST https://web-production-84e69.up.railway.app/api/v1/hackrx/run \
  -H "Content-Type: application/json" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D&final=submission",
    "questions": [
      "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
      "What is the waiting period for pre-existing diseases (PED) to be covered?"
    ]
  }'
```

### **Run Full Test Suite**
```bash
python submission_checklist.py
```

## 📋 **Submission Details**

### **Webhook URL for Hackathon**
```
https://web-production-84e69.up.railway.app/api/v1/hackrx/run
```

### **Environment Variables Set in Railway**
- [ ] `GOOGLE_API_KEY` - For embeddings
- [ ] `OPENROUTER_API_KEY` - For LLM
- [ ] `HACKRX_API_KEY` - For authentication (optional)
- [ ] `PORT` - Set automatically by Railway

### **API Features**
- [ ] Document processing (PDF)
- [ ] Text extraction and chunking
- [ ] Semantic search
- [ ] Entity extraction
- [ ] LLM answer generation
- [ ] Caching (disabled for testing)

## 🎯 **Final Verification**

### **Before Submitting:**
1. Run `python submission_checklist.py` - All tests should pass
2. Test with hackathon's exact document URL
3. Verify response format matches requirements
4. Check that no authentication is required
5. Ensure CORS is working

### **Submission Ready When:**
- [ ] All checklist items are checked ✅
- [ ] All tests pass ✅
- [ ] Performance is acceptable ✅
- [ ] Answer quality is good ✅

## 🚀 **Ready to Submit!**

**Webhook URL:** `https://web-production-84e69.up.railway.app/api/v1/hackrx/run`

**Status:** ✅ Ready for HackRx Hackathon Submission 