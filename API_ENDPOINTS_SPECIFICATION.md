# API Endpoints Specification for AI Music Generation System

## Overview
This document defines the REST API endpoints for the AI music generation system. The API follows RESTful principles and provides comprehensive functionality for generating, managing, and retrieving AI-generated music tracks.

## Base URL
```
https://api.musicgen.example.com/v1
```

## Authentication
All endpoints require authentication via API key or JWT token.

### Headers
```
Authorization: Bearer <api_key_or_jwt_token>
Content-Type: application/json
```

## Response Format
All responses follow this structure:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-12T17:55:04Z",
  "request_id": "req_1234567890abcdef"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter: tempo must be between 40 and 240",
    "details": {
      "parameter": "tempo",
      "value": 300,
      "constraint": "40-240"
    }
  },
  "timestamp": "2024-01-12T17:55:04Z",
  "request_id": "req_1234567890abcdef"
}
```

## Endpoints

### 1. Music Generation Endpoints

#### 1.1 Generate Music from Parameters
**POST** `/ai/generate`

Generate original music based on detailed parameters.

**Request Body:**
```json
{
  "parameters": {
    "genre": "electronic",
    "subgenre": "synthwave",
    "mood": "nostalgic",
    "tempo": 120,
    "key": "C_minor",
    "duration": 180,
    "instrumental": false,
    "lyrics": {
      "enabled": true,
      "theme": "cyberpunk_city",
      "language": "en",
      "style": "poetic_tech"
    },
    "primary_instruments": ["synth_bass", "drum_machine", "arpeggiator"],
    "complexity": "medium",
    "ai_model": "kie_v4",
    "creativity": 0.7,
    "output_formats": ["wav", "mp3", "midi"],
    "audio_quality": "high"
  },
  "metadata": {
    "title": "Neon Dreams",
    "description": "A cyberpunk synthwave track for nighttime driving",
    "tags": ["cyberpunk", "synthwave", "80s", "nostalgic"],
    "project_id": "proj_123"
  },
  "callback_url": "https://your-app.com/callback",
  "webhook_events": ["generation_started", "generation_completed", "generation_failed"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_1234567890abcdef",
    "task_id": "task_9876543210fedcba",
    "status": "queued",
    "estimated_completion_time": "2024-01-12T18:00:00Z",
    "queue_position": 5,
    "track_preview": {
      "title": "Neon Dreams",
      "estimated_duration": 180,
      "formats": ["wav", "mp3", "midi"]
    }
  },
  "message": "Music generation queued successfully"
}
```

#### 1.2 Generate Music from Template
**POST** `/ai/generate-from-template`

Generate music using a predefined template with optional customizations.

**Request Body:**
```json
{
  "template_id": "ai_template_001",
  "customizations": {
    "tempo": 125,
    "key": "D_minor",
    "duration": 240,
    "lyrics": {
      "theme": "digital_love"
    }
  },
  "metadata": {
    "title": "Custom Synthwave Track",
    "tags": ["custom", "synthwave", "ai_generated"]
  }
}
```

**Response:** Same as 1.1

#### 1.3 Generate Batch of Variations
**POST** `/ai/generate-batch`

Generate multiple variations of a track with different parameters.

**Request Body:**
```json
{
  "base_parameters": {
    "genre": "electronic",
    "subgenre": "house",
    "mood": "energetic",
    "tempo": 122
  },
  "variations": [
    {
      "variation_id": "var_1",
      "customizations": {
        "key": "C_major",
        "instrumental": true
      }
    },
    {
      "variation_id": "var_2",
      "customizations": {
        "key": "F_minor",
        "lyrics": {
          "enabled": true,
          "theme": "club_night"
        }
      }
    },
    {
      "variation_id": "var_3",
      "customizations": {
        "tempo": 128,
        "complexity": "high"
      }
    }
  ],
  "batch_settings": {
    "concurrent_generations": 2,
    "notify_when_all_complete": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_1234567890abcdef",
    "generation_ids": [
      "gen_1111111111111111",
      "gen_2222222222222222",
      "gen_3333333333333333"
    ],
    "status": "processing",
    "completed": 0,
    "total": 3
  },
  "message": "Batch generation started successfully"
}
```

#### 1.4 Generate Playlist
**POST** `/ai/generate-playlist`

Generate a cohesive playlist of multiple tracks.

**Request Body:**
```json
{
  "playlist_config": {
    "name": "Chill Study Session",
    "description": "A playlist of lo-fi beats for focused studying",
    "total_duration": 1800,  // 30 minutes
    "track_count": 6,
    "cohesion_level": "high",  // low, medium, high
    "transition_style": "smooth"  // abrupt, smooth, crossfade
  },
  "base_parameters": {
    "genre": "lofi",
    "mood": "calm",
    "tempo_range": [75, 90],
    "complexity": "low"
  },
  "track_variations": {
    "allow_key_changes": true,
    "allow_tempo_variation": 5,  // ±5 BPM
    "allow_instrumentation_variation": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "playlist_id": "playlist_1234567890abcdef",
    "generation_ids": [
      "gen_aaaaaaaaaaaaaaaa",
      "gen_bbbbbbbbbbbbbbbb",
      "gen_cccccccccccccccc",
      "gen_dddddddddddddddd",
      "gen_eeeeeeeeeeeeeeee",
      "gen_ffffffffffffffff"
    ],
    "estimated_completion_time": "2024-01-12T18:30:00Z",
    "track_order": [1, 2, 3, 4, 5, 6]
  },
  "message": "Playlist generation started successfully"
}
```

### 2. Generation Status & Management

#### 2.1 Get Generation Status
**GET** `/ai/generations/{generation_id}`

Get the status of a specific generation.

**Response:**
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_1234567890abcdef",
    "status": "processing",  // queued, processing, completed, failed, cancelled
    "progress": 65,  // percentage
    "estimated_time_remaining": 120,  // seconds
    "started_at": "2024-01-12T17:55:00Z",
    "updated_at": "2024-01-12T17:56:00Z",
    "completed_at": null,
    "track_preview": {
      "title": "Neon Dreams",
      "duration": 180,
      "formats_available": ["mp3"],
      "formats_processing": ["wav", "midi"]
    },
    "quality_metrics": {
      "melodic_coherence": 0.85,
      "harmonic_consistency": 0.92,
      "audio_quality": 0.88
    }
  },
  "message": "Generation status retrieved successfully"
}
```

