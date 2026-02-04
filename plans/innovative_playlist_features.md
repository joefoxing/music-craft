# Innovative Generative AI Playlist Features Specification

This document outlines the technical specification for four innovative AI-driven features designed to transform the playlist experience from a static list of songs into a dynamic, generative audio journey.

## 1. Prompt-to-Playlist (Narrative Generation)

**Concept:**
Instead of generating single tracks, users define a high-level "Narrative" or "Vibe" (e.g., "A cyberpunk detective exploring a rainy neon city, leading to a high-speed chase"), and the system generates a sequence of coherent tracks that evolve to tell that story.

### User Experience
1.  **Input:** User provides a master prompt (text) and selects a playlist length (e.g., 5 tracks, 15 minutes).
2.  **Blueprint Preview:** The system uses an LLM to break the master prompt into a "Playlist Blueprint"—a sequence of track descriptions (e.g., "Track 1: Atmospheric rain, slow synth jazz", "Track 2: Suspense building, faster bassline", "Track 3: Full chase, high BPM").
3.  **Generation:** User approves/edits the blueprint, and the system triggers batch generation.
4.  **Result:** A new playlist is created where tracks flow logically into one another.

### Technical Architecture
*   **Blueprint Engine (LLM):**
    *   Input: User Prompt + Duration.
    *   Process: Chain-of-Thought prompting to decompose the narrative into `N` segments.
    *   Output: JSON array of Track Prompts, each with specific `bpm`, `key`, `mood`, and `instrumentation` params to ensure cohesion.
*   **Batch Orchestrator:**
    *   Extends the `MusicGenerationService` to handle `BatchRequest` objects.
    *   Parallel or sequential processing (sequential allows passing the end-state of Track N as the "init_audio" or context for Track N+1 for better continuity).
*   **UI Components:**
    *   `PlaylistGeneratorModal`: Input for master prompt.
    *   `BlueprintTimeline`: Visual representation of the generated track arc before audio generation starts.

### Integration Points
*   **Entry Point:** "Create Smart Playlist" button in `SongLibrary`.
*   **Data Model:** New `PlaylistGenerationJob` model to track the status of the multi-track generation.

---

## 2. Infinite Contextual Extension (The "Forever" Vibe)

**Concept:**
A playlist that never ends. When the user reaches the last track, the system analyzes the musical context of the recent tracks and generates a new one that perfectly continues the vibe, effectively creating an infinite radio station tailored to the current listening session.

### User Experience
1.  **Activation:** User toggles "Infinite Mode" on any active playlist.
2.  **Trigger:** When the playback queue has < 2 tracks remaining.
3.  **Generation:** System silently generates the next track in the background.
4.  **Playback:** The new track is appended to the queue seamlessly.

### Technical Architecture
*   **Context Analyzer:**
    *   Input: Last 3 tracks in the playlist.
    *   Analysis: Extract metadata (BPM, Key, Genre Tags) and, if available, audio feature embeddings.
*   **Continuation Logic:**
    *   **Strict Mode:** Keeps same BPM/Key/Genre.
    *   **Drift Mode:** Slowly evolves parameters (e.g., increase BPM by 5% every track) to prevent monotony.
*   **Prompt Engineering:**
    *   Constructs a prompt: "Generate a track similar to [Track N] but with elements of [Track N-1]. Maintain energy level."
    *   Uses `continuation_audio` (if supported by model) using the last 10s of the previous track to ensure seamless audio splicing.

### Integration Points
*   **Audio Player:** `AudioPlayer` component needs an `onQueueLow` event listener.
*   **Backend:** New API endpoint `/api/generate/continuation`.

---

## 3. Stem-Based Mixing (Smart Crossfade)

**Concept:**
AI-driven "DJ" transitions. Instead of a simple volume crossfade, the system mixes the *stems* (separated instrument tracks) of the outgoing and incoming songs. For example, keeping the drums of Track A playing while the melody of Track B fades in, or swapping the basslines.

### User Experience
1.  **Playback:** User listens to a playlist.
2.  **Transition:** As Track A ends, its melody/vocals fade out, but its drums continue. Track B's melody fades in over Track A's drums. Then Track A's drums fade out as Track B's drums kick in.
3.  **Visuals:** The player UI visualizes the "Handoff" between tracks.

### Technical Architecture
*   **Stem Separation Pipeline:**
    *   Since raw generation often yields a flat mix, we integrate a source separation model (e.g., Demucs or Spleeter) running server-side (or via WebAssembly if feasible for performance).
    *   *Optimization:* Pre-process stems for tracks in "Smart Playlists" rather than real-time.
