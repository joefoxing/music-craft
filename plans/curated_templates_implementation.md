# 20+ Curated Templates Implementation Plan

## Overview
This plan outlines the creation of 20+ high-quality music generation templates across 6 categories. Each template includes a carefully crafted prompt, style description, metadata, and example references where available.

## 1. Template Categories and Distribution

### Category Breakdown
- **Electronic (6 templates)**: Synthwave, House, Techno, Drum & Bass, Future Bass, Ambient Techno
- **Ambient (4 templates)**: Meditation, Space, Nature, Piano
- **Cinematic (4 templates)**: Trailer, Emotional, Suspense, Fantasy
- **Hip Hop & Lo-fi (3 templates)**: Boom Bap, Jazz Hop, Chill Lo-fi
- **Rock & Metal (2 templates)**: Alternative Rock, Progressive Metal
- **World & Ethnic (2 templates)**: Japanese, African
- **Bonus Templates (2+)**: Experimental, Hybrid genres

**Total: 21+ templates**

## 2. Template Creation Guidelines

### Quality Standards
1. **Prompt Quality**: Each prompt must be 50-200 words, descriptive, and evocative
2. **Style Accuracy**: Style tags must accurately represent the musical genre
3. **Technical Details**: Include BPM, duration, and instrumental settings
4. **Metadata**: Provide generation parameters for consistent results
5. **Example References**: Include example image/audio URLs where possible

### Template Structure Requirements
```json
{
  "id": "template_XXX",
  "name": "Descriptive Name",
  "description": "Brief description (1-2 sentences)",
  "category": "category_id",
  "subcategory": "optional_subcategory",
  "prompt": "Detailed prompt text (50-200 words)",
  "style": "comma-separated style tags",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "bpm": 120,
  "duration": "2:30",
  "instrumental": true,
  "difficulty": "beginner|intermediate|advanced",
  "popularity": 0-100,
  "author": "System",
  "created_at": "2024-01-12",
  "updated_at": "2024-01-12",
  "example_audio_url": "optional_url",
  "example_image_url": "optional_url",
  "metadata": {
    "model": "V4",
    "temperature": 0.8,
    "top_p": 0.95,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1
  }
}
```

## 3. Template Catalog

### Electronic Category (6 templates)

#### 1. Cyberpunk Synthwave
```json
{
  "id": "template_001",
  "name": "Cyberpunk Synthwave",
  "description": "A cyberpunk synthwave track with pulsating bass and nostalgic 80s atmosphere",
  "category": "electronic",
  "subcategory": "synthwave",
  "prompt": "A cyberpunk synthwave track with pulsating basslines, arpeggiated synthesizers, and nostalgic 80s atmosphere. Features driving rhythm, neon-lit cityscape vibes, emotional melodic hooks, and retro-futuristic sound design. The track should evoke feelings of nighttime city driving, rain-slicked streets reflecting neon signs, and a sense of melancholic futurism. Include atmospheric pads, sequenced arpeggios, and a memorable lead melody that tells a story of human connection in a digital world.",
  "style": "synthwave, cyberpunk, 80s, retro-futuristic, atmospheric, driving",
  "tags": ["electronic", "synth", "cyberpunk", "80s", "nostalgic", "driving", "atmospheric"],
  "bpm": 120,
  "duration": "3:15",
  "instrumental": true,
  "difficulty": "beginner",
  "popularity": 95,
  "example_image_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=300&fit=crop"
}
```

#### 2. Deep House Groove
```json
{
  "id": "template_002",
  "name": "Deep House Groove",
  "description": "Smooth deep house with soulful vocals and hypnotic rhythms",
  "category": "electronic",
  "subcategory": "house",
  "prompt": "A deep house track with smooth, hypnotic rhythms, warm basslines, and soulful vocal samples. Create a late-night club atmosphere with atmospheric pads, subtle percussion, and a building energy that maintains a chilled vibe throughout. The track should feature a four-on-the-floor beat, filtered chords, and emotional depth that evokes feelings of connection and movement. Include breakdowns with atmospheric elements and builds that lead to satisfying drops without being overpowering.",
  "style": "deep house, soulful, hypnotic, atmospheric, chilled, groovy",
  "tags": ["electronic", "house", "deep", "soulful", "atmospheric", "groovy", "chilled"],
  "bpm": 122,
  "duration": "4:20",
  "instrumental": false,
  "difficulty": "intermediate",
  "popularity": 88,
  "example_image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=300&fit=crop"
}
```

