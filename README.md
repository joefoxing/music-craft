# Music Cover Generator v1.0

A Python web application for generating music covers using the Kie API. This application allows users to upload audio files and transform them into new musical styles while retaining the original melody.

**Version**: 1.0.0
**Release Date**: January 11, 2026
**Status**: Stable Release

## Version Highlights
- **Complete Feature Set**: Audio upload, dual generation modes, multiple AI models
- **Enhanced Callback System**: Comprehensive callback processing and history tracking
- **Production Ready**: Clean codebase with proper error handling and documentation
- **Ngrok Integration**: Built-in public tunnel support for external API callbacks
- AI assistants: see docs/AI_RULES.md
## Features

- **Audio File Upload**: Upload MP3, WAV, OGG, M4A, or FLAC files (max 100MB)
- **Dual Generation Modes**:
  - **Simple Mode**: Just provide a prompt, lyrics auto-generated (max 500 chars)
  - **Custom Mode**: Full control over style, title, and exact lyrics
- **Multiple AI Models**: Support for V5, V4_5PLUS, V4_5, V4_5ALL, and V4 models
- **Real-time Status Tracking**: Poll task status and receive callbacks
- **Responsive Web Interface**: Modern, user-friendly interface
- **Parameter Validation**: Automatic validation of character limits and required fields
- **Enhanced Index Page** (Phase 1):
  - **Activity Dashboard**: Real-time feed of user activities and music generation history
  - **Template Library**: Curated collection of 20+ music generation templates with one-click application
  - **Advanced Filtering**: Filter templates by category, difficulty, popularity, and tags
  - **Template Search**: Full-text search across template names, descriptions, and tags

## Prerequisites

