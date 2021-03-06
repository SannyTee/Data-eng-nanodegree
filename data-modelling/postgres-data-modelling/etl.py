import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """
        Reads the song log file and process the data into artists and song table
        :param cur: database cursor
        :param filepath: path to file to be processed
        :return: None
        """
    df = pd.read_json(filepath, lines=True)

    num_songs, artist_id, artist_latitude, artist_longitude, artist_location, artist_name, song_id, title, duration, year = df.values[0]
    # insert song record
    song_data = [song_id, title, duration, year, artist_id]
    cur.execute(song_table_insert, song_data)

    # insert artist record
    artist_data = [artist_id, artist_latitude, artist_location, artist_longitude, artist_name]
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
        Reads the log file and process the data into the time, user and songplay table
        :param cur: database cursor
        :param filepath:  path to log file to be  processed
        :return: None
    """
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    t = df['ts'].map(lambda val: pd.to_datetime(val, unit='ms'))

    # insert time data records
    time_data = [[line, line.hour, line.day, line.week, line.month, line.year, line.day_name()] for line in t]
    column_labels = ('start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday')
    time_df = pd.DataFrame(time_data, columns=column_labels)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId', 'firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():

        # get songid and artistid from song and artist table
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        if results:
            song_id, artist_id = results
        else:
            song_id, artist_id = None, None
        # insert songplay record
        songplay_data = (pd.to_datetime(row.ts, unit='ms'), int(row.userId), song_id, artist_id, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root, '*.json'))
        for f in files:
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()