#### 2.2 List User Generations
**GET** `/ai/generations`

List all generations for the authenticated user.

**Query Parameters:**
- `status`: Filter by status (queued, processing, completed, failed, cancelled)
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `sort_by`: Sort field (created_at, updated_at, duration)
- `sort_order`: Sort order (asc, desc)

**Response:**
```json
{
  "success": true,
  "data": {
    "generations": [
      {
        "generation_id": "gen_1234567890abcdef",
        "title": "Neon Dreams",
        "status": "completed",
        "duration": 180,
        "genre": "electronic",
        "created_at": "2024-01-12T17:55:00Z",
        "completed_at": "2024-01-12T18:00:00Z",
        "formats_available": ["wav", "mp3", "midi"],
        "preview_url": "https://cdn.example.com/preview/gen_123.mp3"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    },
    "summary": {
      "total_generations": 45,
      "completed": 38,
      "processing": 5,
      "failed": 2
    }
  },
  "message": "Generations retrieved successfully"
}
```

#### 2.3 Cancel Generation
**POST** `/ai/generations/{generation_id}/cancel`

Cancel a queued or processing generation.

**Response:**
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_1234567890abcdef",
    "previous_status": "processing",
    "new_status": "cancelled",
    "cancelled_at": "2024-01-12T17:57:00Z"
  },
  "message": "Generation cancelled successfully"
}
```

#### 2.4 Retry Failed Generation
**POST** `/ai/generations/{generation_id}/retry`

Retry a failed generation with same parameters.

**Response:**
```json
{
  "success": true,
  "data": {
    "original_generation_id": "gen_1234567890abcdef",
    "new_generation_id": "gen_new1234567890abc",
    "status": "queued"
  },
  "message": "Generation retry queued successfully"
}
```

### 3. Track Management

#### 3.1 Get Generated Track
**GET** `/ai/tracks/{track_id}`

Get details and download links for a generated track.

**Response:**
```json
{
  "success": true,
  "data": {
    "track_id": "track_1234567890abcdef",
    "generation_id": "gen_1234567890abcdef",
    "title": "Neon Dreams",
    "description": "A cyberpunk synthwave track for nighttime driving",
    "metadata": {
      "genre": "electronic",
      "subgenre": "synthwave",
      "mood": "nostalgic",
      "tempo": 120,
      "key": "C_minor",
      "duration": 180.5,
      "instrumental": false,
      "has_lyrics": true,
      "lyric_language": "en",
      "lyric_theme": "cyberpunk_city"
    },
    "audio_files": [
      {
        "format": "wav",
        "url": "https://cdn.example.com/tracks/track_123.wav",
        "size_bytes": 42345678,
        "bit_depth": 24,
        "sample_rate": 44100,
        "duration": 180.5
      },
      {
        "format": "mp3",
        "url": "https://cdn.example.com/tracks/track_123.mp3",
        "size_bytes": 8456789,
        "bitrate_kbps": 320,
        "duration": 180.5
      },
      {
        "format": "midi",
        "url": "https://cdn.example.com/tracks/track_123.mid",
        "size_bytes": 123456,
        "track_count": 8
      }
    ],
    "stems": [
      {
        "stem_id": "stem_1234567890abcdef",
        "name": "Drums",
        "format": "wav",
        "url": "https://cdn.example.com/stems/stem_123_drums.wav"
      },
      {
        "stem_id": "stem_2234567890abcdef",
        "name": "Bass",
        "format": "wav",
        "url": "https://cdn.example.com/stems/stem_123_bass.wav"
      }
    ],
    "lyrics": {
      "text": "Neon lights reflect on rain-slicked streets...",
      "formatted": "[Verse 1]\nNeon lights reflect on rain-slicked streets\nDigital dreams and electric beats...",
      "timestamps": [
        {"start": 0.0, "end": 15.5, "text": "Neon lights reflect..."},
        {"start": 15.5, "end": 31.0, "text": "Digital dreams and..."}
      ]
    },
    "chord_chart": {
      "url": "https://cdn.example.com/charts/track_123.pdf",
      "formats": ["pdf", "musicxml"]
    },
    "quality_metrics": {
      "melodic_coherence": 0.85,
      "harmonic_consistency": 0.92,
      "rhythmic_stability": 0.88,
      "audio_fidelity": 0.95,
      "overall_quality": 0.90
    },
    "created_at": "2024-01-12T18:00:00Z",
    "expires_at": "2025-01-12T18:00:00Z",  // 1 year retention
    "download_count": 3,
    "play_count": 15
  },
  "message": "Track details retrieved successfully"
}
```

#### 3.2 Download Track
**GET** `/ai/tracks/{track_id}/download`

Download a specific format of a generated track.

**Query Parameters:**
- `format`: Audio format (wav, mp3, flac, ogg, midi)
- `stem`: Optional stem name (drums, bass, melody, vocals)

**Response:** Binary audio file with appropriate Content-Type headers.

#### 3.3 Delete Track
**DELETE** `/ai/tracks/{track_id}`

Delete a generated track and all associated files.

**Response:**
```json
{
  "success": true,
  "data": {
    "track_id": "track_1234567890abcdef",
    "deleted": true,
    "deleted_at": "2024-01-12T18:05:00Z",
    "files_deleted": 5
  },
  "message": "Track deleted successfully"
}
```

#### 3.4 Update Track Metadata
**PATCH** `/ai/tracks/{track_id}`

Update track metadata (title, description, tags).

**Request Body:**
```json
{
  "title": "Updated Track Title",
  "description": "Updated description",
  "tags": ["updated", "synthwave", "cyberpunk"],
  "is_public": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "track_id": "track_1234567890abcdef",
    "updated_fields": ["title", "description", "tags", "is_public"],
    "updated_at": "2024-01-12T18:06:00Z"
  },
  "message": "Track metadata updated successfully"
}
```

### 4. Template Management

#### 4.1 List AI Templates
**GET** `/ai/templates`

List available AI generation templates.

**Query Parameters:**
- `category`: Filter by category
- `subcategory`: Filter by subcategory
- `search`: Search in name/description
- `ai_model`: Filter by compatible AI model
- `has_lyrics`: Filter templates with lyric support

**Response:**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "template_id": "ai_template_001",
        "name": "AI Synthwave Generator",
        "description": "Generates original synthwave tracks with AI",
        "category": "electronic",
        "subcategory": "synthwave",
        "ai_model": "kie_v4",
        "has_lyrics": true,
        "popularity": 92,
        "preview_url": "https://cdn.example.com/template_previews/ai_001.mp3"
      }
    ],
    "categories": [
      {"name": "electronic", "count": 15},
      {"name": "rock", "count": 8},
      {"name": "ambient", "count": 6}
    ],
    "total_templates": 45
  },
  "message": "Templates retrieved successfully"
}
```

#### 4.2 Get Template Details
**GET** `/