import json
from collections import defaultdict
import os
from src.database import *

def slice_to_csv(slice_path="", co_occurrences=None):
    if co_occurrences is None:
        co_occurrences = defaultdict(lambda: defaultdict(int))
    with open(slice_path, 'r') as file:
        data = json.load(file)
    # Process each playlist in the JSON data
    for playlist in data['playlists']:
        # Extract all artist-song pairs in the current playlist
        playlist_artist_song_pairs = [(track['artist_name'], track['track_name']) for track in playlist['tracks']]
        
        # Update co-occurrence counts for each pair of artist-song in the playlist
        for i, pair1 in enumerate(playlist_artist_song_pairs):
            for pair2 in playlist_artist_song_pairs[i+1:]:  # Ensure we don't count a pair with itself
                co_occurrences[pair1][pair2] += 1
                co_occurrences[pair2][pair1] += 1  # Ensure symmetry, as co-occurrence is bidirectional
    return co_occurrences

def find_top_co_occurrences(co_occurrences, artist_name, song_name, top_n=10):
    # Create a key from the provided artist name and song name
    search_key = (artist_name, song_name)

    # Find the co-occurring songs for the given artist and song
    co_occurring_songs = co_occurrences.get(search_key, {})

    # Sort the co-occurring songs by their co-occurrence count in descending order
    sorted_co_occurring_songs = sorted(co_occurring_songs.items(), key=lambda x: x[1], reverse=True)

    # Take the top_n items from the sorted list
    top_co_occurring_songs = sorted_co_occurring_songs[:top_n]

    if not top_co_occurring_songs:
        print(f"No co-occurring songs found for '{artist_name} - {song_name}'")

    # Format and return the top co-occurring songs
    result = {}
    for (co_song, count) in top_co_occurring_songs:
        result[f"{co_song[0]} - {co_song[1]}"] = count
    return result

def update_co_occurrences_from_folder(folder_path, slice_limit=5):
    # Initialize an empty co_occurrences dictionary
    co_occurrences = defaultdict(lambda: defaultdict(int))

    # List all files in the given folder and sort them
    filenames = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    filenames.sort()  # Sorts the files in ascending alphanumeric order

    # Process files up to the slice_limit
    for i, filename in enumerate(filenames[:slice_limit]):
        print(f"Processing slice {i+1}/{slice_limit}: {filename}")
        file_path = os.path.join(folder_path, filename)
        # Check if the file is a JSON file and exists (redundant check removed)
        co_occurrences = slice_to_csv(file_path, co_occurrences)

    return co_occurrences

def normalize_co_occurrences(co_occurrences):
    normalized_co_occurrences = defaultdict(lambda: defaultdict(float))
    total_co_occurrences = 0
    for artist_song, co_occurring_songs in co_occurrences.items():
        total_co_occurrences += co_occurring_songs
    for artist_song, co_occurring_songs in co_occurrences.items():
        normalized_co_occurrences[artist_song] = co_occurring_songs / total_co_occurrences
    return normalized_co_occurrences

def combine_co_occurence_list(co_occurrences_list):
    combined_co_occurrences = defaultdict(lambda: defaultdict(int))
    for co_occurrences in co_occurrences_list:
        for artist_song, co_occurring_songs in co_occurrences.items():
            if artist_song in combined_co_occurrences:
                combined_co_occurrences[artist_song] += co_occurring_songs
            else:
                combined_co_occurrences[artist_song] = co_occurring_songs
    # Sort key by value and return in a list
    return combined_co_occurrences

def print_combined_co_occurrences(co_occurrences, top_n=10, playlist=[]):
    sorted_co_occurrences = dict(sorted(co_occurrences.items(), key=lambda item: item[1], reverse=True))
    for i, (artist_song, co_occurring_songs) in enumerate(sorted_co_occurrences.items()):
        if artist_song_string_split(artist_song) in playlist:
            top_n += 1
            continue
        if i >= top_n:
            break
        print(f"{artist_song} - {co_occurring_songs}")

def artist_song_string_split(str):
    return str.split(' - ')[0], str.split(' - ', 1)[1].split(':')[0]

def get_recommendations(playlist, co_occurences, top_n=10, use_database=False, database_path="co_occurrences.db"):
    co_occurences_list = []
    for artist, song in playlist:
        if use_database:
            top_co_occurences = find_top_co_occurrences_database(co_occurences, artist, song, 50)
        else:
            top_co_occurences = find_top_co_occurrences(co_occurences, artist, song, 50)
        co_occorences_normalized = normalize_co_occurrences(top_co_occurences)
        co_occurences_list.append(co_occorences_normalized)

    # Combined co-occurences
    combined_co_occurences = combine_co_occurence_list(co_occurences_list)
    print_combined_co_occurrences(combined_co_occurences, top_n=top_n, playlist=playlist)