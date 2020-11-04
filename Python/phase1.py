#!/usr/bin/env python3

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
import os

import competency_test_analysis as cta

root_dir = '/mnt/DARPA/CONSULTING/Analytics/Phase_1/Data'
competency_dir = f'{root_dir}/competency_data'
trial_dir = f'{root_dir}/trial_data'
export_dir = f'{root_dir}/processed_data'
map_dir = f'{root_dir}/map_data'
fov_dir = f'{root_dir}/fov_data'
survey_file = f'{root_dir}/study-1_2020.08_HSRData_SurveysNumeric_CondBtwn-na_CondWin-na_Trial-na_Team-na_Member-na_Vers-1.csv'

DIFFICULTIES = ('Easy', 'Medium', 'Hard')

"""
Additional variables created in the dataframe after loading the metadata,
and what each variable holds, for easy reference. Add new variables to this
list alphabetically.

data_entered_area_id - the id of the room being entered
data_exited_area_id - the id of the room being exited
data_score - current score
ext_beeps - Holds the number of beeps when the beeper goes off (1 - green, 2 - yellow)
ext_event - type of event (see events above)
ext_exited_room_type - type of room the player exited (in real time)
ext_green_per_minute - number of green victims saved per minute (triage events only)
ext_green_victims_in_current_room (used on event messages)
ext_last_room_id - the id of the previous room the player was in
ext_next_room_id - the id of the next room the player will enter
ext_next_room_id - The id of the room that the player will enter next
ext_next_victim_distance - distance to next victim triaged (used on event messages)
ext_room_id - Room currently in
ext_room_name - Room name currently in (DO NOT TRUST, use room id and semantic map instead)
ext_room_skipped - on trigger events, the id of a room that has been skipped
ext_room_type - type of room the player is in, based upon the actual state of the room
ext_rooms_skipped - ids of rooms skipped, room entered events only ([{'id': 'tkt', 'type': 1}])
ext_seconds_remaining - Seconds remaining in mission
ext_total_yellow_victims_remaining (used on event messages)
ext_trigger - Holds a room id when the trigger point is stepped on (parent rooms only)
ext_victim_strategy - current victim strategy (used on triage event messages)
ext_victims_in_view - a list of keys to victim_list (used on FoV messages)
ext_victims_seen - victims seen since last room entered event (keys to victim_list, used on event messages)
ext_victims_skipped_green - green victims skipped, triage events only
ext_victims_skipped_yellow - yellow victims skipped, triage events only
ext_yellow_per_minute - number of yellow victims saved per minute (triage events only)
ext_yellow_victims_in_current_room (used on event messages)
ext_prior_use_consistent - the running total of rooms skipped consistent with victim strategy
ext_prior_use_inconsistent - the running total of rooms skipped inconsistent with victim strategy
"""

