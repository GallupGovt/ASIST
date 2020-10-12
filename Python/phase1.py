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
import copy

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
        goal_code = int(survey_df.at[member_id, goal_column])-1
        goal = ['victims', 'extinguisher', 'tasks', 'points'][goal_code]
        workload_column = ('Q213', 'Q222', 'Q231')[seek]
        workload = int(survey_df.at[member_id, workload_column])

        # ***ERIK***: Replace this
        orig_victim_strategy = 'Yellow Only'

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
        for i, r in df.iterrows():
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
        def get_room_id(name):
            # Correct variances in the naming scheme
            if name == 'The Computer Farm': name = 'Computer Farm'
            if name == 'Open Break Area': name = 'Break Room'
            for key, item in rooms[complexity].items():
                if item['name'] == name:
                    return key
            print("ERROR: Could not find room name", name, "-- check semantic map", complexity)
            sys.exit()
        print("Creating room_victims list...")
        room_victims = {'total': {'Green': 0, 'Yellow': 0, 'type': 0}}
        for v in df['data_mission_victim_list'][df['data_mission_victim_list'].notnull()].values[0]:
            r = v['room_name']
            room_id = get_room_id(r)
            if room_id not in room_victims:
                room_victims[room_id] = {'Green': 0, 'Yellow': 0, 'type': 0}
            if v['block_type'] == 'block_victim_1':
                room_victims['total']['Green'] += 1
                room_victims[room_id]['Green'] += 1
            elif v['block_type'] == 'block_victim_2':
                room_victims['total']['Yellow'] += 1
                room_victims[room_id]['Yellow'] += 1
        # Determines the type of each room.
        # 0) no victims, 1) one or more yellow victims,
        # 2) One or more green victims, 3) a mix of green and yellow.
        update_room_types(room_victims)
        # Create rooms in room_victims for rooms with zero victims
        for id, r in rooms[complexity].items():
            if id not in room_victims:
                room_victims[id] = {'Green': 0, 'Yellow': 0, 'type': 0}

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
        df['ext_victims_in_view'] = np.NaN
        df['ext_victims_in_view'] = df['ext_victims_in_view'].astype('object')
        def find_victims_in_view(blocks):
            vl = []
            for b in blocks:
                if b['type'].startswith('block_victim'):
                    (x, y, z) = b['location']
                    vl.append((x, y, z))
            return vl
        for i, r in df.iterrows():
            if r['topic'] == 'agent/pygl_fov/player/3d/summary':
                df.at[i, 'ext_victims_in_view'] = find_victims_in_view(
                    blocks=r['data_blocks'])

        # Determine victims seen since last victim_triaged event and put them in 'ext_victims_seen'
        print("Determining victims seen since last triage event...")
        df['ext_victims_seen'] = np.NaN
        df['ext_victims_seen'] = df['ext_victims_seen'].astype('object')
        vl = set()
        for i, r in df.iterrows():
            # If it's a triage event, put the list of victims seen in the dataframe,
            # reset the victim list, and continue
            if r['ext_event'] == 'victim_triaged':
                df.at[i, 'ext_victims_seen'] = sorted(list(vl))
                vl = set()
                continue
            # If there are no victims in view, continue
            if not isinstance(r['ext_victims_in_view'], list): continue
            # Add the victims in view to the set
            for v in r['ext_victims_in_view']: vl.add(v)

        # Determine rooms skipped since last room_entered event put them in 'ext_rooms_skipped'
        print("Determining rooms skipped since last room entered event...")
        df['ext_rooms_skipped'] = np.NaN
        df['ext_rooms_skipped'] = df['ext_rooms_skipped'].astype('object')
        vl = {}
        for i, r in df.iterrows():
            # If it's a room entered event, put the list of rooms triggered in the dataframe,
            # reset the triggered list, and continue
            if r['ext_event'] == 'room_entered':
                # Discard the room that has been entered
                if r['ext_room_id'] in vl: vl.pop(r['ext_room_id'])
                vlx = []
                for k, v in vl.items():
                    vlx.append({'id': k, 'type': v})
                df.at[i, 'ext_rooms_skipped'] = vlx
                vl = {}
                continue
            # If there are no rooms triggered, continue
            if not isinstance(r['ext_trigger'], str): continue
            # Add the room triggered to the set, accounting for the fact that
            # if it's after five minutes, all yellow victims are expired
            id = r['ext_trigger']
            if i < expire_index:
                vl[id] = room_victims[id]['type']
            else:
                green = room_victims[id]['Green']
                if green == 0: vl[id] = 0
                else: vl[id] = 2

        # Create a new df, event_df, to contain all event rows with events
        event_df = df[(df['ext_event']=='victim_triaged') |
            (df['ext_event']=='room_entered')].copy()

        print("Determining victims skipped and strategy since last triage event...")
        df['ext_victims_skipped'] = np.NaN
        df['ext_victims_skipped'] = df['ext_victims_skipped'].astype('object')
        victim_strategy = orig_victim_strategy
        for i, r in event_df.iterrows():
            if r['ext_event'] == 'victim_triaged':
                # Determine victim strategy at each moment
                victim_strategy = compute_victim_strategy(
                    old_vs=victim_strategy,
                    rescued=r['data_color'],
                    viewed=r['ext_victims_seen'],
                    victim_list=victim_list
                )
                event_df.at[i, 'ext_victim_strategy'] = victim_strategy
                # Determine colors of victims seen since last triaged
                (green, yellow) = (0, 0)
                for v in r['ext_victims_seen']:
                    if victim_list[v]['color'] == 'Green': green += 1
                    elif victim_list[v]['color'] == 'Yellow': yellow += 1
                # Subtract one for the victim currently being triaged
                if r['data_color'] == 'Green': green -= 1
                elif r['data_color'] == 'Yellow': yellow -= 1
                event_df.at[i, 'ext_victims_skipped_green'] = green
                event_df.at[i, 'ext_victims_skipped_yellow'] = yellow

        # Determine the distance of the next victim
        event_df['ext_next_victim_distance'] = (
            ((event_df['data_x']-event_df['ext_next_victim_x'])**2+
            (event_df['data_z']-event_df['ext_next_victim_z'])**2+
            (event_df['data_y']-event_df['ext_next_victim_y'])**2)
            **(1/2))

        # Determine yellow victims remaining at each point
        yellow = room_victims['total']['Yellow']
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
        tmp_room_victims = copy.deepcopy(room_victims)
        for i, row in event_df.iterrows():
            r = row['ext_room_id']
            # Does the room have any victims?
            if r not in tmp_room_victims:
                event_df.at[i, 'ext_yellow_victims_in_current_room'] = 0
                event_df.at[i, 'ext_green_victims_in_current_room'] = 0
                continue
            # If the row is greater than the expire_index (when all yellows die)
            # then yellow must be zero
            if i >= expire_index:
                tmp_room_victims[r]['Yellow'] = 0
            # Else if the triaged victim was yellow, decrease yellows by 1
            elif row['data_color'] == 'Yellow':
                tmp_room_victims[r]['Yellow'] -= 1
            # Else if the triaged victim was green, decrease greens by 1
            if row['data_color'] == 'Green':
                tmp_room_victims[r]['Green'] -= 1
            event_df.at[i, 'ext_yellow_victims_in_current_room'] = tmp_room_victims[r]['Yellow']
            event_df.at[i, 'ext_green_victims_in_current_room'] = tmp_room_victims[r]['Green']
            update_room_types(tmp_room_victims)
            event_df.at[i, 'ext_room_type'] = tmp_room_victims[r]['type']

        # Determine time spent in each victim strategy, first five minutes only
        prev_sr = 600
        prev_vs = orig_victim_strategy
        vs_data = {prev_vs: 0}
        for i, row in event_df.loc[event_df['ext_event']=='victim_triaged'].iterrows():
            vs = row['ext_victim_strategy']
            if vs not in vs_data: vs_data[vs] = 0
            sr = row['ext_seconds_remaining']
            if sr >= 300:
                time_elapsed = prev_sr - sr
                vs_data[prev_vs] += time_elapsed
                prev_vs = vs
                prev_sr = sr
            else:
                time_elapsed = prev_sr - 300
                vs_data[prev_vs] += time_elapsed
                break


        # Put in Q7 survey responses
        q7_cols = [col for col in survey_df if col.startswith('Q7_')]
        q7 = survey_df[q7_cols]
        event_df['ext_q7_average'] = q7.mean(axis=1, skipna=True)[member_id]

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


        # Create a final dictionary to hold all of the data
        final = {
            'member_id': member_id,
            'trial_id': trial_id,
            'complexity': complexity,
            'training': training,
            'goal': goal,
            'events': [],
        }












        # write_final_csv(new_df, fname)
        # plot_map(fname, area_df, connection_df, location_df, df)


# Get the metadata about the file from the filename and fill in the values into
# the dataframe
def get_metadata(name):
    s = re.search(r'TrialMessages_CondBtwn-(.*)_CondWin-Falcon(.*)-DynamicMap_Trial-(.*)_Team-na_Member-(.*)_', name)
    member_id = s.group(4)
    trial_id = s.group(3)
    complexity = s.group(2)
    training = s.group(1)
    return (member_id, trial_id, complexity, training)

def update_room_types(room_victims):
    for k, v in room_victims.items():
        if   v['Yellow'] == 0 and v['Green'] == 0: v['type'] = 0
        elif v['Yellow'] >  0 and v['Green'] == 0: v['type'] = 1
        elif v['Yellow'] == 0 and v['Green'] >  0: v['type'] = 2
        elif v['Yellow'] >  0 and v['Green'] >  0: v['type'] = 3

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