*   **Mixing Engine (Web Audio API):**
    *   The frontend `AudioPlayer` becomes a multi-track mixer.
    *   It loads 4 AudioBuffers (Track A Stems, Track B Stems).
    *   Applies volume automation curves based on a "Transition Template" (e.g., "Bass Swap", "Vocal Handoff", "Percussion Bridge").
*   **Beat Matching (Critical):**
    *   System must detect BPM/Grid.
    *   Apply `playbackRate` adjustment to align Track B's BPM to Track A during the transition.

### Integration Points
*   **Storage:** Stems need to be stored alongside the main audio file (e.g., `song_id/stems/drums.mp3`).
*   **Player UI:** Enhanced player with stem visualization/controls.

---

## 4. Smart Playlist Templating

**Concept:**
A structural blueprint system that allows users to define or select a "Skeleton" for a playlist. Unlike "Prompt-to-Playlist" which generates the structure from text, Templating applies a pre-defined mathematical or logical structure to the generation process (e.g., "BPM Ramp-Up" or "Hero's Journey").

### User Experience
1.  **Template Selection:** In the Library, users browse a "Playlist Templates" tab.
2.  **Configuration:** User selects a template (e.g., "Workout Ramp-Up") and provides a "Base Theme" (e.g., "90s House").
3.  **Preview:** The system shows the calculated parameters for each track (e.g., Track 1: 120 BPM, Track 2: 124 BPM, Track 3: 128 BPM).
4.  **Customization:** Users can "fork" a template to adjust the curves or constraints.

### Template Data Structure (JSON Schema)
The templates use a node-based architecture where parameters can be absolute, relative (to previous track), or interpolated (start to end).

```json
{
  "id": "workout_ramp_up_30m",
  "name": "High Intensity Interval Ramp",
  "description": "A 30-minute mix that starts steady and builds to a high-intensity peak.",
  "total_tracks": 6,
  "nodes": [
    {
      "position": 0,
      "role": "Warmup",
      "constraints": {
        "bpm": { "mode": "absolute", "value": 110 },
        "energy": { "mode": "absolute", "value": 0.4 },
        "prompt_suffix": "steady rhythm, warmup vibe"
      }
    },
    {
      "position": 1,
      "role": "Build",
      "constraints": {
        "bpm": { "mode": "relative", "operation": "add", "value": 5 },
        "energy": { "mode": "relative", "operation": "add", "value": 0.1 }
      }
    },
    {
      "position": 2, // ... implied interpolation logic could be used here ...
      "role": "Steady State",
      "constraints": {
        "bpm": { "mode": "linear_interpolate", "target": 128, "steps_remaining": 3 }
      }
    },
    {
      "position": 5,
      "role": "Cool Down",
      "constraints": {
        "bpm": { "mode": "absolute", "value": 100 },
        "energy": { "mode": "absolute", "value": 0.3 },
        "prompt_suffix": "ambient, relaxing, cool down"
      }
    }
  ],
  "global_constraints": {
    "key_consistency": "camelot_wheel_mixing", // Logic to ensure harmonically compatible keys
    "genre_lock": true // Forces all tracks to adhere to the user's base genre selection
  }
}
```

### Constraint Application Mechanism
1.  **Queue Pre-processor:** When a template is instantiated:
    *   The "Base Theme" (user input) acts as the `root_prompt`.
    *   The system iterates through `nodes` in the JSON schema.
    *   **Resolution Step:** It resolves relative values (e.g., `prev_bpm + 5`) and interpolations.
2.  **Job Creation:** It generates a list of `GenerationTask` objects, each with fixed parameters derived from the resolution step.
3.  **Dependency Handling:** If `key_consistency` is enabled, Track N+1's generation might be paused until Track N is completed to detect its actual Key (if not strictly enforceable via prompt).

### UI Flow
*   **Library Interface:**
    *   New Tab: `Playlist Templates`.
    *   Grid view of "Blueprints" (Cards showing a visual curve of BPM/Energy).
*   **Template Editor (Advanced):**
    *   A "Node Graph" or "Timeline" editor where users can drag points on a BPM/Energy curve to create custom templates.
    *   "Save as User Template" option.

---

## Implementation Roadmap

### Phase 1: Prompt-to-Playlist & Smart Templating (MVP)
*   Build the `Blueprint Engine` (Prompt Engineering).
*   Implement the `TemplateService` to parse the JSON schema and resolve constraints.
*   Create the "Create Smart Playlist" UI with Template selection.
*   Implement Batch Generation in backend.

### Phase 2: Infinite Extension
*   Implement "Queue Monitoring" in frontend.
*   Create `Context Analyzer` logic.
*   Connect to generation endpoint.

### Phase 3: Stem Mixing (Advanced)
*   Integrate Demucs (Python) for server-side separation.
*   Refactor `AudioPlayer` to handle multi-channel/stem playback.
*   Implement basic beat-matching logic in JS.
