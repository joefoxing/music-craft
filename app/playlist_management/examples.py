"""
Comprehensive Usage Examples for Playlist Management System

This file demonstrates various features and use cases of the playlist management system,
including basic operations, advanced features, and integration examples.
"""

import os
import tempfile
from datetime import datetime, timedelta
from app.playlist_management import (
    create_playlist_manager, 
    create_song, 
    create_playlist,
    InMemoryStorage,
    FileStorage,
    DuplicateSongError,
    PlaylistExistsError
)
from app.playlist_management.song import Song
from app.playlist_management.playlist import Playlist


def example_basic_operations():
    """Demonstrate basic playlist and song operations."""
    print("=== Basic Operations Example ===")
    
    # Create playlist manager
    manager = create_playlist_manager(storage_type='memory')
    
    # Create a playlist
    playlist = manager.create_playlist(
        name="My Rock Collection",
        description="A collection of my favorite rock songs",
        tags=['rock', 'favorites', 'classic'],
        is_public=True
    )
    print(f"Created playlist: {playlist.metadata.name}")
    
    # Create songs
    songs = [
        create_song(
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            duration=355,
            genre="Rock"
        ),
        create_song(
            title="Stairway to Heaven",
            artist="Led Zeppelin",
            album="Led Zeppelin IV",
            duration=483,
            genre="Rock"
        ),
        create_song(
            title="Hotel California",
            artist="Eagles",
            album="Hotel California",
            duration=391,
            genre="Rock"
        )
    ]
    
    # Add songs to playlist
    for song in songs:
        manager.add_song_to_playlist(playlist.playlist_id, song)
        print(f"Added song: {song.display_name}")
    
    # Display playlist info
    print(f"Playlist has {len(playlist)} songs")
    print(f"Total duration: {playlist.get_total_duration_formatted()}")
    
    return manager, playlist


def example_search_and_filtering():
    """Demonstrate search and filtering capabilities."""
    print("\n=== Search and Filtering Example ===")
    
    manager, playlist = example_basic_operations()
    
    # Search for songs
    queen_songs = manager.search_songs_across_playlists('Queen')
    print(f"Found {len(queen_songs)} playlists with 'Queen' songs")
    
    for playlist_id, songs in queen_songs.items():
        for song in songs:
            print(f"  - {song.display_name}")
    
    # Filter by genre within playlist
    print("\nFiltering songs by genre within playlist:")
    rock_songs = playlist.filter_songs_by_genre('Rock')
    for song in rock_songs:
        print(f"  - {song.display_name}")
    
    # Search playlists
    manager.create_playlist(name="Jazz Collection", tags=['jazz'], description="Jazz favorites")
    manager.create_playlist(name="Pop Hits", tags=['pop'], description="Popular pop songs")
    
    rock_playlists = manager.find_playlists_by_tag('rock')
    print(f"\nFound {len(rock_playlists)} playlists with 'rock' tag")
    
    for pl in rock_playlists:
        print(f"  - {pl.metadata.name}: {pl.metadata.description}")


def example_playlist_management():
    """Demonstrate playlist CRUD operations."""
    print("\n=== Playlist Management Example ===")
    
    manager = create_playlist_manager(storage_type='memory')
    
    # Create multiple playlists
    playlists = []
    for i in range(3):
        playlist = manager.create_playlist(
            name=f"Playlist {i+1}",
            description=f"Description for playlist {i+1}",
            tags=[f'tag{i+1}', 'demo']
        )
        playlists.append(playlist)
        print(f"Created: {playlist.metadata.name}")
    
    # List all playlists
    all_playlists = manager.list_playlists()
    print(f"\nTotal playlists: {len(all_playlists)}")
    
    # Update a playlist
    playlist_to_update = playlists[0]
    manager.update_playlist(
        playlist_to_update.playlist_id,
        name="Updated Playlist 1",
        description="Updated description"
    )
    print(f"Updated playlist name to: {manager.get_playlist(playlist_to_update.playlist_id).metadata.name}")
    
    # Delete a playlist
    playlist_to_delete = playlists[2]
    result = manager.delete_playlist(playlist_to_delete.playlist_id)
    print(f"Deleted playlist: {result}")
    
    # Verify deletion
    remaining_playlists = manager.list_playlists()
    print(f"Remaining playlists: {len(remaining_playlists)}")


