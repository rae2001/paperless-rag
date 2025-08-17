# Troubleshooting Guide

## Common Startup Issues

### Container Not Starting with "PAPERLESS_URL environment variable is required"

This error indicates that the wrong application is running in the container. Here's how to fix it:

### Torch Security Vulnerability Error

If you see this error:
```
ValueError: Due to a serious vulnerability issue in `torch.load`, even with `weights_only=True`, we now require users to upgrade torch to at least v2.6
```

**Problem**: The torch version is too old for the security requirements.
**Solution**: The requirements.txt has been updated to `torch>=2.6.0`. Rebuild the container.

### Problem
The error shows:
```
ValueError: PAPERLESS_URL environment variable is required
File "/app/main.py", line 76, in startup_event
File "/app/shared/paperless_client.py", line 343, in create_paperless_client
```

But our application expects `PAPERLESS_BASE_URL` and has a different file structure.

### Quick Fix

1. **Create .env file:**
   ```bash
   python create_env.py
   ```

2. **Edit .env with your credentials:**
   ```bash
   # Edit the .env file and add:
   PAPERLESS_API_TOKEN=your_actual_token
   OPENROUTER_API_KEY=your_actual_key
   ```

3. **Fix and rebuild container:**
   ```bash
   python fix_container.py
   ```

### Manual Fix Steps

If the scripts don't work, follow these manual steps:

1. **Stop and clean up:**
   ```bash
   docker-compose down
   docker-compose down --rmi all
   docker system prune -f
   ```

2. **Create .env file manually:**
   ```bash
   cp env.example .env
   # Edit .env with your actual credentials
   ```

3. **Rebuild without cache:**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Check what's running:**
   ```bash
   python check_app.py
   ```

### Verify Fix

After rebuilding, you should see:
- Container starts without errors
- Health check at `http://localhost:8088/health` returns HTTP 200
- Logs show "Paperless RAG Q&A API" (not "RAG Chat API")

### Common Issues

**Issue**: Still getting PAPERLESS_URL error
**Solution**: The container is using cached image. Run `docker-compose down --rmi all` to force rebuild.

**Issue**: .env file not being read
**Solution**: Ensure .env is in the same directory as docker-compose.yml

**Issue**: Import errors with Pydantic
**Solution**: The requirements.txt has been updated with correct Pydantic versions.

**Issue**: Container exits immediately
**Solution**: Check logs with `docker-compose logs rag-api` for detailed error messages.

### Getting Your Credentials

**Paperless API Token:**
1. Go to `http://192.168.1.77:8000/admin/authtoken/tokenproxy/`
2. Create a new token
3. Copy the token value

**OpenRouter API Key:**
1. Sign up at https://openrouter.ai/
2. Go to Keys section
3. Create new API key
4. Add credits for usage

### Validation Commands

Test the fixed container:

```bash
# Health check
curl http://localhost:8088/health

# List endpoints
curl http://localhost:8088/

# Test question (after ingesting documents)
curl -X POST http://localhost:8088/ask \
  -H 'Content-Type: application/json' \
  -d '{"query": "test question"}'
```

If you continue having issues, run the diagnostic scripts:
- `python check_app.py` - Check what's in the container
- `python fix_container.py` - Full rebuild and fix
- `python test_api.py` - Test all endpoints
