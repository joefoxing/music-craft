# Google Drive Public URL Guide for Music Cover Generator

This guide explains how to use Google Drive public URLs with the Music Cover Generator application.

## Why Use Google Drive URLs?

The Kie API requires publicly accessible audio URLs for processing. Localhost URLs (`http://localhost:5000/...`) are not accessible to Kie's servers. Google Drive provides a convenient way to host audio files publicly.

## Step-by-Step Guide

### 1. Upload Your Audio File to Google Drive

1. Go to [drive.google.com](https://drive.google.com)
2. Click "New" → "File upload"
3. Select your audio file (MP3, WAV, OGG, M4A, FLAC)
4. Wait for the upload to complete

### 2. Get a Shareable Link

1. Right-click on the uploaded file
2. Select "Get link"
3. Click "Change to anyone with the link"
4. Set permission to "Viewer" (not "Editor")
5. Click "Copy link"
6. Click "Done"

### 3. Convert to Direct Download Link

The copied link looks like:
```
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
```

You need to convert it to a direct download link:
```
https://drive.google.com/uc?export=download&id=FILE_ID
```

**Where to find FILE_ID:**
- The FILE_ID is the long string between `/d/` and `/view` in the original URL
- Example: `https://drive.google.com/file/d/1AbC2DeF3GhIjKlMnOpQrStUvWxYz/view`
  - FILE_ID = `1AbC2DeF3GhIjKlMnOpQrStUvWxYz`
  - Direct URL = `https://drive.google.com/uc?export=download&id=1AbC2DeF3GhIjKlMnOpQrStUvWxYz`

### 4. Use in the Application

1. Open the Music Cover Generator at `http://localhost:5000/`
2. In the "Audio Source" section, click "Use URL" tab
3. Paste the direct download URL:
   ```
   https://drive.google.com/uc?export=download&id=YOUR_FILE_ID
   ```
4. Click "Test Audio URL" to verify accessibility
5. If successful, click "Use This URL"
6. Proceed with generation settings

## Alternative Methods

### Method A: Using ngrok (For Local Files)

If you want to use local files without uploading to Google Drive:

1. Install ngrok: `npm install -g ngrok` or download from [ngrok.com](https://ngrok.com)
2. Run: `ngrok http 5000`
3. Copy the public URL (e.g., `https://abc123.ngrok.io`)
4. Upload files through the application as usual
5. The application will use the ngrok URL which is publicly accessible

### Method B: Using Public Sample Files

For testing, you can use these public audio URLs:

- `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3`
- `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3`
- `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3`

## Troubleshooting

### Common Issues

#### 1. "URL test failed: Could not access the URL"
- Ensure the file is set to "Anyone with the link" permission
- Try the direct download format: `https://drive.google.com/uc?export=download&id=FILE_ID`
- Some organizations restrict external access to Google Drive files

#### 2. "403 Forbidden" or "404 Not Found"
- Verify the FILE_ID is correct
- Make sure the file hasn't been deleted or moved
- Check that sharing permissions are set correctly

#### 3. "CORS Error" in browser console
- Google Drive may block direct audio access from some browsers
- Try using a different public hosting service (Dropbox, AWS S3, etc.)
- Use the "Test Audio URL" button to verify accessibility

#### 4. File too large
- Google Drive has file size limits for direct downloads
- Maximum recommended: 100MB for audio files
- For larger files, consider compressing or using a different service

### Testing Your URL

Before using in the application, you can test the URL directly:

1. Open a new browser tab
2. Paste the Google Drive direct URL
3. If it starts downloading the file, the URL works
4. If you see a Google Drive page, the URL format is incorrect

## Best Practices

1. **File Preparation:**
   - Use common audio formats: MP3, WAV, OGG
   - Keep files under 8 minutes (Kie API limit)
   - Compress large files to reduce upload time

2. **URL Management:**
   - Keep a list of your FILE_IDs for reuse
   - Remove sharing permissions when no longer needed
   - Test URLs before starting generation

3. **Application Usage:**
   - Always test URLs with the "Test Audio URL" button
   - Use the "Use URL" tab for Google Drive links
   - Use the "Upload File" tab for local files with ngrok

## Security Considerations

- Google Drive links are publicly accessible to anyone with the URL
- Consider creating a separate Google account for testing
- Remove sharing permissions after generation is complete
- Do not share sensitive or copyrighted material

## Advanced: Using Other Cloud Services

### Dropbox
1. Upload file to Dropbox
2. Right-click → Share → Create link
3. Change `www.dropbox.com` to `dl.dropboxusercontent.com`
4. Example: `https://dl.dropboxusercontent.com/s/FILE_ID/filename.mp3`

### AWS S3
1. Upload to a public S3 bucket
2. Use URL format: `https://BUCKET.s3.REGION.amazonaws.com/FILE_KEY`
3. Ensure bucket has public read permissions

### GitHub
1. Upload to a GitHub repository
2. Use raw URL: `https://raw.githubusercontent.com/USER/REPO/BRANCH/FILE`

## Support

If you encounter issues:
1. Check the application console for error messages
2. Verify your Google Drive sharing settings
3. Test the URL in a separate browser tab
4. Contact support with the specific error message

---

**Note:** Generated files via Kie API will be deleted after 15 days. Always download and save your generated covers locally.