def example_advanced_song_management():
    """Demonstrate advanced song management features."""
    print("\n=== Advanced Song Management Example ===")
    
    manager, playlist = example_basic_operations()
    
    # Add more songs for demonstration
    additional_songs = [
        create_song(title="Sweet Child O' Mine", artist="Guns N' Roses", genre="Rock"),
        create_song(title="Nothing Else Matters", artist="Metallica", genre="Metal"),
        create_song(title="Bohemian Rhapsody", artist="Queen", duration=355, genre="Rock")  # Duplicate
    ]
    
    # Add songs
    for song in additional_songs:
        try:
            manager.add_song_to_playlist(playlist.playlist_id, song)
            print(f"Added: {song.display_name}")
        except DuplicateSongError:
            print(f"Skipped duplicate: {song.display_name}")
    
    # Update a song
    first_song = playlist.read_songs()[0]
    playlist.update_song(first_song, {
        'title': f"{first_song.title} (Remastered)",
        'genre': 'Classic Rock'
    })
    print(f"Updated song: {first_song.title}")
    
    # Reorder songs
    songs = playlist.read_songs()
    new_order = [songs[2].song_id, songs[0].song_id, songs[1].song_id]
    playlist.reorder_songs(new_order)
    print("Reordered songs in playlist")
    
    # Shuffle songs
    playlist.shuffle_songs()
    print("Shuffled songs in playlist")
    
    # Clear all songs
    song_count = len(playlist)
    playlist.clear_songs()
    print(f"Cleared {song_count} songs from playlist")


def example_cross_playlist_operations():
    """Demonstrate operations across multiple playlists."""
    print("\n=== Cross-Playlist Operations Example ===")
    
    manager = create_playlist_manager(storage_type='memory')
    
    # Create playlists
    rock_playlist = manager.create_playlist(name="Rock Songs", tags=['rock'])
    pop_playlist = manager.create_playlist(name="Pop Songs", tags=['pop'])
    
    # Create songs
    rock_song = create_song(title="Rock Song 1", artist="Rock Artist", genre="Rock")
    pop_song = create_song(title="Pop Song 1", artist="Pop Artist", genre="Pop")
    
    # Add songs to different playlists
    manager.add_song_to_playlist(rock_playlist.playlist_id, rock_song)
    manager.add_song_to_playlist(pop_playlist.playlist_id, pop_song)
    
    # Move song between playlists
    result = manager.move_song_between_playlists(
        rock_playlist.playlist_id,
        pop_playlist.playlist_id,
        rock_song
    )
    print(f"Moved song between playlists: {result}")
    
    # Verify the move
    rock_after = manager.get_playlist(rock_playlist.playlist_id)
    pop_after = manager.get_playlist(pop_playlist.playlist_id)
    
    print(f"Rock playlist songs: {len(rock_after)}")
    print(f"Pop playlist songs: {len(pop_after)}")
    
    # Find duplicate songs across playlists
    manager.add_song_to_playlist(rock_playlist.playlist_id, rock_song)  # Add same song back
    duplicates = manager.get_duplicate_songs()
    print(f"Found {len(duplicates)} songs in multiple playlists")
    
    for song_id, playlist_ids in duplicates.items():
        print(f"  Song {song_id} is in {len(playlist_ids)} playlists")


def example_analytics_and_statistics():
    """Demonstrate analytics and statistics features."""
    print("\n=== Analytics and Statistics Example ===")
    
    manager = create_playlist_manager(storage_type='memory')
    
    # Create diverse playlists and songs
    songs_data = [
        ("Song 1", "Artist 1", "Rock"),
        ("Song 2", "Artist 2", "Pop"),
        ("Song 3", "Artist 3", "Jazz"),
        ("Song 4", "Artist 1", "Rock"),  # Same artist as Song 1
        ("Song 5", "Artist 4", "Rock"),
        ("Song 6", "Artist 5", "Pop"),
    ]
    
    for title, artist, genre in songs_data:
        playlist = manager.create_playlist(
            name=f"{genre} Playlist",
            description=f"{genre} music collection",
            tags=[genre.lower()],
            is_public=(genre == "Pop")
        )
        
        song = create_song(title=title, artist=artist, genre=genre, duration=200)
        manager.add_song_to_playlist(playlist.playlist_id, song)
    
    # Get comprehensive statistics
    stats = manager.get_playlist_statistics()
    
    print("=== Playlist Statistics ===")
    print(f"Total Playlists: {stats['total_playlists']}")
    print(f"Total Songs: {stats['total_songs']}")
    print(f"Unique Songs: {stats['total_unique_songs']}")
    print(f"Average Songs per Playlist: {stats['average_songs_per_playlist']:.1f}")
    print(f"Total Duration: {stats['total_duration']} seconds")
    print(f"Average Duration per Playlist: {stats['average_duration_per_playlist']:.1f} seconds")
    
    print("\n=== Genre Popularity ===")
    for genre, count in stats['most_popular_genres']:
        print(f"  {genre.title()}: {count} songs")
    
    print("\n=== Public vs Private ===")
    print(f"Public: {stats['public_vs_private']['public']}")
    print(f"Private: {stats['public_vs_private']['private']}")
    
    print("\n=== Most Active Playlist ===")
    most_active = stats['most_active_playlist']
    print(f"Name: {most_active['name']}")
    print(f"Songs: {most_active['song_count']}")