#### 3. Drum & Bass Energy
```json
{
  "id": "template_003",
  "name": "Drum & Bass Energy",
  "description": "High-energy drum and bass with complex rhythms and atmospheric breaks",
  "category": "electronic",
  "subcategory": "drumandbass",
  "prompt": "An energetic drum and bass track with complex breakbeat rhythms, deep sub-bass, and atmospheric synth pads. Create a sense of urgency and movement with fast-paced percussion, rolling basslines, and ethereal melodic elements. The track should feature intense drops, atmospheric breakdowns, and a driving energy that maintains momentum throughout. Include amen breaks, Reese bass, and cinematic elements that evoke feelings of speed, intensity, and futuristic landscapes.",
  "style": "drum and bass, energetic, atmospheric, complex, futuristic, intense",
  "tags": ["electronic", "drumandbass", "energetic", "atmospheric", "complex", "futuristic"],
  "bpm": 174,
  "duration": "3:45",
  "instrumental": true,
  "difficulty": "advanced",
  "popularity": 82,
  "example_image_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400&h=300&fit=crop"
}
```

#### 4. Lo-fi Study Beats
```json
{
  "id": "template_004",
  "name": "Lo-fi Study Beats",
  "description": "Chill lo-fi hip hop beats perfect for studying or relaxing",
  "category": "electronic",
  "subcategory": "lofi",
  "prompt": "A chill lo-fi hip hop beat with dusty vinyl crackle, relaxed drum patterns, and warm jazz samples. Create a cozy, nostalgic atmosphere perfect for studying, relaxing, or late-night contemplation. The track should feature simple but effective drum programming, melodic piano or guitar loops, and atmospheric textures like rain sounds or ambient noise. Maintain a laid-back vibe with subtle variations and a sense of comforting repetition that supports focus without being distracting.",
  "style": "lo-fi, chill, relaxed, nostalgic, atmospheric, jazzy",
  "tags": ["electronic", "lofi", "chill", "relaxed", "nostalgic", "study", "jazzy"],
  "bpm": 85,
  "duration": "2:30",
  "instrumental": true,
  "difficulty": "beginner",
  "popularity": 92,
  "example_image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&h=300&fit=crop"
}
```

#### 5. Ambient Techno
```json
{
  "id": "template_005",
  "name": "Ambient Techno",
  "description": "Atmospheric techno with deep textures and hypnotic rhythms",
  "category": "electronic",
  "subcategory": "techno",
  "prompt": "An ambient techno track with deep, atmospheric textures, hypnotic rhythms, and evolving soundscapes. Create a meditative yet driving atmosphere with minimal percussion, atmospheric pads, and subtle melodic elements that develop over time. The track should feature a steady four-on-the-floor beat, deep bass frequencies, and atmospheric elements that evoke feelings of vast spaces, introspection, and forward movement. Include gradual builds, atmospheric breakdowns, and a sense of journey rather than traditional song structure.",
  "style": "ambient techno, atmospheric, hypnotic, deep, minimal, evolving",
  "tags": ["electronic", "techno", "ambient", "atmospheric", "hypnotic", "minimal"],
  "bpm": 124,
  "duration": "5:10",
  "instrumental": true,
  "difficulty": "intermediate",
  "popularity": 79,
  "example_image_url": "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?w=400&h=300&fit=crop"
}
```

#### 6. Future Bass Drop
```json
{
  "id": "template_006",
  "name": "Future Bass Drop",
  "description": "Emotional future bass with huge drops and melodic complexity",
  "category": "electronic",
  "subcategory": "futurebass",
  "prompt": "An emotional future bass track with huge supersaw chords, intricate vocal chops, and massive drops. Create a contrast between intimate, melodic verses and explosive, energetic choruses. The track should feature complex sound design, emotional chord progressions, and a sense of cinematic scale. Include pitched vocal samples, glittering arpeggios, and a building energy that leads to satisfying drops with wide stereo imaging and powerful low-end. Evoke feelings of euphoria, nostalgia, and emotional release.",
  "style": "future bass, emotional, cinematic, energetic, melodic, complex",
  "tags": ["electronic", "futurebass", "emotional", "energetic", "melodic", "cinematic"],
  "bpm": 150,
  "duration": "3:30",
  "instrumental": false,
  "difficulty": "advanced",
  "popularity": 86,
  "example_image_url": "https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=300&fit=crop"
}
```

### Ambient Category (4 templates)

#### 7. Calm Meditation
```json
{
  "id": "template_007",
  "name": "Calm Meditation",
  "description": "Soothing ambient music for meditation and relaxation",
  "category": "ambient",
  "subcategory": "meditation",
  "prompt": "A calming ambient track for meditation and relaxation, featuring gentle pads, subtle textures, and slowly evolving soundscapes. Create a sense of peace and stillness with minimal melodic movement, atmospheric drones, and natural sounds like gentle wind or water. The track should promote relaxation and mindfulness with a slow tempo, wide stereo field, and frequencies that encourage deep breathing and mental calm. Avoid sudden changes or dramatic elements, focusing instead on gradual evolution and harmonic warmth.",
  "style": "ambient, calming, meditative, atmospheric, peaceful, evolving",
  "tags": ["ambient", "meditation", "calming", "peaceful", "atmospheric", "relaxing"],
  "bpm": 60,
  "duration": "8:00",
  "instrumental": true,
  "difficulty": "beginner",
  "popularity": 90,
  "example_image_url": "https://images.unsplash.com/photo-1545389336-cf09028c9b04?w=400&h=300&fit=crop"
}
```

