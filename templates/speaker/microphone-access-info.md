On Windows 11 with Chrome, you need to grant microphone permissions. Here's how to fix it:

## **Quick Fix - Allow in Chrome:**

1. Look for a camera/microphone icon in the address bar (left side, near the URL)
2. Click it and select "Allow" for microphone access
3. Refresh the page

## **If that doesn't work - Check Chrome Settings:**

1. Go to `chrome://settings/content/microphone`
2. Make sure microphone is set to "Sites can ask to use your microphone"
3. Check if your site is in the "Blocked" list - if so, remove it
4. Make sure the correct microphone device is selected

## **Windows 11 Privacy Settings:**

1. Press `Win + I` to open Settings
2. Go to **Privacy & Security** → **Microphone**
3. Make sure "Microphone access" is **ON**
4. Make sure "Let apps access your microphone" is **ON**
5. Scroll down and make sure "Let desktop apps access your microphone" is **ON**

## **Important: HTTPS Requirement**

If you're testing locally, Chrome requires either:
- `https://` (secure connection), OR
- `localhost` or `127.0.0.1`

**If you're accessing via `http://frflashy.com` or `http://[your-ip]`, Chrome will block microphone access.** You need HTTPS for remote access.

Think of it like Python's security model - certain operations (like file access) require explicit permissions, and browsers treat microphone access the same way.

Are you testing locally or accessing the actual frflashy.com site? If it's the live site, you'll need an SSL certificate (Let's Encrypt is free and easy to set up).