def example_file_storage():
    """Demonstrate file-based storage operations."""
    print("\n=== File Storage Example ===")
    
    # Create temporary directory for storage
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Create manager with file storage
        manager = create_playlist_manager(storage_type='file', storage_dir=temp_dir)
        
        # Create and save playlists
        playlist1 = manager.create_playlist(name="File Playlist 1", description="First playlist")
        playlist2 = manager.create_playlist(name="File Playlist 2", description="Second playlist")
        
        # Add songs
        song1 = create_song(title="File Song 1", artist="File Artist")
        song2 = create_song(title="File Song 2", artist="File Artist")
        
        manager.add_song_to_playlist(playlist1.playlist_id, song1)
        manager.add_song_to_playlist(playlist2.playlist_id, song2)
        
        # Export all playlists
        export_file = os.path.join(temp_dir, "export.json")
        result = manager.storage.export_all_playlists(export_file)
        print(f"Exported playlists to file: {result}")
        
        # Get storage statistics
        stats = manager.storage.get_storage_stats()
        print(f"Storage stats: {stats['total_playlists']} playlists, {stats['total_size_kb']} KB")
        
        # Clean up
        manager.clear_cache()
        print("Cleared cache")


def example_data_migration():
    """Demonstrate data migration between storage types."""
    print("\n=== Data Migration Example ===")
    
    # Create source with in-memory storage
    source_manager = create_playlist_manager(storage_type='memory')
    
    # Create sample data
    playlist = source_manager.create_playlist(name="Migration Test", tags=['test'])
    song = create_song(title="Migrated Song", artist="Migration Artist", genre="Test")
    source_manager.add_song_to_playlist(playlist.playlist_id, song)
    
    # Create backup
    backup_data = source_manager.storage.backup_to_dict()
    print(f"Created backup with {backup_data['metadata']['playlist_count']} playlists")
    
    # Restore to file storage
    with tempfile.TemporaryDirectory() as temp_dir:
        target_manager = create_playlist_manager(storage_type='file', storage_dir=temp_dir)
        
        # Restore from backup
        result = target_manager.storage.restore_from_backup(backup_data)
        print(f"Restored to file storage: {result}")
        
        # Verify restoration
        restored_playlists = target_manager.list_playlists()
        print(f"Restored {len(restored_playlists)} playlists")
        
        if restored_playlists:
            restored_playlist = restored_playlists[0]
            print(f"Restored playlist: {restored_playlist.metadata.name}")
            print(f"Restored songs: {len(restored_playlist)}")


def example_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n=== Error Handling Example ===")
    
    manager = create_playlist_manager(storage_type='memory')
    
    # Create initial playlist
    playlist = manager.create_playlist(name="Error Test Playlist")
    
    try:
        # Try to create duplicate playlist
        manager.create_playlist(name="Error Test Playlist")
    except PlaylistExistsError as e:
        print(f"Caught expected error: {e}")
    
    # Create invalid song
    try:
        invalid_song = Song(title="", artist="Valid Artist")  # Empty title
    except ValueError as e:
        print(f"Caught validation error: {e}")
    
    # Add valid song
    valid_song = create_song(title="Valid Song", artist="Valid Artist")
    manager.add_song_to_playlist(playlist.playlist_id, valid_song)
    
    # Try to add duplicate
    try:
        manager.add_song_to_playlist(playlist.playlist_id, valid_song)
    except Exception as e:
        print(f"Caught duplicate song error: {type(e).__name__}")
    
    # Try to get non-existent playlist
    non_existent = manager.get_playlist("non-existent-id")
    print(f"Non-existent playlist: {non_existent}")
    
    # Try to update non-existent playlist
    result = manager.update_playlist("non-existent-id", name="New Name")
    print(f"Update non-existent playlist: {result}")


