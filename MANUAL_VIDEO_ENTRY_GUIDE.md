# Manual Video Entry Guide

## Problem: Video Callbacks Not Reaching the App

When using the Kie API to generate music videos, callbacks may not reach the application due to:

1. **Ngrok limitations**: Free ngrok domains may have intermittent connectivity issues
2. **Network issues**: Firewalls, NAT, or routing problems
3. **Callback timeout**: Kie API may timeout if the app doesn't respond within 15 seconds
4. **Domain restrictions**: Some networks block ngrok domains

## Solution: Manual Video Entry

The application includes a manual video entry system that allows you to add video entries manually when callbacks don't reach the app.

### How It Works

1. **Video generation succeeds on Kie website** but the callback doesn't reach your app
2. **You get a video URL** from the Kie website or email notification
3. **Use the manual entry form** in the History page to add the video to your history
4. **The video appears in history** with full playback and download capabilities

### Using the Manual Video Entry Form

1. Navigate to the **History** page (`/history`)
2. Scroll down to the **"Missing Video Callbacks"** section
3. Fill in the form fields:
   - **Task ID**: The task ID from Kie website (e.g., `video-task-123`)
   - **Video URL**: The direct video URL from Kie (e.g., `https://musicfile.kie.ai/video-123.mp4`)
   - **Author** (optional): Artist or creator name (max 50 chars)
   - **Domain Name** (optional): Website or brand for watermark (max 50 chars)
4. Click **"Add Video Entry"**

### Video Status Checking

If you only have a Task ID but not the video URL yet:

1. Enter the **Task ID** in the form
2. Click **"Check Video Status"**
3. The system will check if the video is ready and:
   - If ready: Auto-fills the Video URL field
   - If still processing: Shows status information

### Technical Implementation

#### Backend API Endpoints

- `POST /api/history/manual-video` - Add manual video entry
  ```json
  {
    "task_id": "video-task-123",
    "video_url": "https://musicfile.kie.ai/video-123.mp4",
    "author": "DJ Electronic",
    "domain_name": "music.example.com"
  }
  ```

- `GET /api/video-status/<video_task_id>` - Check video status
  ```json
  {
    "success": true,
    "video_task_id": "video-task-123",
    "status": "complete",
    "video_url": "https://musicfile.kie.ai/video-123.mp4",
    "has_video": true
  }
  ```

#### Data Structure

Manual video entries are stored in `history.json` with these additional fields:
- `is_manual_entry: true` - Identifies manual entries
- `manual_entry_time` - Timestamp when manually added
- `author` - Optional author field
- `domain_name` - Optional domain name field

### Best Practices

1. **Always check video status first** before manually adding
2. **Keep Task IDs** from Kie website for reference
3. **Use descriptive authors/domains** for better organization
4. **Regularly clean up** old entries using the Cleanup button

### Troubleshooting

#### Common Issues

1. **"Video URL not valid"**: Ensure the URL starts with `http://` or `https://`
2. **"Task ID already exists"**: The task is already in history (check existing entries)
3. **"Video not found"**: The video may still be processing or the URL is incorrect

#### Verification Steps

1. Verify the video URL works in a browser
2. Check the Kie website for video completion status
3. Ensure the Task ID matches the one from Kie

### Code References

- **Frontend**: `app/static/js/history.js` - `handleAddManualVideo()`, `handleCheckVideoStatus()`
- **Backend**: `app/routes.py` - `add_manual_video()`, `get_video_status()`
- **Template**: `app/templates/history.html` - "Missing Video Callbacks" section

### Future Improvements

1. **Bulk import** - Add multiple videos at once
2. **Auto-detection** - Periodically check for missing videos
3. **Email integration** - Parse video URLs from Kie notification emails
4. **API integration** - Direct integration with Kie API for status checking

---

*Last Updated: 2026-01-09*