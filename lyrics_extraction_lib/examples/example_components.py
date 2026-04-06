"""
Example 4: Using Individual Pipeline Components
Low-level API for custom workflows
"""
from lyrics_extraction.pipeline import separate, transcribe, postprocess, utils
import tempfile

def component_usage():
    """Demonstrate using individual pipeline components."""
    
    audio_file = "sample_song.mp3"
    
    with utils.TempFileManager() as temp_dir:
        print("Step 1: Preprocessing Audio")
        preprocessed = f"{temp_dir}/preprocessed.wav"
        if utils.preprocess_audio_ffmpeg(audio_file, preprocessed):
            current_audio = preprocessed
            print(f"  ✓ Preprocessed audio: {preprocessed}")
        else:
            current_audio = audio_file
            print(f"  ✗ Preprocessing failed, using original")
        
        print("\nStep 2: Vocal Separation")
        try:
            vocal_stem = separate.separate_vocals(
                current_audio,
                f"{temp_dir}/demucs_output",
                device="cpu"
            )
            if vocal_stem:
                current_audio = vocal_stem
                print(f"  ✓ Vocal separation successful")
            else:
                print(f"  ✗ Vocal separation failed, continuing with current audio")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print("\nStep 3: Audio Duration Check")
        duration = utils.get_audio_duration(current_audio)
        print(f"  Duration: {duration:.1f} seconds")
        
        print("\nStep 4: Transcription")
        transcriber = transcribe.LyricsTranscriber(
            model_size="base",  # Small model for demo
            device="cpu"
        )
        
        trans_result = transcriber.transcribe(
            current_audio,
            language="auto",
            word_timestamps=True
        )
        
        print(f"  ✓ Transcription complete")
        print(f"  Segments: {len(trans_result['segments'])}")
        print(f"  Language: {trans_result['language']}")
        print(f"  Raw text length: {len(trans_result['text'])} chars")
        
        print("\nStep 5: Post-Processing")
        post_result = postprocess.postprocess_lyrics(
            segments=trans_result['segments'],
            include_word_timestamps=True,
            deduplicate=True
        )
        
        print(f"  ✓ Post-processing complete")
        print(f"  Language detected: {post_result['language_detected']}")
        print(f"  Final lyrics length: {len(post_result['lyrics'])} chars")
        
        print("\n=== Final Lyrics ===")
        print(post_result['lyrics'][:300] + "...")
        
        if post_result['words']:
            print(f"\n=== First 10 Words with Timestamps ===")
            for word in post_result['words'][:10]:
                print(f"  {word['word']:15} {word['start']:6.2f}s - {word['end']:6.2f}s")


if __name__ == "__main__":
    component_usage()