def example_flask_integration():
    """Demonstrate integration with Flask web framework."""
    print("\n=== Flask Integration Example ===")
    
    # Note: This is a code example, not actually running Flask
    
    from typing import Dict, Any
    
    class FlaskPlaylistAPI:
        def __init__(self):
            self.manager = create_playlist_manager(storage_type='file', storage_dir='playlist_data')
        
        def get_playlists(self) -> Dict[str, Any]:
            """API endpoint to get all playlists."""
            playlists = self.manager.list_playlists()
            return {
                'playlists': [p.to_dict() for p in playlists],
                'total': len(playlists)
            }
        
        def create_playlist_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
            """API endpoint to create a playlist."""
            try:
                playlist = self.manager.create_playlist(**data)
                return {
                    'success': True,
                    'playlist': playlist.to_dict()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        def add_song_api(self, playlist_id: str, song_data: Dict[str, Any]) -> Dict[str, Any]:
            """API endpoint to add a song to a playlist."""
            try:
                song = create_song(**song_data)
                result = self.manager.add_song_to_playlist(playlist_id, song)
                return {
                    'success': result,
                    'message': 'Song added successfully' if result else 'Failed to add song'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        def search_api(self, query: str) -> Dict[str, Any]:
            """API endpoint to search songs across playlists."""
            results = self.manager.search_songs_across_playlists(query)
            return {
                'query': query,
                'results': {
                    playlist_id: [song.to_dict() for song in songs]
                    for playlist_id, songs in results.items()
                }
            }
    
    # Example usage
    api = FlaskPlaylistAPI()
    print("Created Flask API wrapper")
    
    # Example API calls (would be used in actual Flask routes)
    response = api.get_playlists()
    print(f"Get playlists response: {response['total']} playlists")
    
    response = api.create_playlist_api({
        'name': 'API Test Playlist',
        'description': 'Created via API',
        'is_public': True
    })
    print(f"Create playlist response: {response['success']}")


def example_performance_testing():
    """Demonstrate performance characteristics."""
    print("\n=== Performance Testing Example ===")
    
    import time
    
    # Test with in-memory storage
    start_time = time.time()
    memory_manager = create_playlist_manager(storage_type='memory')
    
    # Create many playlists and songs
    for i in range(100):
        playlist = memory_manager.create_playlist(name=f"Perf Playlist {i}")
        for j in range(5):
            song = create_song(
                title=f"Perf Song {j}",
                artist=f"Perf Artist {j % 10}",
                duration=200 + j * 10
            )
            memory_manager.add_song_to_playlist(playlist.playlist_id, song)
    
    memory_time = time.time() - start_time
    print(f"Memory storage: Created 100 playlists with 500 songs in {memory_time:.2f} seconds")
    
    # Test search performance
    start_time = time.time()
    results = memory_manager.search_songs_across_playlists('Artist')
    search_time = time.time() - start_time
    print(f"Search performance: Found songs in {len(results)} playlists in {search_time:.4f} seconds")
    
    # Test statistics
    start_time = time.time()
    stats = memory_manager.get_playlist_statistics()
    stats_time = time.time() - start_time
    print(f"Statistics: Generated stats in {stats_time:.4f} seconds")


def run_all_examples():
    """Run all examples to demonstrate the system capabilities."""
    print("=" * 60)
    print("PLAYLIST MANAGEMENT SYSTEM - COMPREHENSIVE EXAMPLES")
    print("=" * 60)
    
    try:
        example_basic_operations()
        example_search_and_filtering()
        example_playlist_management()
        example_advanced_song_management()
        example_cross_playlist_operations()
        example_analytics_and_statistics()
        example_file_storage()
        example_data_migration()
        example_error_handling()
        example_flask_integration()
        example_performance_testing()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nExample failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run specific examples
    run_all_examples()
    
    # Or run individual examples
    # example_basic_operations()
    # example_search_and_filtering()
    # example_playlist_management()
    # example_advanced_song_management()
    # example_cross_playlist_operations()
    # example_analytics_and_statistics()
    # example_file_storage()
    # example_data_migration()
    # example_error_handling()
    # example_flask_integration()
    # example_performance_testing()