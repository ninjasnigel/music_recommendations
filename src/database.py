import sqlite3
import json
import os
import re

def setup_database(db_path="co_occurrences.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS co_occurrences
                 (song1 TEXT, song2 TEXT, count INTEGER, PRIMARY KEY (song1, song2))''')
    conn.commit()
    conn.close()

def numerical_sort_key(filename):
    # Extract numbers from the filename using regular expressions
    numbers = map(int, re.findall(r'\d+', filename))
    return tuple(numbers)  # Return a tuple of numbers as the sort key

def update_database_with_slice(file_path, db_path="co_occurrences.db"):
    # Open the JSON file and load its content
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Process each playlist in the JSON data
    for playlist in data['playlists']:
        # Extract all artist-song pairs in the current playlist
        playlist_artist_song_pairs = [(track['artist_name'], track['track_name']) for track in playlist['tracks']]
        
        # Update co-occurrence counts for each pair of artist-song in the playlist
        for i, pair1 in enumerate(playlist_artist_song_pairs):
            for pair2 in playlist_artist_song_pairs[i+1:]:  # Ensure we don't count a pair with itself
                # Ensure symmetric updates for both pair1 -> pair2 and pair2 -> pair1
                for song1, song2 in [(pair1, pair2), (pair2, pair1)]:
                    # Convert the artist-song pairs into a single string key for each song
                    song1_key = f"{song1[0]} - {song1[1]}"
                    song2_key = f"{song2[0]} - {song2[1]}"
                    # Update the database with the new count
                    c.execute('''
                        INSERT INTO co_occurrences (song1, song2, count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(song1, song2) DO UPDATE SET count = count + 1
                    ''', (song1_key, song2_key))
                    
    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

def update_co_occurrences_from_folder_database(folder_path, db_path="co_occurrences.db", slice_limit=5):
    # List all JSON files in the given folder and sort them
    filenames = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    # Implement a custom sort function if needed, like numerical_sort_key, to ensure correct order
    filenames.sort(key=numerical_sort_key)  # Assuming numerical_sort_key function is defined elsewhere

    # Process files up to the slice_limit
    for i, filename in enumerate(filenames[:slice_limit]):
        print(f"Processing slice {i+1}/{slice_limit}: {filename}")
        file_path = os.path.join(folder_path, filename)
        # Update the database with co-occurrences from this slice
        update_database_with_slice(file_path, db_path)

    # Since the database is being updated directly, there's no dictionary to return
    print("Finished updating co-occurrences in the database.")


def find_top_co_occurrences_database(db_path, artist_name, song_name, top_n=10):
    # Construct the search key from artist name and song name
    search_key = f"{artist_name} - {song_name}"
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Execute a query to find the top co-occurring songs for the given song
    query = '''
    SELECT song2, count 
    FROM co_occurrences 
    WHERE song1 = ? 
    ORDER BY count DESC 
    LIMIT ?
    '''
    c.execute(query, (search_key, top_n))
    
    # Fetch the results
    results = c.fetchall()
    
    # Close the connection to the database
    conn.close()
    
    # Format the results for display or further processing
    top_co_occurrences = []
    for song, count in results:
        top_co_occurrences.append(f"{song}: {count} times")
    
    return top_co_occurrences

"""def get_recommendations(playlist, co_occurences, top_n=10, database=False):
    co_occurences_list = []
    for artist, song in playlist:
        top_co_occurences = find_top_co_occurrences(co_occurences, artist, song, 50)
        co_occorences_normalized = normalize_co_occurrences(top_co_occurences)
        co_occurences_list.append(co_occorences_normalized)

    # Combined co-occurences
    combined_co_occurences = combine_co_occurence_list(co_occurences_list)
    print_combined_co_occurrences(combined_co_occurences, top_n=top_n, playlist=playlist)"""