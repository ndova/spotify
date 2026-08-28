#!/usr/bin/env python3
import sys
import os
from config import Config
from spotify_client import SpotifyClient
from itunes_client import iTunesClient
from downloader import AudioDownloader
import argparse
from typing import List, Dict
import time

class MusicDownloader:
    def __init__(self):
        """Initialize the music downloader application"""
        self.spotify_client = SpotifyClient(
            Config.SPOTIFY_CLIENT_ID,
            Config.SPOTIFY_CLIENT_SECRET
        ) if Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET else None
        
        self.itunes_client = iTunesClient()
        self.downloader = AudioDownloader(Config.DOWNLOAD_PATH)
    
    # Spotify methods (keep existing ones)
    def download_spotify_track(self, track_url: str):
        """Download a single track from Spotify"""
        if not self.spotify_client:
            print("❌ Spotify client not configured!")
            return
        
        print("\n" + "="*50)
        print("🎵 DOWNLOADING SPOTIFY TRACK")
        print("="*50)
        
        track_info = self.spotify_client.extract_track_info(track_url)
        if track_info:
            print(f"\n📝 Track found: {track_info['artist']} - {track_info['title']}")
            print(f"💿 Album: {track_info['album']}")
            
            if self.downloader.download_from_youtube(track_info):
                print("\n✅ Track downloaded successfully!")
            else:
                print("\n❌ Failed to download track.")
        else:
            print("❌ Invalid track URL or track not found.")
    
    def download_spotify_playlist(self, playlist_url: str):
        """Download all tracks from a Spotify playlist"""
        if not self.spotify_client:
            print("❌ Spotify client not configured!")
            return
        
        print("\n" + "="*50)
        print("📻 DOWNLOADING SPOTIFY PLAYLIST")
        print("="*50)
        
        tracks = self.spotify_client.extract_playlist_info(playlist_url)
        if tracks:
            print(f"\n📝 Found {len(tracks)} tracks in playlist")
            
            successful = 0
            for i, track in enumerate(tracks, 1):
                print(f"\n[{i}/{len(tracks)}] Downloading: {track['artist']} - {track['title']}")
                
                if self.downloader.download_from_youtube(track):
                    successful += 1
                
                time.sleep(1)
            
            print(f"\n✅ Playlist download complete! {successful}/{len(tracks)} tracks downloaded.")
        else:
            print("❌ Invalid playlist URL or playlist is empty.")
    
    # iTunes methods
    def search_itunes(self, query: str, limit: int = 10):
        """Search for tracks on iTunes"""
        print("\n" + "="*50)
        print("🍎 SEARCHING iTUNES")
        print("="*50)
        
        tracks = self.itunes_client.search_tracks(query, limit)
        if tracks:
            print(f"\n📝 Found {len(tracks)} tracks on iTunes:")
            for i, track in enumerate(tracks, 1):
                price = f"${track['track_price']:.2f}" if track.get('track_price') else "N/A"
                print(f"  [{i}] {track['artist']} - {track['title']}")
                print(f"      Album: {track['album']} | Genre: {track.get('genre', 'N/A')} | Price: {price}")
            
            print("\nOptions:")
            print("  - Enter track numbers to download (comma-separated)")
            print("  - Type 'preview' + numbers for 30-sec previews (e.g., 'preview 1,3')")
            print("  - Type 'all' to download all via YouTube")
            print("  - Type 'q' to quit")
            
            choice = input("\n> ").strip().lower()
            
            if choice == 'q':
                return
            
            if choice.startswith('preview'):
                # Download iTunes previews
                numbers = choice.replace('preview', '').strip()
                selected_tracks = self._select_tracks(tracks, numbers)
                if selected_tracks:
                    print(f"\n📥 Downloading {len(selected_tracks)} preview(s)...")
                    for track in selected_tracks:
                        print(f"\nDownloading preview: {track['artist']} - {track['title']}")
                        if self.downloader.download_itunes_preview(track):
                            print("  ✅ Preview downloaded")
                        else:
                            print("  ❌ Preview download failed")
                        time.sleep(0.5)
            elif choice == 'all':
                # Download all via YouTube
                print(f"\n📥 Downloading {len(tracks)} tracks via YouTube...")
                successful = 0
                for i, track in enumerate(tracks, 1):
                    print(f"\n[{i}/{len(tracks)}] Downloading: {track['artist']} - {track['title']}")
                    if self.downloader.download_from_youtube(track):
                        successful += 1
                    time.sleep(1)
                print(f"\n✅ Download complete! {successful}/{len(tracks)} tracks downloaded.")
            else:
                # Download selected via YouTube
                selected_tracks = self._select_tracks(tracks, choice)
                if selected_tracks:
                    print(f"\n📥 Downloading {len(selected_tracks)} tracks via YouTube...")
                    successful = 0
                    for track in selected_tracks:
                        print(f"\nDownloading: {track['artist']} - {track['title']}")
                        if self.downloader.download_from_youtube(track):
                            successful += 1
                        time.sleep(1)
                    print(f"\n✅ Download complete! {successful}/{len(selected_tracks)} tracks downloaded.")
        else:
            print("❌ No tracks found on iTunes.")
    
    def search_itunes_albums(self, query: str, limit: int = 5):
        """Search for albums on iTunes"""
        print("\n" + "="*50)
        print("🍎 SEARCHING iTUNES ALBUMS")
        print("="*50)
        
        albums = self.itunes_client.search_albums(query, limit)
        if albums:
            print(f"\n📝 Found {len(albums)} albums on iTunes:")
            for i, album in enumerate(albums, 1):
                print(f"  [{i}] {album['artist']} - {album['album']}")
                print(f"      Tracks: {album['track_count']} | Genre: {album.get('genre', 'N/A')}")
            
            print("\nEnter album number to view tracks, or 'q' to quit:")
            choice = input("> ").strip()
            
            if choice == 'q':
                return
            
            try:
                album_index = int(choice) - 1
                if 0 <= album_index < len(albums):
                    album = albums[album_index]
                    print(f"\n📀 Loading tracks for: {album['artist']} - {album['album']}")
                    
                    tracks = self.itunes_client.get_album_tracks(album['album_id'])
                    if tracks:
                        print(f"\nFound {len(tracks)} tracks:")
                        for i, track in enumerate(tracks, 1):
                            print(f"  [{i}] {track['title']} ({track['duration']}s)")
                        
                        print("\nOptions:")
                        print("  - Enter track numbers to download (comma-separated)")
                        print("  - Type 'preview' + numbers for 30-sec previews")
                        print("  - Type 'all' to download all via YouTube")
                        print("  - Type 'q' to quit")
                        
                        download_choice = input("\n> ").strip().lower()
                        
                        if download_choice == 'q':
                            return
                        
                        if download_choice.startswith('preview'):
                            numbers = download_choice.replace('preview', '').strip()
                            selected_tracks = self._select_tracks(tracks, numbers)
                            if selected_tracks:
                                print(f"\n📥 Downloading {len(selected_tracks)} preview(s)...")
                                for track in selected_tracks:
                                    print(f"\nDownloading preview: {track['title']}")
                                    if self.downloader.download_itunes_preview(track):
                                        print("  ✅ Preview downloaded")
                                    else:
                                        print("  ❌ Preview download failed")
                                    time.sleep(0.5)
                        elif download_choice == 'all':
                            print(f"\n📥 Downloading {len(tracks)} tracks via YouTube...")
                            successful = 0
                            for track in tracks:
                                print(f"\nDownloading: {track['artist']} - {track['title']}")
                                if self.downloader.download_from_youtube(track):
                                    successful += 1
                                time.sleep(1)
                            print(f"\n✅ Download complete! {successful}/{len(tracks)} tracks downloaded.")
                        else:
                            selected_tracks = self._select_tracks(tracks, download_choice)
                            if selected_tracks:
                                print(f"\n📥 Downloading {len(selected_tracks)} tracks via YouTube...")
                                successful = 0
                                for track in selected_tracks:
                                    print(f"\nDownloading: {track['artist']} - {track['title']}")
                                    if self.downloader.download_from_youtube(track):
                                        successful += 1
                                    time.sleep(1)
                                print(f"\n✅ Download complete! {successful}/{len(selected_tracks)} tracks downloaded.")
                else:
                    print("❌ Invalid album number.")
            except ValueError:
                print("❌ Invalid input.")
        else:
            print("❌ No albums found on iTunes.")
    
    def _select_tracks(self, tracks: List[Dict], choice: str) -> List[Dict]:
        """Helper method to select tracks based on user input"""
        try:
            if choice == 'all':
                return tracks
            
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            return [tracks[i] for i in indices if 0 <= i < len(tracks)]
        except:
            return []
    
    def interactive_mode(self):
        """Run the application in interactive mode"""
        while True:
            print("\n" + "="*50)
            print("🎵 MUSIC DOWNLOADER")
            print("="*50)
            print("1. Search iTunes")
            print("2. Search iTunes Albums")
            print("3. Download from Spotify (if configured)")
            print("4. Exit")
            print("="*50)
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                query = input("Enter search query: ").strip()
                self.search_itunes(query)
            
            elif choice == '2':
                query = input("Enter album search query: ").strip()
                self.search_itunes_albums(query)
            
            elif choice == '3':
                if self.spotify_client:
                    url = input("Enter Spotify URL: ").strip()
                    if 'playlist' in url:
                        self.download_spotify_playlist(url)
                    else:
                        self.download_spotify_track(url)
                else:
                    print("❌ Spotify is not configured. Please set up Spotify API credentials.")
            
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option. Please try again.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Music Downloader - Download music from iTunes and Spotify')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-s', '--source', choices=['itunes', 'spotify', 'itunes-album'],
                       default='itunes', help='Source to search (itunes, spotify, itunes-album)')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('-l', '--limit', type=int, default=10,
                       help='Number of results to show')
    
    args = parser.parse_args()
    
    downloader = MusicDownloader()
    
    if args.interactive or not args.query:
        downloader.interactive_mode()
    elif args.query:
        if args.source == 'itunes':
            downloader.search_itunes(args.query, args.limit)
        elif args.source == 'itunes-album':
            downloader.search_itunes_albums(args.query, args.limit)
        elif args.source == 'spotify':
            if downloader.spotify_client:
                url = args.query
                if 'playlist' in url:
                    downloader.download_spotify_playlist(url)
                else:
                    downloader.download_spotify_track(url)
            else:
                print("❌ Spotify is not configured!")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()