#### 8. Space Exploration
```json
{
  "id": "template_008",
  "name": "Space Exploration",
  "description": "Cosmic ambient music evoking the vastness of space",
  "category": "ambient",
  "subcategory": "space",
  "prompt": "A cosmic ambient track evoking the vastness of space, featuring ethereal pads, metallic textures, and slowly drifting melodies. Create a sense of awe and wonder with deep bass drones, glittering high-frequency elements, and atmospheric effects that suggest celestial bodies and interstellar travel. The track should feature minimal rhythmic elements, focusing instead on texture, space, and gradual evolution. Include elements that suggest radio signals, cosmic radiation, and the silent majesty of the universe.",
  "style": "space ambient, cosmic, ethereal, atmospheric, vast, drifting",
  "tags": ["ambient", "space", "cosmic", "ethereal", "atmospheric", "drifting"],
  "bpm": 70,
  "duration": "6:30",
  "instrumental": true,
  "difficulty": "intermediate",
  "popularity": 84,
  "example_image_url": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=300&fit=crop"
}
```

#### 9. Rainy Day Piano
```json
{
  "id": "template_009",
  "name": "Rainy Day Piano",
  "description": "Emotional piano piece with rain sounds and melancholic melodies",
  "category": "ambient",
  "subcategory": "piano",
  "prompt": "An emotional piano piece with melancholic melodies, subtle rain sounds, and atmospheric textures. Create a sense of introspection and gentle sadness with simple but expressive piano phrases, minimal accompaniment, and the sound of gentle rain in the background. The track should feature emotional chord progressions, delicate playing, and a sense of space between notes. Include occasional atmospheric elements like distant thunder or wind to enhance the rainy day atmosphere without overpowering the piano.",
  "style": "piano, emotional, melancholic, atmospheric, rainy, introspective",
  "tags": ["ambient", "piano", "emotional", "melancholic", "rainy", "introspective"],
  "bpm": 75,
  "duration": "3:45",
  "instrumental": true,
  "difficulty": "beginner",
  "popularity": 88,
  "example_image_url": "https://images.unsplash.com/photo-1433162653888-a571db5ccccf?w=400&h=300&fit=crop"
}
```

#### 10. Forest Atmosphere
```json
{
  "id": "template_010",
  "name": "Forest Atmosphere",
  "description": "Nature-inspired ambient with forest sounds and organic textures",
  "category": "ambient",
  "subcategory": "nature",
  "prompt": "A nature-inspired ambient track featuring forest sounds, organic textures, and earthy musical elements. Create a sense of being deep in a forest with bird songs, rustling leaves, flowing water, and gentle wind. The musical elements should complement rather than dominate, with wooden percussion, breathy flutes, and earthy drones. The track should evolve slowly, mimicking natural processes and creating a immersive soundscape that promotes connection with nature and environmental awareness.",
  "style": "nature ambient, organic, earthy, atmospheric, forest, immersive",
  "tags": ["ambient", "nature", "forest", "organic", "earthy", "immersive"],
  "bpm": 65,
  "duration": "7:15",
  "instrumental": true,
  "difficulty": "intermediate",
  "popularity": 81,
  "example_image_url": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=400&h=300&fit=crop"
}
```

### Cinematic Category (4 templates)

#### 11. Epic Trailer Music
```json
{
  "id": "template_011",
  "name": "Epic Trailer Music",
  "description": "Powerful orchestral music for movie trailers and epic scenes",
  "category": "cinematic",
  "subcategory": "trailer",
  "prompt": "Epic trailer music featuring powerful orchestral arrangements, massive percussion, and building tension. Create a sense of grandeur and drama with full orchestra, choir, and modern hybrid elements. The track should follow classic trailer structure: mysterious opening, building tension, emotional middle section, and explosive finale. Include brass fanfares, string ostinatos, taiko drums, and cinematic sound design that evokes blockbuster movies, heroic journeys, and world-changing events.",
  "style": "epic, orchestral, cinematic, powerful, dramatic, trailer",
  "tags": ["cinematic", "orchestral", "epic", "dramatic", "trailer", "powerful"],
  "bpm": 130,
  "duration": "2:45",
  "instrumental": false,
  "difficulty": "advanced",
  "popularity": 93,
  "example_image_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=400&h=300&fit=crop"
}
```

#### 12. Emotional Piano Score
```json
{
  "id": "template_012",
  "name": "Emotional Piano Score",
  "description": "Heartfelt piano music for emotional film scenes",
  "category": "cinematic",
  "subcategory": "emotional",
  "prompt": "An emotional piano score for heartfelt film scenes, featuring expressive melodies, subtle string accompaniment, and cinematic atmosphere. Create a sense of intimacy and emotional depth with delicate piano playing, emotional chord progressions, and minimal orchestral support. The track should evoke feelings of love, loss, memory, or personal transformation. Include space for emotional expression, dynamic variation, and a narrative arc that supports visual storytelling without being overly dramatic or sentimental.",
