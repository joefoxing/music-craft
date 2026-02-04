# User Input Parameters Specification for AI Music Generation System

## Overview
This document defines the comprehensive set of user input parameters for generating original, royalty-free music tracks using AI. The parameters are organized into logical categories and include validation rules, default values, and usage examples.

## Parameter Categories

### 1. Core Musical Parameters

#### 1.1 Genre Selection
**Parameter**: `genre`
- **Type**: String (enum)
- **Required**: Yes
- **Default**: "electronic"
- **Options**:
  - `electronic` - Electronic music (synthwave, house, techno, etc.)
  - `rock` - Rock music (alternative, indie, classic, etc.)
  - `pop` - Pop music (contemporary, synth-pop, etc.)
  - `hiphop` - Hip-hop and rap
  - `jazz` - Jazz (traditional, fusion, smooth, etc.)
  - `classical` - Classical and orchestral
  - `ambient` - Ambient and atmospheric
  - `lofi` - Lo-fi and chill beats
  - `reggae` - Reggae and dub
  - `country` - Country and folk
  - `metal` - Metal and hard rock
  - `world` - World music and ethnic
  - `custom` - User-defined genre

#### 1.2 Subgenre Specification
**Parameter**: `subgenre`
- **Type**: String
- **Required**: No (genre-dependent)
- **Examples by genre**:
  - Electronic: `synthwave`, `house`, `techno`, `dubstep`, `trance`, `drum_and_bass`
  - Rock: `alternative`, `indie`, `classic_rock`, `punk`, `progressive`
  - Pop: `synth_pop`, `indie_pop`, `electro_pop`, `dream_pop`
  - Jazz: `smooth_jazz`, `fusion`, `bebop`, `swing`

#### 1.3 Mood/Emotion
**Parameter**: `mood`
- **Type**: String (enum)
- **Required**: Yes
- **Default**: "neutral"
- **Options**:
  - `happy` - Upbeat, joyful, positive
  - `sad` - Melancholic, emotional, introspective
  - `energetic` - High-energy, driving, intense
  - `calm` - Peaceful, relaxed, soothing
  - `mysterious` - Mysterious, suspenseful, enigmatic
  - `romantic` - Romantic, loving, passionate
  - `epic` - Grand, cinematic, powerful
  - `dreamy` - Dream-like, ethereal, floating
  - `aggressive` - Aggressive, angry, intense
  - `playful` - Playful, fun, whimsical

#### 1.4 Tempo (BPM)
**Parameter**: `tempo`
- **Type**: Integer or String
- **Required**: No
- **Default**: Genre-appropriate tempo
- **Range**: 40-240 BPM
- **String options**: `slow` (60-80), `medium` (90-120), `fast` (130-160), `very_fast` (170+)

#### 1.5 Musical Key
**Parameter**: `key`
- **Type**: String
- **Required**: No
- **Default**: "auto" (AI determines optimal key)
- **Format**: `[Note][Accidental][Mode]`
  - Note: C, D, E, F, G, A, B
  - Accidental: `#` (sharp), `b` (flat), or empty
  - Mode: `major` or `minor`
- **Examples**: `C_major`, `A_minor`, `F#_minor`, `Gb_major`

#### 1.6 Duration
**Parameter**: `duration`
- **Type**: Integer (seconds) or String
- **Required**: No
- **Default**: 180 (3 minutes)
- **Range**: 30-600 seconds (30 seconds to 10 minutes)
- **String options**: `short` (30-60s), `medium` (2-3min), `long` (4-5min), `extended` (6-10min)

### 2. Instrumentation & Arrangement

#### 2.1 Primary Instruments
**Parameter**: `primary_instruments`
- **Type**: Array of Strings
- **Required**: No
- **Default**: Genre-appropriate
- **Examples**:
  - `["electric_guitar", "drums", "bass"]` (Rock)
  - `["synth_bass", "drum_machine", "arpeggiator"]` (Electronic)
  - `["piano", "upright_bass", "drums"]` (Jazz)
  - `["strings", "brass", "timpani"]` (Orchestral)

#### 2.2 Instrumentation Style
**Parameter**: `instrumentation_style`
- **Type**: String (enum)
- **Required**: No
- **Options**:
  - `acoustic` - Natural acoustic instruments
  - `electronic` - Synthesizers and electronic sounds
  - `hybrid` - Mix of acoustic and electronic
  - `orchestral` - Full orchestra
  - `minimal` - Sparse, minimal instrumentation
  - `dense` - Rich, layered instrumentation

#### 2.3 Arrangement Structure
**Parameter**: `structure`
- **Type**: Object or String
- **Required**: No
- **Default**: Genre-appropriate structure
- **String options**: `verse_chorus`, `progressive`, `ambient`, `through_composed`
- **Object format**:
```json
{
  "has_intro": true,
  "has_verse": true,
  "has_chorus": true,
  "has_bridge": false,
  "has_outro": true,
  "sections": [
    {"type": "intro", "duration": 15},
    {"type": "verse", "duration": 30},
    {"type": "chorus", "duration": 30},
    {"type": "verse", "duration": 30},
    {"type": "chorus", "duration": 30},
    {"type": "outro", "duration": 15}
  ]
}
```

