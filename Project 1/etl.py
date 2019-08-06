'''
Author: Ivan  Diaz (Based on Udacity DE Nanodegree template
This module calls the jobs to extract, transform and lod the Sparkfy
logs and songs data to the created database
To be directly called from the terminal, required the sql_queries module
'''

import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """
    Perform ETL on the dataset: song_data, to create the songs and artists dimensional tables
    :param cur: Cursor object
    :param filepath: Data source location from process_data function
    """
    # open song file
    df = pd.read_json(filepath, lines=True)

    # insert song record
    song_data = df[['song_id',
                    'title',
                    'artist_id',
                    'year',
                    'duration']]

    song_data = song_data.values.flatten().tolist()

    cur.execute(song_table_insert, song_data)

    # insert artist record
    artist_data = df[['artist_id',
                      'artist_name',
                      'artist_location',
                      'artist_latitude',
                      'artist_longitude']]

    artist_data = artist_data.values.flatten().tolist()

    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
    Perform ETL on the dataset: log_data, to create time, user and songplays tables
    :param cur: Cursor object
    :param filepath: Data source location from process_data function
    """

    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df.page == 'NextSong']

    # convert timestamp column to datetime
    t = pd.to_datetime(df.ts, unit='ms')

    # insert time data records
    time_data = pd.concat([t,
                           t.dt.hour,
                           t.dt.day,
                           t.dt.week,
                           t.dt.month,
                           t.dt.year,
                           t.dt.weekday],
                          axis=1)

    column_labels = ('start_time',
                     'hour',
                     'day',
                     'week',
                     'month',
                     'year',
                     'weekday')
    time_df = pd.DataFrame(data=time_data.values, columns=column_labels)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId',
                  'firstName',
                  'lastName',
                  'gender',
                  'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        # get songid and artistid from song and artist tables
        results = cur.execute(song_select, (row.song, row.artist, row.length))
        songid, artistid = results if results else None, None

        # insert songplay record
        songplay_data = (pd.to_datetime(row.ts, unit='ms'),
                         row.userId,
                         row.level,
                         songid,
                         artistid,
                         row.sessionId,
                         row.location,
                         row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    Iterates over files from the song_data and log_data sources and process the
    previously defined functions process_song_file and process_log_file
    :param cur: Cursor object
    :param conn: Connection
    :param filepath: Data source location songs or logs
    :param func: Process applied for songs or logs data
    """

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