- Python 3.9 or higher
- Kie API key (get from [https://kie.ai/api-key](https://kie.ai/api-key))

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Lyric_Cover
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Kie API key:
   ```
   KIE_API_KEY=your-api-key-here
   ```

## Usage

1. Start the application:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Follow the three-step process:
   - **Step 1**: Upload an audio file
   - **Step 2**: Configure generation settings
   - **Step 3**: Generate the music cover

## API Endpoints

### Backend Endpoints
- `GET /` - Web interface
- `POST /upload` - File upload endpoint
- `POST /api/generate-cover` - Generate music cover
- `POST /api/v1/generate` - Direct music generation (text-to-music)
- `GET /api/task-status/<task_id>` - Check task status
- `GET /api/v1/lyrics/record-info` - Retrieve lyrics generation status and content
- `POST /callback` - Kie API callback handler
- `GET /api/models` - Get available models and limits
- **Enhanced Index Page Endpoints**:
  - `GET /api/templates` - Get templates with filtering and pagination
  - `GET /api/templates/<template_id>` - Get specific template by ID
  - `GET /api/templates/categories` - Get all template categories
  - `GET /api/templates/stats` - Get template statistics
  - `GET /api/user-activity` - Get aggregated user activities

### Kie API Integration
The application integrates with multiple Kie API endpoints:

1. **Music Cover Generation**: `/api/v1/generate/upload-cover` - Generate music covers from uploaded audio
2. **Direct Music Generation**: `/api/v1/generate` - Generate music directly from text prompts (text-to-music)
3. **Lyrics Generation**: `/api/v1/lyrics` - Generate lyrics from text prompts
4. **Music Video Generation**: `/api/v1/mp4/generate` - Generate music videos from audio
5. **Lyrics Record Info**: `/api/v1/lyrics/record-info` - Retrieve lyrics generation status and content

#### Direct Music Generation Endpoint (`/api/v1/generate`)
The new `/api/v1/generate` endpoint supports both custom and non-custom modes:

**For Custom Mode (`customMode: true`):**
- If `instrumental: true`: Must provide `style` and `title`
- If `instrumental: false`: Must provide `style`, `prompt` (used as exact lyrics), and `title`
- Adhere to model-specific character limits

**For Non-custom Mode (`customMode: false`):**
- Only the `prompt` (max 500 characters) is required
- All other parameters should be omitted or left empty

**Required Parameters:**
- `customMode` (boolean): Whether to use custom mode
- `instrumental` (boolean): Whether the audio should be instrumental
- `callBackUrl` (string): URL for status updates
- `model` (string): Model version (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
- `prompt` (string): Description of desired audio content or exact lyrics

**Optional Parameters for Custom Mode:**
- `vocalGender` ('m' or 'f')
- `styleWeight` (0-1)
- `weirdnessConstraint` (0-1)
- `audioWeight` (0-1)
- `negativeTags` (string)
- `personaId` (string)

**Authentication:** Include API key in the request header: `Authorization: Bearer YOUR_API_KEY`

## Configuration

### Environment Variables
- `KIE_API_KEY`: Your Kie API key (required)
- `FLASK_DEBUG`: Enable debug mode (default: False)
- `SECRET_KEY`: Flask secret key for sessions
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `BASE_URL`: Base URL for callbacks (default: http://localhost:5000)

### Email Configuration (for user verification and password reset)
The application includes user authentication with email verification. To enable email sending:

1. **For Gmail** (recommended for development):
   - Enable 2-factor authentication on your Google account
   - Generate an app-specific password: https://myaccount.google.com/apppasswords
   - Use that password (not your regular Gmail password)

   **Note**: App passwords are only needed for sending emails via SMTP. For user authentication, the application now supports "Sign in with Google" (OAuth) which is the recommended approach and doesn't require app passwords.

2. **Configure in `.env` file**:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

3. **Development Mode**:
   - When `FLASK_DEBUG=true` and email is not configured, verification links are printed to the console
   - This allows testing email verification without setting up real email

4. **Production**:
   - For production, use a dedicated email service (SendGrid, Mailgun, etc.)
   - Update the SMTP settings accordingly in your production environment

### OAuth Authentication (Google & GitHub)

The application supports OAuth authentication via Google and GitHub. To enable OAuth login:

1. **Google OAuth Setup**:
  - Go to [Google Cloud Console](https://console.cloud.google.com/)
  - Create a new project or select an existing one
  - Enable the "Google+ API" (now called "Google People API") and "Google OAuth2 API"
  - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
  - Configure consent screen if prompted
  - Create a web application credential
  - Add authorized redirect URI: `https://your-domain.com/auth/oauth/callback/google`
    - For local development: `http://localhost:5000/auth/oauth/callback/google`
    - For Ngrok: `https://your-ngrok-url.ngrok-free.app/auth/oauth/callback/google`
  - Copy the Client ID and Client Secret to your `.env` file:
    ```
    GOOGLE_OAUTH_CLIENT_ID=your-google-client-id-here
    GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret-here
    ```

2. **GitHub OAuth Setup**:
  - Go to [GitHub Developer Settings](https://github.com/settings/developers)
  - Click "New OAuth App"
  - Application name: "Music Cover Generator"
  - Homepage URL: Your application URL (e.g., `http://localhost:5000` or Ngrok URL)
  - Authorization callback URL: `https://your-domain.com/auth/oauth/callback/github`
    - For local development: `http://localhost:5000/auth/oauth/callback/github`
    - For Ngrok: `https://your-ngrok-url.ngrok-free.app/auth/oauth/callback/github`
  - Register application
  - Copy the Client ID and Client Secret to your `.env` file:
    ```
    GITHUB_OAUTH_CLIENT_ID=your-github-client-id-here
    GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret-here
    ```

3. **Enable OAuth**:
  - Set `OAUTH_ENABLED=true` in your `.env` file
  - Restart the application

**Note**: OAuth authentication creates user accounts automatically if they don't exist. Email verification is automatically marked as verified for OAuth users.

### Ngrok Integration
The application includes built-in Ngrok support for creating public tunnels to your local server. This is essential for receiving callbacks from external APIs like Kie.

**Ngrok Environment Variables:**
- `NGROK_ENABLED`: Enable Ngrok tunnel (default: false)
- `NGROK_AUTH_TOKEN`: Optional Ngrok auth token for persistent tunnels
- `NGROK_REGION`: Ngrok server region (us, eu, ap, au, sa, jp, in) (default: us)
- `NGROK_URL`: Manually set Ngrok URL if not using auto-tunnel

**Usage:**
1. Set `NGROK_ENABLED=true` in your `.env` file
2. (Optional) Get a free auth token from [ngrok.com](https://ngrok.com) and set `NGROK_AUTH_TOKEN`
3. Start the application: `python run.py`
4. The application will automatically create a public Ngrok tunnel
5. Use the provided public URL for callbacks and external access

**Note:** Without an auth token, Ngrok tunnels are temporary and change each time you restart the application.

### Model Limitations
Each model has different character limits:

| Model | Prompt Limit | Style Limit | Title Limit |
|-------|-------------|-------------|-------------|
| V5 | 5000 chars | 1000 chars | 100 chars |
| V4_5PLUS | 5000 chars | 1000 chars | 100 chars |
| V4_5 | 5000 chars | 1000 chars | 100 chars |
| V4_5ALL | 5000 chars | 1000 chars | 80 chars |
| V4 | 3000 chars | 200 chars | 80 chars |

**Simple Mode**: Prompt limited to 500 characters regardless of model.

## Project Structure

```
Lyric_Cover/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── kie_client.py        # Kie API client
│   ├── routes.py            # Application routes
│   ├── ngrok_utils.py       # Ngrok tunnel management
│   ├── core/                # Core utilities and API client
│   ├── services/            # Business logic services
│   │   ├── template_service.py    # Template management service
│   │   ├── history_service.py     # History management service
│   │   └── callback_service.py    # Callback processing service
│   ├── routes/              # Route blueprints
│   │   ├── api.py          # API endpoints (including enhanced features)
│   │   ├── auth.py         # Authentication routes
│   │   ├── callback.py     # Callback handling routes
│   │   ├── history_routes.py # History viewing routes
│   │   └── main.py         # Main web interface routes
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Stylesheet
│   │   ├── js/
│   │   │   ├── components/  # Frontend components
│   │   │   │   ├── activityFeed.js    # Activity dashboard component
│   │   │   │   ├── templateGallery.js # Template library component
│   │   │   │   └── templateApplier.js # Template application component
│   │   │   └── app.js       # Main frontend JavaScript
│   │   ├── templates/       # Template data files
│   │   │   ├── templates.json          # Primary template file
│   │   │   └── templates_complete.json # Complete template collection
│   │   └── uploads/         # Uploaded audio files
│   └── templates/
│       ├── index.html       # Main web interface
│       ├── index_enhanced.html # Enhanced index page with dashboard
│       └── auth/            # Authentication templates
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── ENHANCED_INDEX_PAGE_PHASE1.md # Enhanced features documentation
└── README.md               # This file
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest

# Run tests
pytest
```

### Code Style
This project follows PEP 8 guidelines. Use black for formatting:
```bash
pip install black
black .
```

## Limitations

1. **Audio Duration**: Uploaded audio must not exceed 8 minutes (1 minute for V4_5ALL model)
2. **File Retention**: Generated files are deleted from Kie servers after 15 days
3. **API Rate Limits**: Subject to Kie API rate limits
4. **File Size**:
   - Maximum upload size is 40MB when using Ngrok (free tier limit)
   - Can be increased to 100MB when running locally without Ngrok
   - Configure via `MAX_CONTENT_LENGTH` in `.env` file

## Troubleshooting

### Common Issues

1. **"Invalid API Key" error**:
   - Verify your KIE_API_KEY in the .env file
   - Check if the API key has sufficient credits

2. **File upload fails with 413 error**:
   - **When using Ngrok**: Ensure file size is under 40MB (Ngrok free tier limit)
   - **When running locally**: File size limit is 100MB (configurable via MAX_CONTENT_LENGTH)
   - Check file format (MP3, WAV, OGG, M4A, FLAC)
   - Verify uploads directory has write permissions

3. **"Can't fetch the uploaded audio" error**:
   - Usually caused by file size exceeding Ngrok limits
   - Reduce file size or compress audio
   - Alternatively, run locally without Ngrok (set NGROK_ENABLED=false)

4. **Generation fails**:
   - Check character limits for your selected model
   - Ensure all required fields are filled
   - Verify internet connectivity to Kie API

5. **Task status returns 404 error**:
   - The Kie API may not expose a public task status endpoint
   - The application will automatically switch to callback-only mode
   - Status updates will be received via the callback endpoint
   - Check that your callback URL is accessible (http://localhost:5000/callback when running locally)
   - The web interface will show "Waiting for Callback" when this occurs

6. **Ngrok tunnel creation fails**:
   - "Endpoint already online" error: Another Ngrok process is running
   - Solution: Stop existing Ngrok processes or set NGROK_ENABLED=false
   - The application will try to reuse existing tunnels when possible

7. **Email verification not sent**:
   - **Development Mode**: Check the console for verification links (printed when email is not configured)
   - **Gmail Authentication Error**: Ensure you're using an app-specific password, not your regular Gmail password
   - **SMTP Configuration**: Verify MAIL_USERNAME and MAIL_PASSWORD in .env file
   - **Gmail Security**: Some Gmail accounts may require enabling "Less secure app access" (not recommended) or using app-specific passwords
   - **Alternative**: Use a different email service (SendGrid, Mailgun, etc.) with appropriate SMTP settings

### Task Status Note
The Kie API documentation mentions a "Get Music Generation Details" endpoint but doesn't specify the exact URL. The application tries multiple common patterns:
- `/api/v1/generate/{task_id}`
- `/api/v1/tasks/{task_id}`
- `/api/v1/generate/task/{task_id}`
- `/api/v1/generate/details/{task_id}`

If all patterns fail, the application gracefully falls back to callback-only status updates. This is normal behavior and doesn't affect the generation process.

### Logs
Check the Flask application logs for detailed error information.

## License

This project is for educational and demonstration purposes.

## Acknowledgments

- [Kie AI](https://kie.ai) for providing the music generation API
- Flask framework for the web backend
- All contributors and testers

## Support

For issues with the Kie API, contact [Kie AI support](mailto:support@kie.ai).

For application issues, check the [GitHub issues](https://github.com/your-repo/issues) or create a new issue.T e s t   d e p l o y m e n t 
 
 #   A u t o m a t e d   D e p l o y m e n t   T e s t 
 
 