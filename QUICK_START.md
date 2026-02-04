# Quick Start Guide

## 1. Installation

```bash
# Clone or create project directory
cd Lyric_Cover

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Kie API key
```

## 2. Configuration

Edit the `.env` file:
```env
KIE_API_KEY=your-api-key-here
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
```

Get your API key from: https://kie.ai/api-key

## 3. Running the Application

```bash
# Start the Flask server
python run.py
```

The application will start at: http://localhost:5000

## 4. Using the Web Interface

1. **Upload Audio File**: Drag and drop or click to upload an audio file (MP3, WAV, OGG, M4A, FLAC)
2. **Configure Settings**:
   - Select AI Model (V4, V5, etc.)
   - Choose Simple or Custom Mode
   - Enter prompt and other parameters
3. **Generate Cover**: Click "Generate Music Cover"
4. **Monitor Progress**: Track task status in real-time
5. **Download Results**: Get your generated music cover

## 5. API Usage Examples

### Upload a file
```bash
curl -X POST -F "file=@audio.mp3" http://localhost:5000/upload
```

### Generate cover (Simple Mode)
```bash
curl -X POST http://localhost:5000/api/generate-cover \
  -H "Content-Type: application/json" \
  -d '{
    "upload_url": "http://localhost:5000/static/uploads/filename.mp3",
    "prompt": "A relaxing piano melody",
    "custom_mode": false,
    "instrumental": false,
    "model": "V4"
  }'
```

### Check task status
```bash
curl http://localhost:5000/api/task-status/task_id_here
```

## 6. Troubleshooting

### Common Issues

1. **"Invalid API Key"**: Verify your KIE_API_KEY in .env file
2. **File upload fails**: Check file size (<100MB) and format
3. **Generation fails**: Verify character limits and required parameters
4. **Server not starting**: Check if port 5000 is available

### Logs
Check the Flask console output for detailed error messages.

## 7. Next Steps

- Add database support for tracking multiple users
- Implement user authentication
- Add batch processing capabilities
- Integrate with cloud storage (S3, Google Cloud)
- Add email notifications for completed tasks

## Support

- API Documentation: https://docs.kie.ai/suno-api/upload-and-cover-audio
- Application Issues: Check README.md for troubleshooting
- Kie API Support: support@kie.ai