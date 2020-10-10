#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 08:58:25 2020

@author: cynthia_song
"""

import json
import numpy as np
import pandas as pd
import glob
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import textwrap
import sys
import re
import pprint
from tqdm import tqdm
import math

# main program
def main():

    # # read in the file that contains the path of each file.
    # file1 = open('path.txt', 'r')
    # Lines = file1.readlines()
    # file_names = []
    # for line in Lines:
    #     file_names.append(line.strip())

    # directory = 'Data/messages/Falcon/'
    directory = '/home/erik_jones/git/asist_data'
    condition_path = 'Data/metadata/conditions_metadata.csv'
    survey_path = 'Data/surveys/surveys.csv'
    map_path = 'Data/Locations'

    DIFFICULTIES = ('Easy',)

    # Load the semantic maps (room locations). room_to_parent is a mapping
    # of child room ids to their parent room id. rooms is a dictionary of
    # room ids to their name, type, children (if any), and x1/x2/z1/z2
    # coordinates if not a parent.
    map = {}
    room_to_parent = {}
    rooms = {}
    coordinates = {}
    for d in (DIFFICULTIES):
        room_to_parent[d] = {}
        rooms[d] = {}
        with open(map_path + f'/Falcon_v1.0_{d}_sm.json') as f:
            map[d] = json.loads(f.read())
        for loc in map[d]['locations']:
            rooms[d][loc['id']] = {'name': loc['name'], 'type': loc['type']}
            if 'child_locations' in loc:
                rooms[d][loc['id']]['children'] = loc['child_locations']
                for x in loc['child_locations']:
                    room_to_parent[d][x] = loc['id']
            else:
                rooms[d][loc['id']]['x1'] = loc['bounds']['coordinates'][0]['x']
                rooms[d][loc['id']]['x2'] = loc['bounds']['coordinates'][1]['x']
                rooms[d][loc['id']]['z1'] = loc['bounds']['coordinates'][0]['z']
                rooms[d][loc['id']]['z2'] = loc['bounds']['coordinates'][1]['z']
        # Create a map of every possible coordinate and what rooms they go to
        coordinates[d] = {}
        (low_x, low_z) = (99999,99999)
        (high_x, high_z) = (-99999,-99999)
        for id, r in rooms[d].items():
            if 'x1' in r:
                if r['x1'] < low_x: low_x = r['x1']
                if r['x2'] < low_x: low_x = r['x2']
                if r['x1'] > high_x: high_x = r['x1']
                if r['x2'] > high_x: high_x = r['x2']
                if r['z1'] < low_z: low_z = r['z1']
                if r['z2'] < low_z: low_z = r['z2']
                if r['z1'] > high_z: high_z = r['z1']
                if r['z2'] > high_z: high_z = r['z2']
        for x in range(low_x, high_x + 1):
            for z in range(low_z, high_z + 1):
                coordinates[d][(x, z)] = {'x': x, 'z': z, 'rooms': []}
                for id, r in rooms[d].items():
                    if 'x1' not in r: continue
                    if r['x1'] <= x <= r['x2'] and r['z1'] <= z <= r['z2']:
                        coordinates[d][(x,z)]['rooms'].append(id)
                        if id in room_to_parent[d]:
                            coordinates[d][(x,z)]['rooms'].append(room_to_parent[d][id])

    # Create a mapping of beep trigger coordinates to room ids
    for d in (DIFFICULTIES):
        tdf = pd.read_csv(f'{map_path}/MapInfo_{d}.csv')
        for i, row in tdf.iterrows():
            (x, y, z) = row['LocationXYZ'].split()
            (x, y, z) = (int(x), int(y), int(z))
            for room_id, room in rooms[d].items():
                if room['name'] == row['RoomName']:
                    coordinates[d][(x, z)]['trigger'] = room_id

    # Read in the survey data, indexed to the member_id (we hope)
    survey_df = pd.read_csv(survey_path, skiprows=[1,2], index_col='Q4')
    survey_df.replace(-99, np.NaN, inplace=True)

    # Loop through each JSON file
    for name in glob.glob(directory+'/*.json'):
        fname = name.replace(directory, "")

        # Get the information out of the filename
        (member_id, trial_id, complexity, training) = get_metadata(name)

        # ***ERIK***: Replace this once you have real data
        member_id = 23

        # Get their goal from the survey. The numbers correspond to
        # the order of three columns in the order of Easy, Medium, and Hard. If
        # the numbers are 213, the order of those three columns are Q13=Medium,
        # Q17=Easy, Q21=Hard. Start with getting Column o
        o = (str(int(survey_df.at[member_id, 'o'])))
        # Figure out which number to look for based on the complexity
        seek = {'Easy': 1, 'Medium': 2, 'Hard': 3}[complexity] -1
        # Figure out which goal column to look at based on the seek number
        # and get that goal
        goal_column = ('Q13', 'Q17', 'Q21')[seek]
        goal_code = [int(survey_df.at[member_id, goal_column])-1]
        goal = ('victims', 'extinguisher', 'tasks', 'points')[goal_code]

        # ***ERIK***: Replace this
        victim_strategy = 'Yellow Only'

        # Pull in the raw data from the json file into a dictionary, keeping
        # only topic, data, and msg
        print("Loading JSON...")
        with open(directory+fname) as f:
            orig_data = json.loads("[" + f.read().replace("}\n{", "},\n{") + "]")
        data = []
        for line in orig_data:
            # Skip all observation messages from the god character, ASIST3
            if line['data'].get('name', '') == 'ASIST3':
                continue
            data.append({
                'data': line['data'],
                'topic': line['topic'],
                'msg': line['msg']
            })

        # pprint.pprint(data[30000], indent=2)
        # print('------------------')
        # pprint.pprint(data[30001], indent=2)
        # sys.exit()

        # i = 0
        # for d in data:
        #     # if (d['topic'] == 'observations/events/player/door'
        #     #     or d['topic'] == 'observations/events/player/beep'
        #     #     or d['topic'] == 'observations/events/player/triage'
        #     #     or 'entered_area_id' in d['data']):
        #     if d['topic'] == 'observations/events/player/beep':
        #         i += 1
        #         pprint.pprint(d, indent=2)
        #         print('----------------------')
        # sys.exit()

        # Normalize the data into a dataframe
        print("Normalizing JSON into a dataframe...")
        df = pd.json_normalize(data)
        df.columns = df.columns.map(lambda x: x.replace(".", "_"))

        # Create ext_trigger for any moment the player steps on a beep trigger
        print("Creating trigger data...")
        last_room = None
        for i, r in df[df['data_x'].notnull()].iterrows():
            x = r['data_x']
            z = r['data_z']
            for c in [
                (math.floor(x), math.floor(z)),
                (math.floor(x), math.ceil(z)),
                (math.ceil(x), math.floor(z)),
                (math.ceil(x), math.ceil(z))]:
                if c not in coordinates[complexity]:
                    continue
                if 'trigger' in coordinates[complexity][c]:
                    t = coordinates[complexity][c]['trigger']
                    if last_room != t:
                        df.at[i, 'ext_trigger'] = t
                        last_room = t

        # Creating ext_beeps to indicate number of beeps (1 or 2)
        for i, r in df[df['data_beep_x'].notnull()].iterrows():
            if r['data_message'] == 'Beep':
                df.at[i, 'ext_beeps'] = 1
            elif r['data_message'] == 'Beep Beep':
                df.at[i, 'ext_beeps'] = 2

        # Creates a victim list where the key is a hash of the x/y/z coordinates.
        # This must be done from the FoV because the x/y/z in the victim_list event
        # is wrong. Stores x, y, z and color.
        print("Creating victim list...")
        victim_list = {}
        for i, r in tqdm(df.iterrows()):
            if r['topic'] == 'agent/pygl_fov/player/3d/summary':
                for b in r['data_blocks']:
                    if not b['type'].startswith('block_victim'): continue
                    (vx, vy, vz) = b['location']
                    key = (vx, vy, vz)
                    if key in victim_list: continue
                    victim_list[key] = {
                        'x': vx, 'y': vy, 'z': vz,
                        'color': 'Green' if b['type'] == 'block_victim_1' else 'Yellow'
                    }

        # Determines number of victims per room by color
        print("Creating room_victims list...")
        room_victims = {'total': {'green': 0, 'yellow': 0, 'type': 0}}
        for v in df['data_mission_victim_list'][df['data_mission_victim_list'].notnull()].values[0]:
            r = v['room_name']
            if r not in room_victims:
                room_victims[r] = {'green': 0, 'yellow': 0, 'type': 0}
            if v['block_type'] == 'block_victim_1':
                room_victims['total']['green'] += 1
                room_victims[r]['green'] += 1
            elif v['block_type'] == 'block_victim_2':
                room_victims['total']['yellow'] += 1
                room_victims[r]['yellow'] += 1

        # Determines the type of each room.
        # 0) no victims, 1) one or more yellow victims,
        # 2) One or more green victims, 3) a mix of green and yellow.
        for k, v in room_victims.items():
            if   v['yellow'] >  0 and v['green'] == 0: v['type'] = 1
            elif v['yellow'] == 0 and v['green'] >  0: v['type'] = 2
            elif v['yellow'] >  0 and v['green'] >  0: v['type'] = 3

        # Fills the event rows that have blank values with their values from the previous row
        # cols = ['data_x', 'data_y', 'data_z', 'data_mission_timer', 'data_blocks']
        print("Setting player coordinates and elapsed time...")
        cols = ['data_x', 'data_y', 'data_z', 'data_mission_timer']
        df.loc[:,cols] = df.loc[:,cols].ffill()

        # Creates 'ext_seconds_remaining' based on time from mission start
        df = set_elapsed_time(df)

        # Find out what index number yellow victims expire at
        expire_index = df['data_expired_message'][df['data_expired_message'].notnull()].index.values[0]

        # Create extension variables for room id and room name and fill them forward
        df['ext_room_id'] = df['data_entered_area_id']
        df['ext_room_id'].fillna(method='ffill', inplace=True)
        df['ext_room_name'] = df['data_entered_area_name']
        df['ext_room_name'].fillna(method='ffill', inplace=True)

        # Create 'ext_event' for 'room_entered' or 'victim_triaged'
        print("Creating ext_event...")
        def check_event(row):
            if row['data_entered_area_id'] not in (None, np.NaN, ''):
                return 'room_entered'
            elif (row['data_triage_state'] not in (None, np.NaN, '')
                and row['data_triage_state']=='SUCCESSFUL'):
                return 'victim_triaged'
            else:
                return np.NaN
        df['ext_event'] = df.apply(lambda row: check_event(row), axis=1)

        # Determine the location of the next victim
        df['ext_next_victim_x'] = df['data_victim_x'].bfill()
        df['ext_next_victim_y'] = df['data_victim_y'].bfill()
        df['ext_next_victim_z'] = df['data_victim_z'].bfill()

        # Determine the victims in view at any moment and put into
        # 'ext_victims_in_view'.
        print("Creating victims in view...")
        # df['ext_rooms_in_view'] = np.NaN
        df['ext_victims_in_view'] = np.NaN
        # df['ext_rooms_in_view'] = df['ext_rooms_in_view'].astype('object')
        df['ext_victims_in_view'] = df['ext_victims_in_view'].astype('object')
        for i, r in tqdm(df.iterrows()):
            if r['topic'] == 'agent/pygl_fov/player/3d/summary':
                # df.at[i, 'ext_rooms_in_view'] = find_rooms_in_view(
                #     blocks=r['data_blocks'],
                #     diff=complexity,
                #     map=map,
                #     room_to_parent=room_to_parent)
                df.at[i, 'ext_victims_in_view'] = find_victims_in_view(
                    blocks=r['data_blocks'])

        # Determine victims seen since last event and put them in 'ext_victims_seen'
        print("Determining victims seen since last event...")
        df['ext_victims_seen'] = np.NaN
        df['ext_victims_seen'] = df['ext_victims_seen'].astype('object')
        vl = set()
        for i, r in tqdm(df.iterrows()):
            # If it's an event, put the list of victims seen in the dataframe,
            # reset the victim list, and continue
            if r['ext_event'] == 'victim_triaged' or r['ext_event'] == 'room_entered':
                df.at[i, 'ext_victims_seen'] = sorted(list(vl))
                vl = set()
                continue
            # If there are no victims in view, continue
            if not isinstance(r['ext_victims_in_view'], list): continue
            # Add the victims in view to the set
            for v in r['ext_victims_in_view']: vl.add(v)

        # Create a new df, event_df, to contain all event rows with events
        event_df = df[(df['ext_event']=='victim_triaged') |
            (df['ext_event']=='room_entered')].copy()

        # Determine victim strategy at each moment
        for i, r in event_df.iterrows():
            if r['ext_event'] == 'victim_triaged':
                victim_strategy = compute_victim_strategy(
                    old_vs=victim_strategy,
                    rescued=r['data_color'],
                    viewed=r['ext_victims_seen'],
                    victim_list=victim_list
                )
            event_df.at[i, 'ext_victim_strategy'] = victim_strategy

        # Determine the distance of the next victim
        event_df['ext_next_victim_distance'] = (
            ((event_df['data_x']-event_df['ext_next_victim_x'])**2+
            (event_df['data_z']-event_df['ext_next_victim_z'])**2+
            (event_df['data_y']-event_df['ext_next_victim_y'])**2)
            **(1/2))

        # Determine yellow victims remaining at each point
        yellow = rooms['total']['yellow']
        for i, row in event_df.iterrows():
            # If the row is greater than the expire_index (when all yellows die)
            # then yellow must be zero
            if i >= expire_index:
                yellow = 0
            # Else if the triaged victim was yellow, decrease yellows by 1
            elif row['data_color']=='Yellow':
                yellow -= 1
            event_df.at[i, 'ext_total_yellow_victims_remaining'] = yellow

        # Determine green and yellow victims in current room
        for i, row in event_df.iterrows():
            r = row['ext_room_name']
            # Does the room have any victims?
            if r not in room_victims:
                event_df.at[i, 'ext_yellow_victims_in_current_room'] = 0
                event_df.at[i, 'ext_green_victims_in_current_room'] = 0
                continue
            # If the row is greater than the expire_index (when all yellows die)
            # then yellow must be zero
            if i >= expire_index:
                room_victims[r]['yellow'] = 0
            # Else if the triaged victim was yellow, decrease yellows by 1
            elif row['data_color'] == 'Yellow':
                room_victims[r]['yellow'] -= 1
            # Else if the triaged victim was green, decrease greens by 1
            if row['data_color'] == 'Green':
                room_victims[r]['green'] -= 1
            event_df.at[i, 'ext_yellow_victims_in_current_room'] = room_victims[r]['yellow']
            event_df.at[i, 'ext_green_victims_in_current_room'] = room_victims[r]['green']
            event_df.at[i, 'ext_room_type'] = room_victims[r]['type']

        # Put in Q7 survey responses
        q7_cols = [col for col in survey_df if col.startswith('Q7_')]
        q7 = survey_df[q7_cols]
        event_df['ext_q7_average'] = q7.mean(axis=1, skipna=True)[member_id]
        event_df['member_id'] = member_id
        event_df['trial_id'] = trial_id
        event_df['complexity'] = complexity
        event_df['training'] = training
        event_df['ext_goal'] = goal

        sys.exit()















        cols = ['ext_event', 'member_id', 'trial_id', 'complexity', 'training',
          'ext_q7_average',
          'ext_room_type', 'ext_next_victim_distance', 'ext_room_id',
          'ext_room_name', 'ext_seconds_remaining', 'data_color',
          'ext_yellow_victims_in_current_room', 'ext_green_victims_in_current_room',
          'ext_total_yellow_victims_remaining']
        export_df = event_df[cols]

        print(export_df)
        sys.exit()














        # write_final_csv(new_df, fname)
        # plot_map(fname, area_df, connection_df, location_df, df)


def find_rooms_in_view(blocks, diff, map, room_to_parent):
    """Find all of the rooms that are in the current FoV"""
    # Make a unique list of room ids
    ids = set()
    # Loop through every block in the FoV message
    for b in blocks:
        (bx, by, bz) = b['location']
        for d in ('locations', 'connections'):
            for x in map[diff][d]:
                if 'bounds' not in x:
                    continue
                x1, z1, x2, z2 = (
                    x['bounds']['coordinates'][0]['x'],
                    x['bounds']['coordinates'][0]['z'],
                    x['bounds']['coordinates'][1]['x'],
                    x['bounds']['coordinates'][1]['z'])
                if x1 <= bx <= x2  and  z1 <= bz <= z2:
                    # If it's a location, get the room id and parent room ids
                    if d == 'locations':
                        # print('Adding room')
                        ids.add(x['id'])
                        if x['id'] in room_to_parent[diff]:
                            # print('Adding room parent')
                            ids.add(room_to_parent[diff][x['id']])
                    # If it's a connection, get the rooms it is connected to
                    elif d == 'connections':
                        for c in x['connected_locations']:
                            # print('Adding connected room')
                            ids.add(c)
    return sorted(list(ids))

# Scan through the blocks to find victims in view
def find_victims_in_view(blocks):
    vl = []
    for b in blocks:
        if b['type'].startswith('block_victim'):
            (x, y, z) = b['location']
            vl.append((x, y, z))
    return vl

# Get the metadata about the file from the filename and fill in the values into
# the dataframe
def get_metadata(name):
    s = re.search(r'TrialMessages_CondBtwn-(.*)_CondWin-Falcon(.*)-DynamicMap_Trial-(.*)_Team-na_Member-(.*)_', name)
    member_id = s.group(4)
    trial_id = s.group(3)
    complexity = s.group(2)
    training = s.group(1)
    return (member_id, trial_id, complexity, training)

# Find when the game start and calculate elapsed time based on that
def set_elapsed_time(df):

    # Return the number of seconds, expecting the format 'mm : ss'
    def timer_to_secs(x):
        if x in (None, np.NaN, ''):
            return None
        s = re.search(r'([0-9]*) : ([0-9]*)', x)
        if s is not None:
            return (int(s.group(1)) * 60) + int(s.group(2))
        else:
            return None

    # Set the time in seconds in 'ext_seconds_remaining', and fill forward empty values
    df['ext_seconds_remaining'] = df['data_mission_timer'].apply(timer_to_secs).ffill()
    return df

# Figure out what new victim strategy is
def compute_victim_strategy(old_vs, rescued, viewed, victim_list):
    if old_vs not in ('Yellow Only', 'Sequential', 'Green Only', 'Mixed'):
        raise Exception(f"Incorrect old_vs ({old_vs})")
    # Determine what was skipped
    (g, y) = (0,0)
    new = ''
    for v in viewed:
        if   victim_list[v]['color'] == 'Green':  g += 1
        elif victim_list[v]['color'] == 'Yellow': y += 1
    # Determine new strategy
    if old_vs == 'Yellow Only':
        if rescued == 'Yellow':
            if   g >  0 and y == 0: new = 'Yellow Only'
            elif g == 0 and y == 0: new = 'Yellow Only'
            elif g == 0 and y >  0: new = 'Mixed'
            elif g >  0 and y >  0: new = 'Mixed'
        elif rescued == 'Green':
            if   g >  0 and y == 0: new = 'Mixed'
            elif g == 0 and y == 0: new = 'Sequential'
            elif g == 0 and y >  0: new = 'Green Only'
            elif g >  0 and y >  0: new = 'Mixed'
    elif old_vs == 'Sequential':
        if rescued == 'Yellow':
            if   g >  0 and y == 0: new = 'Yellow Only'
            elif g == 0 and y == 0: new = 'Sequential'
            elif g == 0 and y >  0: new = 'Mixed'
            elif g >  0 and y >  0: new = 'Mixed'
        elif rescued == 'Green':
            if   g >  0 and y == 0: new = 'Mixed'
            elif g == 0 and y == 0: new = 'Sequential'
            elif g == 0 and y >  0: new = 'Green Only'
            elif g >  0 and y >  0: new = 'Mixed'
    elif old_vs == 'Green Only':
        if rescued == 'Yellow':
            if   g >  0 and y == 0: new = 'Yellow Only'
            elif g == 0 and y == 0: new = 'Sequential'
            elif g == 0 and y >  0: new = 'Mixed'
            elif g >  0 and y >  0: new = 'Mixed'
        elif rescued == 'Green':
            if   g >  0 and y == 0: new = 'Mixed'
            elif g == 0 and y == 0: new = 'Green Only'
            elif g == 0 and y >  0: new = 'Green Only'
            elif g >  0 and y >  0: new = 'Mixed'
    elif old_vs == 'Mixed':
        if rescued == 'Yellow':
            if   g >  0 and y == 0: new = 'Yellow Only'
            elif g == 0 and y == 0: new = 'Sequential'
            elif g == 0 and y >  0: new = 'Mixed'
            elif g >  0 and y >  0: new = 'Mixed'
        elif rescued == 'Green':
            if   g >  0 and y == 0: new = 'Mixed'
            elif g == 0 and y == 0: new = 'Green Only'
            elif g == 0 and y >  0: new = 'Green Only'
            elif g >  0 and y >  0: new = 'Mixed'
    if new == '':
        raise Exception(f"Could not compute new victim strategy: old_vs: {old_vs}, rescued: {rescued}, g: {g}, y: {y}")
    return new




























def get_area(data):
    area_df = pd.json_normalize(data ,"areas")
    return area_df

def get_connection(data):
    connection_df = pd.json_normalize(data ,"connections")
    return connection_df

def get_location(data):
    location_df = pd.json_normalize(data ,"locations")
    return location_df

# group the victims by room and sum up.
def get_new_loc(data):
    location_df = pd.json_normalize(data ,"locations")
    new_loc_df = location_df.groupby(['area_id'])[['victims.critical', 'victims.non_critical']].sum().reset_index()
    return new_loc_df

# join the tables to get necessary information
def join_condition(condition_df, fname, subject_id, new_df):
    mission_complex_df = condition_df[['condition_id', 'condition_within_Ss']]
    study_id = fname[11:26]
    condition_id = fname[27:46]
    trial_id = fname[47:62]
    new_df['study_id'] = study_id
    new_df['condition_id'] = condition_id
    new_df['trial_id'] = trial_id
    new_df['subject_id'] = subject_id
    new_df = pd.merge(new_df, mission_complex_df, left_on='condition_id', right_on='condition_id', how='left')
    training_df = condition_df[['condition_id', 'condition_between_Ss']]
    new_df = pd.merge(new_df, training_df, left_on='condition_id', right_on='condition_id', how='left')
    return new_df

def plot_map(fname, area_df, connection_df, location_df, df):
    critical_df = location_df[location_df['victims.critical']==1.0]
    non_critical_df = location_df[location_df['victims.non_critical']==1.0]

    fig,ax = plt.subplots(figsize=(50,20))
    currentAxis = plt.gca()

    for i in range(len(area_df)):
        currentAxis.add_patch(Rectangle((area_df['x1'][i], area_df['y1'][i]), \
                                        area_df['x2'][i]-area_df['x1'][i], area_df['y2'][i]-area_df['y1'][i], \
                                        fill=False, color='black'))
        plt.text(area_df['x1'][i]+1, (area_df['y1'][i]+area_df['y2'][i])/2-1, textwrap.fill(area_df['name'][i], 10),fontsize=16)

    for i in range(len(connection_df)):
        currentAxis.add_patch(Rectangle((connection_df['x'][i], connection_df['y'][i]), \
                                        connection_df['x2'][i]-connection_df['x'][i],\
                                        connection_df['y2'][i]-connection_df['y'][i], \
                                        fill=True, color='white'))

    plt.scatter(critical_df['x'], critical_df['y'], s=200, marker='o', c= 'gold')
    plt.scatter(non_critical_df['x'], non_critical_df['y'], s=200, marker='^', c= 'green')

    plt.scatter(df['data_x'], df['data_z'], s= 15, marker='.', c= 'coral')

    plt.xlim([-2165, -2015])
    plt.ylim([140, 200])
    plt.savefig('./output/'+ fname[:-5] + '.jpeg')


if __name__ == "__main__":
    main()
