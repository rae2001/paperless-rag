# CORS Troubleshooting Guide

This guide helps resolve Cross-Origin Resource Sharing (CORS) issues when using the Paperless RAG Chat UI.

## Quick Solutions

### 1. Use the Clean Chat UI (Recommended)

```bash
python3 serve_clean_chat.py
```

Then access http://localhost:8080

### 2. Configure the API URL

1. Open the chat UI
2. Click on the API URL in the header (e.g., "(http://localhost:8088)")
3. Try different URLs:
   - `http://localhost:8088`
   - `http://127.0.0.1:8088`
   - `http://[your-computer-ip]:8088`

### 3. Restart the API with Updated CORS Settings

The API has been updated to handle CORS properly. Restart it:

```bash
docker compose down
docker compose up --build
```

## Understanding CORS

CORS errors occur when:
- The browser blocks requests from one origin (e.g., http://localhost:8080) to another (e.g., http://localhost:8088)
- The API doesn't send proper CORS headers
- Preflight requests (OPTIONS) are not handled correctly

## Detailed Troubleshooting Steps

### Step 1: Verify API is Running

```bash
# Check if API is accessible
curl http://localhost:8088/health

# Should return JSON with health status
```

### Step 2: Check CORS Configuration

```bash
# Test CORS headers
curl -I http://localhost:8088/health

# Look for these headers:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

### Step 3: Test from Browser Console

Open browser developer tools (F12) and run:

```javascript
fetch('http://localhost:8088/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

### Step 4: Common Fixes

#### Fix 1: Use Same Protocol
Ensure both UI and API use the same protocol (both http:// or both https://)

#### Fix 2: Update Environment Variables
Edit `.env` file and ensure ALLOWED_ORIGINS includes your UI URL:

```env
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,*
```

#### Fix 3: Disable Browser Security (Development Only)
For Chrome on Windows:
```bash
chrome.exe --user-data-dir="C:/Chrome dev session" --disable-web-security
```

**Warning:** Only use this for development!

#### Fix 4: Use a Proxy
Configure the UI server to proxy API requests, avoiding CORS entirely.

## Alternative Solutions

### 1. Use Docker Network
Run the UI in the same Docker network as the API:

```bash
docker run -it --rm --network paperless-rag_default -p 8080:8080 python:3.9 bash
# Inside container: serve the UI
```

### 2. Use Nginx Reverse Proxy
Set up Nginx to serve both UI and API from the same origin.

### 3. Browser Extensions
Install CORS-unblocking extensions (development only):
- "CORS Unblock" for Chrome
- "CORS Everywhere" for Firefox

## Still Having Issues?

1. Check browser console for specific error messages
2. Verify Windows Firewall isn't blocking connections
3. Try a different browser
4. Check if antivirus software is interfering
5. Use the debug tool: Open `debug_connection.html` in your browser

## Contact Support

If you're still experiencing issues:
1. Note the exact error message from browser console
2. Check which URLs you've tried
3. Verify your Docker and API versions
4. Create an issue with these details
