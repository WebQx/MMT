# Testing Production Fixes

## 1. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 9000
```

## 2. Run Automated Tests
```bash
# Run fix verification
python test_fixes.py

# Run full test suite
cd backend && pytest -v
```

## 3. Manual Security Tests

### Path Traversal Protection
```bash
curl -X POST http://localhost:9000/upload_chunk/ \
  -F "chunk=@test.txt" \
  -F "filename=../../../etc/passwd"
# Should return 400 error
```

### Log Injection Prevention
```bash
curl -X POST http://localhost:9000/transcribe/cloud/ \
  -H "Authorization: Bearer guestsecret" \
  -F "file=@test.wav" \
  -F "filename=test\nINJECTED_LOG_ENTRY.wav"
# Logs should show sanitized filename
```

## 4. Error Handling Tests

### Invalid JSON
```bash
curl -X POST http://localhost:9000/transcribe/cloud/ \
  -H "Content-Type: application/json" \
  -d "invalid json"
# Should return structured error
```

### Missing Auth
```bash
curl http://localhost:9000/transcripts/1
# Should return 401 with correlation ID
```

## 5. Check Logs
```bash
# Look for structured error messages
tail -f logs/app.log | grep -E "(error|warning)"

# Verify no generic exceptions
grep -r "except Exception:" backend/ --exclude-dir=tests
# Should return minimal results
```

## 6. Security Scan
```bash
# Install tools
pip install bandit safety

# Run scans
bandit -r backend/
safety check -r backend/requirements.txt
```

## Expected Results
- ✅ No path traversal vulnerabilities
- ✅ Structured error responses with correlation IDs
- ✅ Sanitized log entries
- ✅ Specific exception handling
- ✅ Input validation working
- ✅ All tests passing