#### 2.4 Complexity Level
**Parameter**: `complexity`
- **Type**: String (enum)
- **Required**: No
- **Default**: "medium"
- **Options**:
  - `simple` - Basic chords, simple melody, minimal layers
  - `medium` - Moderate complexity, some layering, standard arrangements
  - `complex` - Rich harmonies, multiple layers, intricate arrangements
  - `very_complex` - Advanced harmonies, counterpoint, sophisticated arrangements

### 3. Lyrical Parameters (Optional)

#### 3.1 Lyrics Enabled
**Parameter**: `lyrics.enabled`
- **Type**: Boolean
- **Required**: No
- **Default**: false

#### 3.2 Lyrical Theme
**Parameter**: `lyrics.theme`
- **Type**: String
- **Required**: If lyrics.enabled is true
- **Examples**:
  - `love` - Romantic love, relationships
  - `nature` - Nature, environment, seasons
  - `technology` - Technology, future, AI
  - `adventure` - Adventure, exploration, journey
  - `introspection` - Self-reflection, emotions, thoughts
  - `social` - Social issues, community, unity
  - `fantasy` - Fantasy, mythology, imagination
  - `urban` - City life, urban experiences

#### 3.3 Language
**Parameter**: `lyrics.language`
- **Type**: String (ISO 639-1 code)
- **Required**: No
- **Default**: "en" (English)
- **Options**: `en`, `es`, `fr`, `de`, `it`, `pt`, `ja`, `ko`, `zh`

#### 3.4 Lyrical Style
**Parameter**: `lyrics.style`
- **Type**: String (enum)
- **Required**: No
- **Default**: "poetic"
- **Options**:
  - `poetic` - Poetic, metaphorical language
  - `conversational` - Natural, conversational tone
  - `narrative` - Storytelling, narrative structure
  - `abstract` - Abstract, non-linear, experimental
  - `direct` - Direct, straightforward expression

#### 3.5 Vocal Characteristics
**Parameter**: `lyrics.vocal_characteristics`
- **Type**: Object
- **Required**: No
- **Properties**:
  - `gender`: `male`, `female`, `neutral`, `mixed`
  - `age`: `young`, `adult`, `mature`, `ageless`
  - `tone`: `warm`, `bright`, `dark`, `neutral`
  - `style`: `pop`, `rock`, `soul`, `opera`, `rap`

### 4. Advanced Musical Parameters

#### 4.1 Harmonic Complexity
**Parameter**: `harmonic_complexity`
- **Type**: String (enum) or Float (0.0-1.0)
- **Required**: No
- **Default**: "medium" (0.5)
- **Options**:
  - `simple` (0.0-0.3): Basic triads, simple progressions
  - `medium` (0.4-0.6): Some extended chords, standard progressions
  - `complex` (0.7-0.8): Jazz chords, modulations, sophisticated progressions
  - `very_complex` (0.9-1.0): Advanced harmony, polytonality, complex modulations

#### 4.2 Rhythmic Feel
**Parameter**: `rhythmic_feel`
- **Type**: String (enum)
- **Required**: No
- **Default**: Genre-appropriate
- **Options**:
  - `straight` - Straight, even rhythms
  - `swing` - Swing feel (jazz, blues)
  - `syncopated` - Syncopated, off-beat emphasis
  - `polyrhythmic` - Multiple rhythmic layers
  - `free` - Free rhythm, rubato

#### 4.3 Dynamic Range
**Parameter**: `dynamic_range`
- **Type**: String (enum)
- **Required**: No
- **Default**: "medium"
- **Options**:
  - `narrow` - Consistent volume throughout
  - `medium` - Moderate volume changes
  - `wide` - Significant dynamic contrast
  - `extreme` - Very quiet to very loud

#### 4.4 Texture Density
**Parameter**: `texture_density`
- **Type**: String (enum) or Integer (1-10)
- **Required**: No
- **Default**: "medium" (5)
- **Options**:
  - `sparse` (1-3): Minimal layers, lots of space
  - `medium` (4-6): Balanced layers, some space
  - `dense` (7-8): Many layers, rich texture
  - `very_dense` (9-10): Maximum layers, complex texture

### 5. AI Model & Generation Parameters

#### 5.1 AI Model Selection
**Parameter**: `ai_model`
- **Type**: String (enum)
- **Required**: No
- **Default**: "kie_v4"
- **Options**:
  - `kie_v4` - Kie API V4 model
  - `suno_v3` - Suno AI V3 model
  - `musiclm` - Google MusicLM
  - `jukebox` - OpenAI Jukebox
  - `ensemble` - Multiple models combined

#### 5.2 Creativity Level
**Parameter**: `creativity`
- **Type**: Float (0.0-1.0)
- **Required**: No
- **Default**: 0.7
- **Description**: Controls how creative/unpredictable the generation is

