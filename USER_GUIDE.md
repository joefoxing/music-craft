# 🎵 Suno Clone - User Guide

Welcome to the **Suno Clone** (Music Craft), a powerful AI-powered music generation platform. This application allows you to generate original songs from text, create covers, remix tracks, and manipulate audio using advanced AI models.

## 🚀 Getting Started

### 1. Access the Application
- **Web Interface**: Navigate to the application URL (e.g., `http://localhost:3000` or your deployed domain).
- **Landing Page**: You will see the main "Make any song" interface.

### 2. Account Creation
To access all features, you must create an account:
1.  Click **Sign Up** in the top right corner.
2.  Enter your email and create a password.
3.  Alternatively, use **Sign in with Google** (if configured).

---

## 🎹 Key Features

### 1. Music Generator (Text-to-Music)
Create original songs from scratch using AI.
- **Navigation**: Click **Create** or go to `/music-generator`.
- **Modes**:
    - **Simple Mode**: Enter a description (e.g., "A sad piano ballad about rain"). The AI writes lyrics and composes the music.
    - **Custom Mode**:
        - **Lyrics**: Write your own lyrics or paste them in.
        - **Style**: Specify genres (e.g., "Rock, Metal, Fast").
        - **Title**: Name your track.
- **Output**: The AI generates two variations of your song.

### 2. Cover Generator (Audio-to-Audio)
Remix or change the style of an existing song.
- **Navigation**: Go to `/cover-generator`.
- **Upload**: Upload an audio file (MP3, WAV, etc.).
- **Settings**: Choose the target style/genre for the cover.

### 3. Audio Tools
Explore the toolkit for specific audio tasks:
-   **Add Instrumental**: Upload a vocal track and generate a backing track.
-   **Add Vocal**: Upload an instrumental and generate vocals.
-   **Vocal Removal**: Separate vocals from a full mix (Karaoke mode).
-   **Voice Conversion**: Change the timbre of a voice in an audio file.

---

## 📚 Library & History

### Library
- **View**: Click **Library** in the navigation bar.
- **Manage**: See all your generated tracks, play them, download them, or delete them.

### History
- **View**: Click **History** (or access via Profile/Dashboard).
- **Status**: Track the progress of ongoing generations.
- **Logs**: View detailed information about past tasks.

---

## ⚙️ Dashboard & Profile

- **Dashboard**: Overview of your activity and quick links to tools.
- **Profile**: Manage your account settings and view usage statistics.

---

## 🔧 For Developers: Local Docker Setup

If you are a developer running this locally:

1.  **Prerequisites**: Install Docker and Docker Compose.
2.  **Start App**:
    ```bash
    make up
    # or
    docker compose up -d
    ```
3.  **Access**: `http://localhost:3000`
4.  **Logs**: `make logs`

See `README.md` for full technical documentation.