def main():

    # --------------------------------------------------------------------------
    # Remove old error messages
    # --------------------------------------------------------------------------
    os.system(f'rm {export_dir}/*_ERROR.txt')

    # --------------------------------------------------------------------------
    # Read in the survey data, indexed to the member_id (Q5)
    # --------------------------------------------------------------------------
    survey_df = pd.read_csv(survey_file, skiprows=[1,2], index_col='Q5')
    survey_df.replace(-99, np.NaN, inplace=True)
    survey_df.index = survey_df.index.str.strip()

    # --------------------------------------------------------------------------
    # Load the semantic maps (room locations). A separate one of each of these
    # dictionaries is created for each difficulty level.
    #
    # orig_map: loads the semantic maps into memory from the file system. This will
    # get updated per mission based on ground truth messages.
    # --------------------------------------------------------------------------
    orig_map = {}
    for d in (DIFFICULTIES):
        with open(f'{map_dir}/Falcon_v1.0_{d}_sm.json') as f:
            orig_map[d] = json.loads(f.read())

    # --------------------------------------------------------------------------
    # Loop through each JSON file
    # --------------------------------------------------------------------------
    # begin_parsing = False
    for name in sorted(glob.glob(trial_dir+'/*.metadata')):
        fname = name.replace(trial_dir, "")



        # Don't do files that are NoTriage or NoSignal
        # if 'FalconEasy-StaticMap_Trial-257' in name:
        #     begin_parsing = True
        #     continue
        # if begin_parsing is False: continue


        # ----------------------------------------------------------------------
        # Get the information out of the filename
        # ----------------------------------------------------------------------
        s = re.search(r'TrialMessages_CondBtwn-(.*)_CondWin-Falcon(.*)-.*Trial-(.*)_Team.*_Member-(.*)_', name)
        member_id = s.group(4)
        trial_id = s.group(3)
        complexity = s.group(2)
        training = s.group(1)
        if complexity == 'Med': complexity = 'Medium'

        # ----------------------------------------------------------------------
        # A function for writing error messages
        # ----------------------------------------------------------------------
        def write_error(error):
            print("ERROR:", error)
            with open(f"{export_dir}/member_{member_id}_trial_{trial_id}_ERROR.txt", "w") as f:
                f.write(error + '\n')

        # ----------------------------------------------------------------------
        # Get the competency test analysis score
        # ----------------------------------------------------------------------
        try:
            competency_score = cta.get_competency_result(member_id)
        except Exception as e:
            competency_score = None

        # ----------------------------------------------------------------------
        # Pull in the raw data from the json file into a dictionary, keeping
        # only topic, data, and msg. Originally we had to pull out the "god"
        # data from the player ASIST3, but that seems to no longer be true in
        # newer files.
        # ----------------------------------------------------------------------
        print(f'------------------\nFILE: {name}\nProcessing {member_id}...')
        print("Loading JSON...")
        # member_id = 44
        # trial_id = 97
        # complexity = 'Hard'
        # training = 'TriageSignal'
        # with open('/home/erik_jones/git/asist/Python/study-1_2020.08_HSRData_TrialMessages_CondBtwn-TriageSignal_CondWin-FalconHard-DynamicMap_Trial-97_Team-na_Member-44_Vers-1.metadata') as f:
        with open(trial_dir+fname) as f:
            orig_data = json.loads("[" + f.read().replace("}\n{", "},\n{") + "]")
        data = []
        try:
            for line in orig_data:
                data.append({
                    'data': line['data'],
                    'topic': line['topic'],
                    'msg': line['msg']
                })
        except Exception as e:
            write_error("It looks like the original metadata file is corrupted")
            continue

        # for i, d in enumerate(data):
        #     if d['topic'] == 'ground_truth/mission/blockages_list':
        #         pprint.pprint(d, indent=2)
        #         print('----------------------')
        # sys.exit()

        # ----------------------------------------------------------------------
        # Replace the FoV data in this file with the new separate FoV data.
        # Hopefully this will only be temporary.
        # ----------------------------------------------------------------------
        try:
            print("Replacing FoV data...")
            fovname = fname.replace('.metadata', '.fov')
            with open(fov_dir + fovname) as f:
            # with open('/home/erik_jones/git/asist/Python/study-1_2020.08_HSRData_TrialMessages_CondBtwn-TriageSignal_CondWin-FalconHard-DynamicMap_Trial-97_Team-na_Member-44_Vers-1.fov') as f:
                fov = json.loads("[" + f.read().replace("}\n{", "},\n{") + "]")
            fovd = {}
            for x in fov: fovd[x['data']['observation']] = x
            newdata = []
            for d in data:
                # Find fov messages in the trial data
                if d['topic'] == 'agent/pygl_fov/player/3d/summary':
                    n = d['data']['observation']
                    # Discard any fov message from the original data that is not
                    # found in the new fov data
                    if n not in fovd:
                        # newdata.append(d)
                        continue
                    # Replace it with the message from the fov data
                    x = fovd[n]
                    newdata.append({
                        'data': x['data'],
                        'topic': 'agent/pygl_fov/player/3d/summary',
                        'msg': x['msg']
                    })
                else:
                    newdata.append(d)
            data = newdata
        except FileNotFoundError as e:
            write_error(f"No FoV file found for this metadata")
            continue

        # ----------------------------------------------------------------------
        # Before we convert to a dataframe, go backwards through the events
        # and put the score for the player as data:score where there is a
        # triage event. We go backwards because the scoreboard is updated after
        # the triage event.
        # ----------------------------------------------------------------------
        score = 0
        final_score = 0
        for i, d in reversed(list(enumerate(data))):
            if d['topic'] == 'observations/events/scoreboard':
                for k, v in d['data']['scoreboard'].items():
                    score = v
                    if score > final_score: final_score = score
            elif d['topic'] == 'observations/events/player/triage':
                if d['data']['triage_state'] == 'SUCCESSFUL':
                    d['data']['score'] = score

        # ----------------------------------------------------------------------
        # Normalize the data into a dataframe
        # ----------------------------------------------------------------------
        print("Normalizing JSON into a dataframe...")
        df = pd.json_normalize(data)
        df.columns = df.columns.map(lambda x: x.replace(".", "_"))

        # -------------------------------------------------------------------
        # We need to process all of the messages from the new semantic map
        # updates. We start by making a complete copy of the original map
        # data.
        #
        # *ON HOLD*. I could find no instance where the semantic map updates
        # actually updated the dimensions of a room, which is all we care about
        # so far.
        # -------------------------------------------------------------------
        map = copy.deepcopy(orig_map)

        # ----------------------------------------------------------------------
        # Create all of the data from the map information, including room
        # information and coordinates.
        # ----------------------------------------------------------------------
        print("Creating map data...")
        # room_to_parent is a mapping of child room ids to their parent room id
        # sample data: {'room_child_id': 'room_id', ...}
        room_to_parent = {}
        # rooms is a dictionary of room ids to their name, type, children (if any),
        # and x1/x2/z1/z2 coordinates if not a parent. y coordinates are not
        # necessary to describe rooms. Sample data:
        # 'wf': { 'children': ['wf_1', 'wf_2', 'wf_3', 'wf_4', 'wf_5'],
        #     'name': 'Water Fountain',
        #     'type': 'fountain'},
        # 'wf_1': { 'name': 'Part of Water Fountain',
        #       'type': 'fountain_part',
        #       'x1': -2105,
        #       'x2': -2097,
        #       'z1': 150,
        #       'z2': 177},
        rooms = {}
        # coordinates is a dictionary of every possible x/z coordinate in the
        # playing field, what room id that coordinate is mapped to, and if that
        # point is a trigger point to a room (added later). Sample data:
        # (-2022, 146): {'room': 'tkt', 'trigger': 'r103', 'x': -2022, 'z': 146},
        # (-2022, 147): {'room': 'tkt', 'x': -2022, 'z': 147},
        coordinates = {}
        newrp = {}
        for d in (DIFFICULTIES):
            room_to_parent[d] = {}
            rooms[d] = {}
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
            # Get rid of nested rooms, every room should go to the ultimate parent
            newrp[d] = {}
            for r, p in room_to_parent[d].items():
                if p in room_to_parent[d]:
                    newrp[d][r] = room_to_parent[d][p]
                else:
                    newrp[d][r] = p
            room_to_parent[d] = newrp[d]
            # Determine the low and high x and z needed.
            (low_x, low_z) = (99999,99999)
            (high_x, high_z) = (-99999,-99999)
            for id, r in rooms[d].items():
                if 'x1' in r:
                    low_x = min(r['x1'], r['x2'], low_x)
                    low_z = min(r['z1'], r['z2'], low_z)
                    high_x = max(r['x1'], r['x2'], high_x)
                    high_z = max(r['z1'], r['z2'], high_z)
            # Create a map of every possible coordinate and what rooms they go to
            coordinates[d] = {}
            for x in range(low_x, high_x + 1):
                for z in range(low_z, high_z + 1):
                    coordinates[d][(x, z)] = {'x': x, 'z': z, 'room': None}
                    for id, r in rooms[d].items():
                        if 'x1' not in r: continue
                        if r['x1'] <= x <= r['x2'] and r['z1'] <= z <= r['z2']:
                            if id in room_to_parent[d]:
                                coordinates[d][(x,z)]['room'] = room_to_parent[d][id]
                            else:
                                coordinates[d][(x,z)]['room'] = id

        # ----------------------------------------------------------------------
        # Create a mapping of beep trigger coordinates to room ids, and a
        # list of rooms with trigger points. This comes from the MapInfo_{diff}.csv
        # files. trigger_rooms sample data: ['acr', 'br', ...]
        # ----------------------------------------------------------------------
        trigger_rooms = {}
        # Sanity rooms is to make sure that when a victim is triaged, they are
        # actually in a trigger room. This is used only for sanity checking.
        sanity_rooms = {}
        for d in (DIFFICULTIES):
            trigger_rooms[d] = []
            sanity_rooms[d] = []
            tdf = pd.read_csv(f'{map_dir}/MapInfo_{d}.csv')
            for i, row in tdf.iterrows():
                # Correct variances in the naming scheme
                mapname = row['RoomName']
                if mapname == 'The Computer Farm': mapname = 'Computer Farm'
                if mapname == 'Open Break Area': mapname = 'Break Room'
                if mapname == 'Janitor': mapname = "Janitor's Closet"
                if mapname not in sanity_rooms[d]: sanity_rooms[d].append(mapname)
                (x, y, z) = row['LocationXYZ'].split()
                (x, y, z) = (int(x), int(y), int(z))
                for room_id, room in rooms[d].items():
                    if room['name'] == mapname:
                        coordinates[d][(x, z)]['trigger'] = room_id
                        if room_id not in trigger_rooms[d]:
                            trigger_rooms[d].append(room_id)

        # ----------------------------------------------------------------------
        # Subject id is P00000##, as opposed to member_id, which is just ##.
        # Subject id is the same as the index in survey_df, column Q5
        # ----------------------------------------------------------------------
        for i, r in df.loc[df['data_subjects'].notnull()].iterrows():
            subject_id = r['data_subjects'][0]
            break

        # ----------------------------------------------------------------------
        # Get their workload from the survey. The numbers correspond to
        # the order of three columns in the order of Easy, Medium, and Hard. If
        # the numbers are 213, the order of those three columns are Q212=Medium,
        # Q221=Easy, Q230=Hard. Start with getting Column o, and turning it into
        # a three-digit string.
        # ----------------------------------------------------------------------
        try:
            # Correct that these look like dates, i.e. 01/02/2003
            o = survey_df.at[subject_id, 'o'].replace('/', '').replace('200', '')
        except KeyError as e:
            write_error("Member not found in survey file")
            continue
        # Figure out which number to look for based on the complexity
        seek = {
            'Easy': int(o[0]),
            'Medium': int(o[1]),
            'Hard': int(o[2])
        }[complexity] - 1
        # Do the same for the workload columns
        workload_column = ('Q212', 'Q221', 'Q230')[seek]
        workload = int(survey_df.at[subject_id, workload_column])

        # ----------------------------------------------------------------------
        # Create original victim and navigation strategies. Right now, this is
        # hard-coded, though will hopefully be changed in the future to reflect
        # the survey answers.
        # ----------------------------------------------------------------------
        orig_victim_strategy = 'Yellow Only'
        orig_nav_strategy = 'Yellow First'

        # ----------------------------------------------------------------------
        # Get videogaming experience, using only the calculable numbers from
        # https://docs.google.com/document/d/1mh1Q2rV_8S_dewdU_UQM4e1WEH05jOGS
        # and not any of the free-form answers.
        # ----------------------------------------------------------------------
        def calculate_experience():
            def get_val(x):
                try:
                    if int(x) == -99: return 0
                    return int(x)
                except Exception as e:
                    return 0
            often_played    = get_val(survey_df.at[subject_id, 'Q261'])
            how_often       = get_val(survey_df.at[subject_id, 'Q262'])
            length          = get_val(survey_df.at[subject_id, 'Q263'])
            frequency       = (how_often - 1) + (length - 1)
            q268            = get_val(survey_df.at[subject_id, 'Q268'])
            better          = (3, 2, 0)[q268 - 1] if q268 != 0 else 0
            q269            = get_val(survey_df.at[subject_id, 'Q269'])
            tournaments     = 1 if q269 == 1 else 0
            tournaments_won = get_val(survey_df.at[subject_id, 'Q271'])
            score = often_played + frequency + better + tournaments + tournaments_won
            return score
        videogame_experience = calculate_experience()

        # ----------------------------------------------------------------------
        # Creates a victim list where the key is a hash of the x/y/z coordinates.
        # Stores the color of the victim and the room id.
        # sample data:
        # (-2104, 60, 190): { 'color': 'Green',
        #               'room': 'r111',
        #               'x': -2104,
        #               'y': 60,
        #               'z': 190},
        # (-2101, 60, 186): { 'color': 'Yellow',
        #               'room': 'r111',
        #               'x': -2101,
        #               'y': 60,
        #               'z': 186}
        # ----------------------------------------------------------------------
        # NOTE: This is the version of the victim list from the FoV messages.
        # We don't use this, except for sanity checking.
        print("Creating victim list from FoV...")
        fov_victim_list = {}
        for i, r in df.iterrows():
            if r['topic'] == 'agent/pygl_fov/player/3d/summary':
                for b in r['data_blocks']:
                    if not b['type'].startswith('block_victim'): continue
                    (vx, vy, vz) = b['location']
                    key = (vx, vy, vz)
                    if key in fov_victim_list: continue
                    fov_victim_list[key] = {
                        'x': vx, 'y': vy, 'z': vz,
                        'color': 'Green' if b['type'] == 'block_victim_1' else 'Yellow',
                        'room': coordinates[complexity][(vx, vz)]['room']
                    }

        # NOTE: This is the version of the victim list from the ground truth.
        # We use this as our actual victim list.
        print("Creating victim list from ground truth...")
        victim_list = {}
        for i, r in df[df['topic']=='ground_truth/mission/victims_list'].iterrows():
            for b in r['data_mission_victim_list']:
                if not b['block_type'].startswith('block_victim'): continue
                key = (b['x'], b['y'], b['z'])
                if key in victim_list: continue
                room = coordinates[complexity][(b['x'], b['z'])]['room']
                victim_list[key] = {
                    'x': b['x'], 'y': b['y'], 'z': b['z'],
                    'color': 'Green' if b['block_type'] == 'block_victim_1' else 'Yellow',
                    'room': room
                }

        # ----------------------------------------------------------------------
        # OLD IDEA: Remove from the list of trigger rooms any room that does not
        # have a victim in it.
        #
        # NEW IDEA: Remove Right Hallway ('rh') only.
        # ----------------------------------------------------------------------
        # tmpvr = []
        # for k, v in victim_list.items():
        #     if v['room'] not in tmpvr: tmpvr.append(v['room'])
        # newtr = []
        # for t in trigger_rooms[complexity]:
        #     if t in tmpvr: newtr.append(t)
        # trigger_rooms[complexity] = newtr
        # for k, v in coordinates[complexity].items():
        #     if 'trigger' in v:
        #         if v['trigger'] not in tmpvr:
        #             v.pop('trigger')
        if 'rh' in trigger_rooms[complexity]:
            trigger_rooms[complexity].remove('rh')
        for k, v in coordinates[complexity].items():
            if 'trigger' in v:
                if v['trigger'] == 'rh':
                    v.pop('trigger')

        # ----------------------------------------------------------------------
        # Create room entered and exited events, as well as the last and next room
        # ----------------------------------------------------------------------
        last_room = ''
        last_i = -1
        for x in ('data_entered_area_id', 'data_exited_area_id', 'ext_last_room_id',
            'ext_next_room_id', 'ext_sanity_room_loc'
        ):
            df[x] = None # Always best practice to pre-populate non-numerical columns
        entered_a_room = False
        for i, r in df.loc[df['data_locations'].notnull()].iterrows():
            loc = r['data_locations'][0]['id']
            if loc == 'UNKNOWN': continue
            # We only want parent rooms
            if loc in room_to_parent[complexity]:
                loc = room_to_parent[complexity][loc]
            # Let's have a sanity check for what room we are in from original messages
            df.at[i, 'ext_sanity_room_loc'] = loc
            if last_room != loc:
                # This next line is crucial, it makes it so that we skip
                # recording the entry info of any room that is not one of the
                # trigger rooms.
                if loc not in trigger_rooms[complexity]: continue
                # What room is the player entering and exiting
                entered_a_room = True
                df.at[i, 'data_entered_area_id'] = loc
                df.at[i, 'data_exited_area_id'] = last_room
                df.at[i, 'ext_last_room_id'] = last_room
                if last_i != -1:
                    df.at[last_i, 'ext_next_room_id'] = loc
                last_room = loc
                last_i = i
        if entered_a_room is False:
            write_error("There was no record of any room being entered by the player")
            continue

        # ----------------------------------------------------------------------
        # Create extension variable for room ids, fill forward
        # ----------------------------------------------------------------------
        df['ext_room_id'] = df['data_entered_area_id']
        df['ext_room_id'].fillna(method='ffill', inplace=True)
        df['ext_next_room_id'].fillna(method='ffill', inplace=True)
        df['ext_last_room_id'].fillna(method='ffill', inplace=True)
        df['ext_sanity_room_loc'].fillna(method='ffill', inplace=True)

        # ----------------------------------------------------------------------
        # Create ext_trigger for any moment the player steps on a beep trigger.
        # x/z coordinates are floats, not integers. so check all possible
        # combinations of the roundings. A trigger to a room only happens once,
        # so don't allow it to happen multiple times in a row to the same room.
        # ext_trigger holds the id of the room being triggered.
        # ----------------------------------------------------------------------
        print("Creating player trigger data...")
        last_room = None
        df['ext_trigger'] = None
        for i, r in df[df['data_x'].notnull()].iterrows():
            x = r['data_x']
            z = r['data_z']
            for c in [
                (math.floor(x), math.floor(z)),
                (math.floor(x), math.ceil(z)),
                (math.ceil(x), math.floor(z)),
                (math.ceil(x), math.ceil(z))]:
                if c not in coordinates[complexity]: continue
                if 'trigger' in coordinates[complexity][c]:
                    t = coordinates[complexity][c]['trigger']
                    if last_room != t:
                        df.at[i, 'ext_trigger'] = t
                        last_room = t

        # ----------------------------------------------------------------------
        # Look at each triggered room and see if it was skipped. If the triggered
        # room is not the current room, previous room, or next room, it was
        # skipped. ext_room_skipped holds the id of the room skipped.
        # ----------------------------------------------------------------------
        df['ext_room_skipped'] = None
        count = 0
        for i, r in df.loc[df['ext_trigger'].notnull()].iterrows():
            t = r['ext_trigger']
            if (  t != r['ext_room_id']
            and t != r['ext_next_room_id']
            and t != r['ext_last_room_id']
            and t in trigger_rooms[complexity]
            ):
                count += 1
                df.at[i, 'ext_room_skipped'] = t

        # ----------------------------------------------------------------------
        # Create ext_beeps to indicate number of beeps (1 = green, 2 = yellow)
        # ----------------------------------------------------------------------
        try:
            for i, r in df[df['data_beep_x'].notnull()].iterrows():
                if r['data_message'] == 'Beep':
                    df.at[i, 'ext_beeps'] = 1
                elif r['data_message'] == 'Beep Beep':
                    df.at[i, 'ext_beeps'] = 2
        except KeyError as e:
            write_error('No beep events in file')
            continue

        # ----------------------------------------------------------------------
        # Determines number of victims per room by color and stores the data in
        # room_victims. This is only the truth at the beginning of the game.
        # Unfortunately this data will change as the game progresses, which we
        # handle later. Sample data:
        # 'acr': {'Green': 0, 'Yellow': 1, 'type': 1},
        # 'br': {'Green': 2, 'Yellow': 1, 'type': 3}
        # ----------------------------------------------------------------------
        def get_room_id(name):
            # Correct variances in the naming scheme
            if name == 'The Computer Farm': name = 'Computer Farm'
            if name == 'Open Break Area': name = 'Break Room'
            if name == 'Janitor': name = "Janitor's Closet"
            for key, item in rooms[complexity].items():
                if item['name'] == name:
                    return key
            print("ERROR: Could not find room name", name, "-- check semantic map", complexity)
            sys.exit()
        def update_room_types(room_victims):
            for k, v in room_victims.items():
                if   v['Yellow'] == 0 and v['Green'] == 0: v['type'] = 0
                elif v['Yellow'] >  0 and v['Green'] == 0: v['type'] = 1
                elif v['Yellow'] == 0 and v['Green'] >  0: v['type'] = 2
                elif v['Yellow'] >  0 and v['Green'] >  0: v['type'] = 3
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

        # ----------------------------------------------------------------------
        # Fills the event rows that have blank values with their values from the previous row
        # cols = ['data_x', 'data_y', 'data_z', 'data_mission_timer', 'data_blocks']
        # ----------------------------------------------------------------------
        print("Setting player coordinates and elapsed time...")
        cols = ['data_x', 'data_y', 'data_z', 'data_mission_timer']
        df.loc[:,cols] = df.loc[:,cols].ffill()

        # ----------------------------------------------------------------------
        # Creates 'ext_seconds_remaining' based on time from mission start
        # Return the number of seconds, expecting the format 'mm : ss'
        # ----------------------------------------------------------------------
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

        # ----------------------------------------------------------------------
        # Find out what index number yellow victims expire at and store it in
        # expire_index.
        # ----------------------------------------------------------------------
        expire_index = df['data_expired_message'][df['data_expired_message'].notnull()].index.values[0]

        # ----------------------------------------------------------------------
        # Create 'ext_event' for 'room_entered' or 'victim_triaged', the only
        # two events that matter for most calculations later.
        # ----------------------------------------------------------------------
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

        # ----------------------------------------------------------------------
        # Determine the location of the next victim
        # ----------------------------------------------------------------------
        df['ext_next_victim_x'] = df['data_victim_x'].bfill()
        df['ext_next_victim_y'] = df['data_victim_y'].bfill()
        df['ext_next_victim_z'] = df['data_victim_z'].bfill()

        # ----------------------------------------------------------------------
        # Determine the victims and openings in view at any moment and put into
        # 'ext_victims_in_view' and 'ext_blockages_in_view'.
        # ----------------------------------------------------------------------
        print("Creating victims and blockages in view...")
        df['ext_victims_in_view'] = np.NaN
        df['ext_victims_in_view'] = df['ext_victims_in_view'].astype('object')
        def find_victims_in_view(r, blocks):
            vl = []
            for b in blocks:
                if b['type'].startswith('block_victim'):
                    (x, y, z) = b['location']
                    vl.append((x, y, z))
                    # Set the first time the victim was seen
                    if 'first_seen' not in victim_list[(x, y, z)]:
                        victim_list[(x, y, z)]['first_seen'] = r['ext_seconds_remaining']
                    # print(f"I am in room {r['ext_room_id']} and I see a victim in room", victim_list[(x,y,z)]['room'])
            return vl
        # For openings, we simply need to know if they saw any openings or not
        def find_openings_in_view(r, blocks):
            for b in blocks:
                if b['type'] == 'perturbation_opening':
                    return 1
            return 0
        for i, r in df.iterrows():
            if r['topic'] == 'agent/pygl_fov/player/3d/summary':
                df.at[i, 'ext_victims_in_view'] = find_victims_in_view(r,
                    blocks=r['data_blocks'])
                df.at[i, 'ext_openings_in_view'] = find_openings_in_view(r,
                    blocks=r['data_blocks'])

        # ----------------------------------------------------------------------
        # Determine average time between yellow victims entering the FoV for the
        # first time, and also green victims.
        # ----------------------------------------------------------------------
        vlast = {"Green": None, "Yellow": None}
        vtime = {"Green": 0, "Yellow": 0}
        vnumber = {"Green": 0, "Yellow": 0}
        for k, v in sorted(victim_list.items(), key=lambda x: x[1].get('first_seen', 1000), reverse=True):
            if 'first_seen' not in v: continue
            c = v['color']
            if vlast[c] is None:
                vlast[c] = v['first_seen']
                continue
            vtime[c] += (vlast[c] - v['first_seen'])
            vlast[c] = v['first_seen']
            vnumber[c] += 1
        green_search_time = vtime['Green'] / vnumber['Green']
        yellow_search_time = vtime['Yellow'] / vnumber['Yellow']

        # ----------------------------------------------------------------------
        # Determine victims seen since last room_entered event and put them in 'ext_victims_seen'
        # ----------------------------------------------------------------------
        print("Determining victims seen since last room entered event...")
        df['ext_victims_seen'] = np.NaN
        df['ext_victims_seen'] = df['ext_victims_seen'].astype('object')
        vl = set()
        openings_seen = False
        for i, r in df.iterrows():
            # If it's a room entered event, put the list of victims seen in the
            # dataframe, reset the victim list, and continue
            if r['ext_event'] == 'room_entered':
                # print("ENTERED:", r['data_entered_area_id'])
                # for v in sorted(list(vl)):
                #     print('--SEEN IN ROOM:', victim_list[v]['room'])
                df.at[i, 'ext_victims_seen'] = sorted(list(vl))
                df.at[i, 'ext_openings_seen'] = openings_seen
                vl = set()
                openings_seen = False
                continue
            # If there are victims in view, process
            if isinstance(r['ext_victims_in_view'], list):
                for v in r['ext_victims_in_view']: vl.add(v)
            # See if any openings were viewed
            if r['ext_openings_in_view'] == 1:
                openings_seen = True

        # ----------------------------------------------------------------------
        # Determine rooms skipped since last room_entered event put them in
        # 'ext_rooms_skipped'. This will be a list of room ids, and is very
        # convenient for later to determine, when a room is entered, what rooms
        # have been skipped since the last room was entered.
        # ----------------------------------------------------------------------
        print("Determining rooms skipped since last room entered event...")
        df['ext_rooms_skipped'] = np.NaN
        df['ext_rooms_skipped'] = df['ext_rooms_skipped'].astype('object')
        vl = {}
        for i, r in df.iterrows():
            # If it's a room entered event, put the list of rooms triggered in the dataframe,
            # reset the triggered list, and continue
            if r['ext_event'] == 'room_entered':
                if len(vl) == 0:
                    df.at[i, 'ext_rooms_skipped'] = []
                vlx = []
                for k, v in vl.items():
                    vlx.append({'id': k, 'type': v})
                df.at[i, 'ext_rooms_skipped'] = vlx
                vl = {}
                continue
            # If there is no room skipped, continue
            if r['ext_room_skipped'] is None: continue
            # Add the room skipped to the set, accounting for the fact that
            # if it's after five minutes, all yellow victims are expired
            id = r['ext_room_skipped']
            if i < expire_index:
                vl[id] = room_victims[id]['type']
            else:
                green = room_victims[id]['Green']
                if green == 0: vl[id] = 0
                else: vl[id] = 2

        # ----------------------------------------------------------------------
        # Create a new df, event_df, to contain all event rows with events. This
        # df is a *copy* of the original df. We should not have to work with the
        # original df at all from here out, every variable that we need should
        # be in the rows of event_df, and it makes it much faster to process
        # now that we don't need the extra 30,000+ rows of the original df.
        # ----------------------------------------------------------------------
        event_df = df[(df['ext_event']=='victim_triaged') |
            (df['ext_event']=='room_entered')].copy()

        # ----------------------------------------------------------------------
        # SANITY CHECK: Was the player actually in a room that is on the
        # trigger list if a victim was triaged?
        # ----------------------------------------------------------------------
        is_error = False
        try:
            for i, row in event_df.iterrows():
                if row['ext_event'] != 'victim_triaged': continue
                if rooms[complexity][row['ext_sanity_room_loc']]['name'] not in sanity_rooms[complexity]:
                    write_error(f"***ERROR***: {i} :: SANITY ROOM {rooms[complexity][row['ext_sanity_room_loc']]['name']} NOT IN TRIGGER ROOMS")
                    is_error = True
                    break
        except Exception as e:
            pass
        if is_error: continue

        # ----------------------------------------------------------------------
        # Fill in empty scores
        # ----------------------------------------------------------------------
        event_df['data_score'].fillna(method='ffill', inplace=True)
        event_df['data_score'].fillna(value=0, inplace=True)

        # ----------------------------------------------------------------------
        # Determine the distance to the next victim and put in ext_next_victim_distance
        # ----------------------------------------------------------------------
        event_df['ext_next_victim_distance'] = (
            ((event_df['data_x']-event_df['ext_next_victim_x'])**2+
            (event_df['data_z']-event_df['ext_next_victim_z'])**2+
            (event_df['data_y']-event_df['ext_next_victim_y'])**2)
            **(1/2))

        # ----------------------------------------------------------------------
        # Determine yellow victims remaining at each point and put in
        # ext_total_yellow_victims_remaining
        # ----------------------------------------------------------------------
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

        # ----------------------------------------------------------------------
        # Determine green and yellow victims in current room, and other
        # calculations that rely on the current state of a room (not the original
        # state of the room). This is where things can get a little dicey.
        # tmp_room_victims is a deepcopy of the original room_victims, and
        # tmp_room_victims will change every time a victim is triaged (or dies).
        # ----------------------------------------------------------------------
        tmp_room_victims = copy.deepcopy(room_victims)
        last_room_type = 0
        cum_empty = 0
        cum_full = 0
        event_df['ext_exited_room_type'] = np.NaN
        for i, row in event_df.iterrows():
            r = row['ext_room_id']
            if row['ext_event'] == 'room_entered':
                # Set ext_exited_room_type to the type of room they just left
                event_df.at[i, 'ext_exited_room_type'] = last_room_type
                # If there are skipped rooms, update those types as well
                if isinstance(row['ext_rooms_skipped'], list):
                    for j, s in enumerate(row['ext_rooms_skipped']):
                        event_df.at[i, 'ext_rooms_skipped'][j]['type'] = tmp_room_victims[s['id']]['type']
                # Set cumulative totals of types of rooms
                if tmp_room_victims[r]['type'] == 0: cum_empty += 1
                else: cum_full += 1
                event_df.at[i, 'ext_rooms_entered_empty'] = cum_empty
                event_df.at[i, 'ext_rooms_entered_not_empty'] = cum_full
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
            # The type of room that it is has to be updated at each point
            update_room_types(tmp_room_victims)
            last_room_type = tmp_room_victims[r]['type']
            event_df.at[i, 'ext_room_type'] = last_room_type

        # ----------------------------------------------------------------------
        # Determine who was left behind when leaving a room.
        # ----------------------------------------------------------------------
        # Copy the victims seen into a left-behind column
        event_df['ext_left_behind'] = event_df['ext_victims_seen']
        # First we have to remove any triaged victim from any *future* left-
        # behind information, since they are not left behind.
        for i, vt_row in event_df[event_df['ext_event']=='victim_triaged'].iterrows():
            loc = (vt_row['data_victim_x'], vt_row['data_victim_y'], vt_row['data_victim_z'])
            # Look at every room entered event after the victim triaged event
            for j, re_row in event_df[event_df['ext_event']=='room_entered'].iterrows():
                if j < i: continue
                if loc in re_row['ext_left_behind']:
                    re_row['ext_left_behind'].remove(loc)
        # Now we have to calculate anyone from the left-behind list that was in
        # the room they just exited
        for i, r in event_df[event_df['ext_event']=='room_entered'].iterrows():
            (g, y) = (0, 0)
            for v in r['ext_left_behind']:
                if victim_list[v]['room'] == r['data_exited_area_id']:
                    if victim_list[v]['color'] == 'Green': g += 1
                    elif victim_list[v]['color'] == 'Yellow': y += 1
            event_df.at[i, 'ext_left_behind_green'] = g
            event_df.at[i, 'ext_left_behind_yellow'] = y

        # ----------------------------------------------------------------------
        # Determine victim strategy at each event. This logic encapsulates the
        # New Victim Strategies tab.
        # ----------------------------------------------------------------------
        def compute_victim_strategy(c, r):
            (y, m, s, g) = ('Yellow Only', 'Mixed', 'Sequential', 'Green Only')
            if   c == 'Yellow Only': p = [y, m, y, y, m, m]
            elif c == 'Sequential':  p = [s, s, s, y, m, g]
            elif c == 'Mixed':       p = [m, m, s, y, m, g]
            elif c == 'Green Only':  p = [m, g, g, m, m, g]
            if r['ext_event'] == 'victim_triaged':
                if r['data_color'] == 'Yellow': return p[0]
                if r['data_color'] == 'Green': return p[1]
            if r['ext_exited_room_type'] == 0: return p[2]
            if r['ext_exited_room_type'] == 2: return p[3]
            if r['ext_exited_room_type'] == 3: return p[4]
            if r['ext_exited_room_type'] == 1: return p[5]
            raise Exception(f"ERROR: Could not determine victim strategy, current: {current_strategy}, color: {r['data_color']}, exited: {r['ext_exited_room_type']}")
        victim_strategy = orig_victim_strategy
        for i, row in event_df.iterrows():
            if i >= expire_index:
                victim_strategy = 'Green Only'
            else:
                victim_strategy = compute_victim_strategy(victim_strategy, row)
            event_df.at[i, 'ext_victim_strategy'] = victim_strategy

        # ----------------------------------------------------------------------
        # Determine navigation strategy at each event. This logic encapsulates
        # the Navigation Strategy tab.
        # ----------------------------------------------------------------------
        def compute_nav_strategy(c, r):
            (y, m, s, a, g) = ('Yellow First', 'Mixed', 'Sequential', 'Avoid Empty', 'Green First')
            id = r['data_entered_area_id']
            # SKIP: 0 = None, 1 = Green Only, 2 = Yellow/Mixed, 3 = Empty
            skip = 0
            if isinstance(r['ext_rooms_skipped'], list):
                for x in r['ext_rooms_skipped']:
                    if skip == 2: continue
                    elif x['type'] in (1, 3): skip = 2
                    elif x['type'] == 2 and skip in (0, 3): skip = 1
                    elif x['type'] == 0 and skip == 0: skip = 3
            t = r['ext_room_type']
            # print("They entered room", id, "of type (",
            #     ('empty', 'yellow/mixed', 'green only', 'yellow/mixed')[int(t)],
            #     ") and skipped (",
            #     ('no', 'green only', 'yellow/mixed', 'empty')[skip], ") rooms"
            # )
            if c == 'Yellow First':
                if t in (1, 3): p = [y, y, m, a]
                elif t == 2:    p = [s, m, m, a]
                elif t == 0:    p = [s, m, m, m]
            elif c == 'Avoid Empty':
                if t in (1, 3): p = [a, y, m, a]
                elif t == 2:    p = [a, m, m, a]
                elif t == 0:    p = [s, m, m, m]
            elif c == 'Sequential':
                if t in (1, 3): p = [s, y, m, a]
                elif t == 2:    p = [s, m, m, a]
                elif t == 0:    p = [s, m, m, m]
            elif c == 'Green First':
                if t in (1, 3): p = [s, m, m, a]
                elif t == 2:    p = [g, m, m, g]
                elif t == 0:    p = [s, m, m, m]
            elif c == 'Mixed':
                if t in (1, 3): p = [m, y, m, a]
                elif t == 2:    p = [s, m, m, a]
                elif t == 0:    p = [s, m, m, m]
            return p[skip]
        nav_strategy = orig_nav_strategy
        for i, row in event_df.iterrows():
            # Do not calculate a navigation strategy unless they've entered a
            # room that specifically has a trigger point
            if row['data_entered_area_id'] not in trigger_rooms[complexity]:
                event_df.at[i, 'ext_nav_strategy'] = nav_strategy
                continue
            # print("TIME:", row['ext_seconds_remaining'])
            # print("ORIGINAL STRATEGY:", nav_strategy)
            nav_strategy = compute_nav_strategy(nav_strategy, row)
            # print("NEW STRATEGY:", nav_strategy)
            # print('-----------------')
            event_df.at[i, 'ext_nav_strategy'] = nav_strategy

        # ----------------------------------------------------------------------
        # FROM PABLO: Figure out prior use of device. Every time a participant skips
        # an empty room (i.e. player enters trigger block > no beep > does
        # not enter room), or a room inconsistent with current strategy
        # (e.g. current strategy = “yellow only”, player enters trigger
        # block > one beep (“green only room”) > does not enter room) 
        # Keep the running total of each one of those two things.
        # victim strategies: ('Yellow Only', 'Mixed', 'Sequential', 'Green Only')
        # ----------------------------------------------------------------------
        (consistent, inconsistent) = (0, 0)
        for i, row in event_df[event_df['ext_event']=='room_entered'].iterrows():
            vs = row['ext_victim_strategy']
            skipped = row['ext_rooms_skipped']
            if not isinstance(skipped, list): skipped = []
            for s in skipped:
                if s['type'] == 0: # Empty room
                    if vs in ('Sequential'): inconsistent += 1
                    else: consistent += 1
                elif s['type'] == 1: # Yellow only room
                    if vs in ('Yellow Only', 'Mixed', 'Sequential'): inconsistent += 1
                    else: consistent += 1
                elif s['type'] == 2: # Green Only room
                    if vs in ('Green Only', 'Mixed', 'Sequential'): inconsistent += 1
                    else: consistent += 1
                elif s['type'] == 3: # Both
                    inconsistent += 1
            event_df.at[i, 'ext_prior_use_consistent'] = consistent
            event_df.at[i, 'ext_prior_use_inconsistent'] = inconsistent

        # ----------------------------------------------------------------------
        # Determine time spent in each victim or nav strategy and points accumulated
        # per strategy, first five minutes only. As a shortcut, I am assuming
        # that the time of the mission is always 600 seconds (prev_sr) and that
        # victims expire at 300 seconds. If this turns out to not be the case
        # later, prev_sr will have to be calculated from the largest
        # ext_seconds_remaining and 300 will have to be changed to reflect the
        # ext_seconds_remaining at expire_index. Data is stored in vs_data.
        # Sample data:
        # 'Mixed': {'time_spent': 556.0, 'score': 230, 'points_per_minute': 46},
        # 'Yellow Only': {'time_spent': 34.0, 'score': , 'points_per_minute': }
        # ----------------------------------------------------------------------
        def get_strategy_data(event, strategy):
            prev_score = 0
            prev_sr = 600
            data = {}
            for i, row in event_df.loc[event_df['ext_event']==event].iterrows():
                vs = row[strategy]
                if vs not in data: data[vs] = {'time_spent': 0, 'score': 0}
                sr = row['ext_seconds_remaining']
                score = row['data_score']
                points_added = score - prev_score
                data[vs]['score'] += points_added
                if sr >= 300:
                    time_elapsed = prev_sr - sr
                    data[vs]['time_spent'] += time_elapsed
                    prev_sr = sr
                    prev_score = score
                else:
                    time_elapsed = prev_sr - 300
                    data[vs]['time_spent'] += time_elapsed
                    break
            return data
        nav_data = get_strategy_data('room_entered', 'ext_nav_strategy')
        vs_data = get_strategy_data('victim_triaged', 'ext_victim_strategy')

        # ----------------------------------------------------------------------
        # Determine yellow and green victims saved per minute, as well as expected
        # green rate.
        # ----------------------------------------------------------------------
        (green, yellow, yellow_rate) = (0, 0, 0)
        total_green = room_victims['total']['Green']
        for i, row in event_df.loc[event_df['ext_event']=='victim_triaged'].iterrows():
            if row['data_color'] == 'Green':
                green += 1
            else:
                yellow += 1
            # elapsed is the number of minutes that have elapsed since mission start
            elapsed = (600 - row['ext_seconds_remaining']) / 60
            green_rate = green / elapsed
            # Only calculate a new yellow rate if yellow victims have not expired
            if i < expire_index:
                yellow_rate = yellow / elapsed
            event_df.at[i, 'ext_yellow_per_minute'] = yellow_rate
            event_df.at[i, 'ext_green_per_minute'] = green_rate
            # Expected green victims saved per minute
            if total_green > (green / elapsed) * 5:
                event_df.at[i, 'ext_expected_green_rate'] = green_rate
            else:
                event_df.at[i, 'ext_expected_green_rate'] = (total_green - (green_rate * 5)) / 5

        # ----------------------------------------------------------------------
        # Calculate points per minute in each strategy
        # ----------------------------------------------------------------------
        for x in (vs_data, nav_data):
            for k, v in x.items():
                v['points_per_minute'] = v['score'] / (v['time_spent'] / 60)

        # ----------------------------------------------------------------------
        # Put in Q7 and Q8 survey responses
        # ----------------------------------------------------------------------
        def get_average_response(colname):
            cols = [col for col in survey_df if col.startswith(colname)]
            return survey_df[cols].mean(axis=1, skipna=True)[subject_id]
        q7_average = get_average_response('Q7_')
        q8_average = get_average_response('Q8_')

        # ----------------------------------------------------------------------
        # Create a final dictionary to hold all of the data
        # ----------------------------------------------------------------------
        final = {
            'member_id': member_id,
            'subject_id': subject_id,
            'trial_id': trial_id,
            'complexity': complexity,
            'training': training,
            'competency_score': competency_score,
            'final_score': final_score,
            'videogame_experience': videogame_experience,
            'q7_average': q7_average,
            'q8_average': q8_average,
            'workload': workload,
            'green_search_time': green_search_time,
            'yellow_search_time': yellow_search_time,
            'original_nav_strategy': orig_nav_strategy,
            'navigation_strategy_data': nav_data,
            'original_victim_strategy': orig_victim_strategy,
            'victim_strategy_data': vs_data,
            'events': [],
        }

        for i, row in event_df.iterrows():
            e = {
                'event': row['ext_event'],
                'room_id': row['ext_room_id'],
                'room_name': rooms[complexity][row['ext_room_id']]['name'],
                'sanity_room_name_actual': rooms[complexity][row['ext_sanity_room_loc']]['name'],
                'event_index_number': i,
                'seconds_remaining': row['ext_seconds_remaining'],
                'yellow_victims_in_current_room': row['ext_yellow_victims_in_current_room'],
                'green_victims_in_current_room': row['ext_green_victims_in_current_room'],
            }
            if row['ext_event'] == 'room_entered':
                e['nav_strategy'] = row['ext_nav_strategy']
                e['room_type'] = row['ext_room_type']
                e['exited_room_type'] = row['ext_exited_room_type']
                e['rooms_skipped'] = row['ext_rooms_skipped']
                e['rooms_entered_empty'] = row['ext_rooms_entered_empty']
                e['rooms_entered_not_empty'] = row['ext_rooms_entered_not_empty']
                e['prior_use_consistent'] = row['ext_prior_use_consistent']
                e['prior_use_inconsistent'] = row['ext_prior_use_inconsistent']
                e['left_behind_yellow'] = row['ext_left_behind_yellow']
                e['left_behind_green'] = row['ext_left_behind_green']
                e['openings_seen'] = row['ext_openings_seen']
            elif row['ext_event'] == 'victim_triaged':
                e['victim_strategy'] = row['ext_victim_strategy']
                e['victim_color'] = row['data_color']
                e['next_victim_distance'] = row['ext_next_victim_distance']
                e['total_yellow_victims_remaining'] = row['ext_total_yellow_victims_remaining']
                e['yellow_per_minute'] = row['ext_yellow_per_minute']
                e['green_per_minute'] = row['ext_green_per_minute']
                e['expected_green_rate'] = row['ext_expected_green_rate']
            else:
                print(f"EXCEPTION: Event {row['ext_event']} not recognized")
                sys.exit()
            final['events'].append(e)

        # ----------------------------------------------------------------------
        # Save the data to a JSON file
        # ----------------------------------------------------------------------
        print(f"Exporting {export_dir}/member_{member_id}_trial_{trial_id}_results.json")
        with open(f"{export_dir}/member_{member_id}_trial_{trial_id}_results.json", "w") as f:
            json.dump(final, f, indent=2, sort_keys=False)

    # --------------------------------------------------------------------------
    # Put the JSON files into two separate CSV files
    # --------------------------------------------------------------------------
    final_df, final_edf = (None, None)
    for name in glob.glob(export_dir+'/*.json'):
        print(name)
        with open(name) as f:
            data = json.load(f)
        events = data.pop('events')
        df = pd.json_normalize(data)
        edf = pd.json_normalize(events)
        edf['member_id'] = data['member_id']
        edf['trial_id'] = data['trial_id']
        final_df = df if final_df is None else final_df.append(df)
        final_edf = edf if final_edf is None else final_edf.append(edf)
    for col in ('trial_id', 'member_id'):
        x = final_edf[col]
        final_edf.drop(labels=[col], axis=1, inplace=True)
        final_edf.insert(0, col, x)
    final_df.to_csv(f'{export_dir}/results_data.csv', index=False)
    final_edf.to_csv(f'{export_dir}/results_events.csv', index=False)

if __name__ == "__main__":
    main()