#### 5.3 Coherence Strength
**Parameter**: `coherence`
- **Type**: Float (0.0-1.0)
- **Required**: No
- **Default**: 0.8
- **Description**: Controls musical coherence and structure preservation

#### 5.4 Genre Adherence
**Parameter**: `genre_adherence`
- **Type**: Float (0.0-1.0)
- **Required**: No
- **Default**: 0.9
- **Description**: How strictly to adhere to genre conventions

### 6. Output & Quality Parameters

#### 6.1 Output Formats
**Parameter**: `output_formats`
- **Type**: Array of Strings
- **Required**: No
- **Default**: `["mp3"]`
- **Options**:
  - `wav` - Uncompressed WAV (high quality)
  - `mp3` - Compressed MP3 (web-friendly)
  - `flac` - Lossless FLAC
  - `ogg` - OGG Vorbis
  - `midi` - MIDI file (note data)
  - `stems` - Separate audio stems
  - `project` - DAW project file

#### 6.2 Audio Quality
**Parameter**: `audio_quality`
- **Type**: String (enum)
- **Required**: No
- **Default**: "high"
- **Options**:
  - `low` - 128kbps MP3, 16-bit/44.1kHz WAV
  - `medium` - 192kbps MP3, 16-bit/48kHz WAV
  - `high` - 320kbps MP3, 24-bit/48kHz WAV
  - `studio` - 24-bit/96kHz WAV, lossless formats

#### 6.3 Mastering Preset
**Parameter**: `mastering_preset`
- **Type**: String (enum)
- **Required**: No
- **Default**: "balanced"
- **Options**:
  - `raw` - No mastering, dry output
  - `balanced` - Balanced mastering for general use
  - `radio_ready` - Optimized for radio/streaming
  - `cinematic` - Wide dynamic range for film/TV
  - `club` - Loud, compressed for club playback

### 7. Template-Based Parameters

#### 7.1 Template ID
**Parameter**: `template_id`
- **Type**: String
- **Required**: No
- **Description**: ID of a predefined template to use as base

#### 7.2 Template Customization
**Parameter**: `template_customizations`
- **Type**: Object
- **Required**: No
- **Description**: Override specific template parameters
- **Example**:
```json
{
  "tempo": 130,
  "key": "D_minor",
  "instrumentation": ["synth_bass", "electric_piano"],
  "lyrics": {
    "theme": "digital_revolution"
  }
}
```

## Parameter Validation Rules

### 1. Range Validation
- Tempo: 40-240 BPM
- Duration: 30-600 seconds
- Float parameters: 0.0-1.0
- Integer parameters: Appropriate ranges per parameter

### 2. Enum Validation
- All enum parameters must match predefined options
- Case-insensitive matching with normalization

### 3. Dependency Validation
- Lyric parameters require `lyrics.enabled: true`
- Subgenre should be compatible with selected genre
- Instrumentation should be compatible with genre/style

### 4. Consistency Validation
- Key should be valid musical key notation
- Duration in seconds should be divisible by musical measures (e.g., multiples of 4 seconds for 120 BPM)
- Output formats should be supported by selected AI model

## Default Parameter Sets

### Quick Start Presets

#### 1. "Synthwave Instrumental"
```json
{
  "genre": "electronic",
  "subgenre": "synthwave",
  "mood": "nostalgic",
  "tempo": 120,
  "duration": 180,
  "instrumental": true,
  "complexity": "medium"
}
```

#### 2. "Lo-fi Study Beats"
```json
{
  "genre": "lofi",
  "mood": "calm",
  "tempo": 85,
  "duration": 180,
  "instrumental": true,
  "primary_instruments": ["piano", "vinyl_crackle", "soft_drums"],
  "texture_density": "sparse"
}
```

#### 3. "Epic Cinematic"
```json
{
  "genre": "classical",
  "mood": "epic",
  "tempo": 130,
  "duration": 150,
  "instrumental": true,
  "primary_instruments": ["strings", "brass", "choir", "timpani"],
  "dynamic_range": "wide"
}
```

#### 4. "Pop Song with Lyrics"
```json
{
  "genre": "pop",
  "mood": "happy",
  "tempo": 128,
  "duration": 210,
  "instrumental": false,
  "lyrics": {
    "enabled": true,
    "theme": "summer_love",
    "language": "en",
    "style": "poetic"
  },
  "structure": "verse_chorus"
}
```

## API Request Examples

### Minimal Request
```json
{
  "genre": "electronic",
  "mood": "energetic"
}
```

### Comprehensive Request
```json
{
  "genre": "rock",
  "subgenre": "alternative",
  "mood": "introspective",
  "tempo": 110,
  "key": "E_minor",
  "duration": 240,
  "primary_instruments": ["electric_guitar", "bass", "drums", "synth_pad"],
  "complexity": "medium",
  "lyrics": {
    "enabled": true,
    "theme": "self_discovery",
    "language": "en",
    "style": "narrative",
    "vocal_characteristics": {
      "gender": "male",
      "age": "adult",
      "tone": "warm"
    }
  },
  "harmonic_complexity": 0.6,
  "dynamic_range": "medium",
  "ai_model": "kie_v