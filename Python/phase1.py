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
from pprint import pprint
from tqdm import tqdm
import math
import copy
import os

import competency_test_analysis as cta

root_dir = '/mnt/DARPA/CONSULTING/Analytics/Phase_1/Data'
# root_dir = '/home/erik_jones/git/asist_data'
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

def duplicate_rv(rv):
    return copy.deepcopy(rv)

# Determines the type of each room.
# 0) no victims, 1) one or more yellow victims,
# 2) One or more green victims, 3) a mix of green and yellow.
def update_room_types(rv):
    (total_y, total_g) = (0, 0)
    for k, v in rv.items():
        if   v['Yellow'] == 0 and v['Green'] == 0: v['type'] = 0
        elif v['Yellow'] >  0 and v['Green'] == 0: v['type'] = 1
        elif v['Yellow'] == 0 and v['Green'] >  0: v['type'] = 2
        elif v['Yellow'] >  0 and v['Green'] >  0: v['type'] = 3
        if k != 'total':
            total_y += v['Yellow']
            total_g += v['Green']
    rv['total'] = {'Green': total_g, 'Yellow': total_y, 'type': 3}

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
    begin_parsing = False
    for name in sorted(glob.glob(trial_dir+'/*.metadata')):
        fname = name.replace(trial_dir, "")

        # if 'Trial-130_' not in name: continue
        # if 'Trial-128_' in name:
        #     begin_parsing = True
        #     continue
        # if begin_parsing is False: continue


        # ----------------------------------------------------------------------
        # Get the information out of the filename
        # ----------------------------------------------------------------------
        s = re.search(r'TrialMessages_CondBtwn-(.*)_CondWin-Falcon(.*)-(.*)_Trial-(.*)_Team.*_Member-(.*)_', name)
        member_id = s.group(5)
        trial_id = s.group(4)
        complexity = s.group(2)
        training = s.group(1) + ' ' + s.group(3)
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
        # only topic, data, and msg.
        # ----------------------------------------------------------------------
        print(f'------------------\nFILE: {name}\nProcessing {member_id}...')
        print("Loading JSON...")
        with open(trial_dir+fname) as f:
            orig_data = json.loads("[" + f.read().replace("}\n{", "},\n{") + "]")
        data = []
        god_accounts = ("ASIST2", "ASIST3", "ASIST6", "ASU_MC")
        start_data = False
        try:
            for line in orig_data:
                # Don't process lines before the mission timer starts
                if start_data is False:
                    if line['topic'] == 'observations/events/mission' and line['data']['mission_state'] == 'Start':
                        start_data = True
                    else:
                        if line['topic'] != 'ground_truth/mission/victims_list':
                            continue
                # Skip the God accounts
                if line.get('name', None) in god_accounts:
                    continue
                if line['data'].get('name', None) in god_accounts:
                    continue
                if line['data'].get('playername', None) in god_accounts:
                    continue
                if line['topic'] == 'observations/events/scoreboard':
                    for g in god_accounts:
                        line['data']['scoreboard'].pop(g, None)
                data.append({
                    'data': line['data'],
                    'topic': line['topic'],
                    'msg': line['msg']
                })
        except Exception as e:
            write_error("It looks like the original metadata file is corrupted")
            continue

        # for i, d in enumerate(data):
        #     if d['topic'] == 'observations/events/mission':
        #         pprint(d, indent=2)
        #         print('----------------------')
        # sys.exit()

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

        # ----------------------------------------------------------------------
        # Create all of the data from the map information, including room
        # information and coordinates.
        # ----------------------------------------------------------------------
        print("Creating map data...")
        map = copy.deepcopy(orig_map)
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
        # Subject id is the same as the index in survey_df, column Q5.
        # NOTE: Trial data is sometimes bad, so using this naive apprach instead
        # ----------------------------------------------------------------------
        # for i, r in df.loc[df['data_subjects'].notnull()].iterrows():
        #     subject_id = r['data_subjects'][0]
        #     break
        subject_id = 'P' + str(member_id).zfill(6)

        # ----------------------------------------------------------------------
        # Get their workload from the survey. The numbers correspond to
        # the order of three columns in the order of Easy, Medium, and Hard. If
        # the numbers are 213, the order of those three columns are Q212=Medium,
        # Q221=Easy, Q230=Hard. Start with getting Column o, and turning it into
        # a three-digit string. Also get original strategies.
        # ----------------------------------------------------------------------
        try:
            # Correct that these look like dates, i.e. 01/02/2003
            o = survey_df.at[subject_id, 'o'].replace('/', '').replace('200', '').replace('0', '')
            if len(o) != 3:
                print("o is not three characters long:", o)
                sys.exit()
            # Figure out which number to look for based on the complexity
            diff_num = {'Easy': '1', 'Medium': '2', 'Hard': '3'}[complexity]
            o_index = int(o.index(diff_num))
            #
            # print('o:', o, 'diff_num:', diff_num, 'comp:', complexity, 'o_index:', o_index)
            #
            workload_column = ('Q212', 'Q221', 'Q230')[o_index]
            workload = int(survey_df.at[subject_id, workload_column])
            vs_column = ('Q208_vic', 'Q217_vic', 'Q226_vic')[o_index]
            orig_victim_strategy = survey_df.at[subject_id, vs_column]
            ns_column = ('Q208_Nav2', 'Q217_Nav2', 'Q226_Nav2')[o_index]
            orig_nav_strategy = survey_df.at[subject_id, ns_column]
            if orig_victim_strategy == 'Insufficient':
                orig_victim_strategy = 'Sequential'
            if orig_nav_strategy == 'Insufficient':
                orig_nav_strategy = 'Sequential'
        except KeyError as e:
            workload = None
            orig_victim_strategy = 'Sequential'
            orig_nav_strategy = 'Sequential'

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
        try:
            videogame_experience = calculate_experience()
        except Exception as e:
            videogame_experience = None

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
        # Remove Right Hallway ('rh') only.
        # ----------------------------------------------------------------------
        if 'rh' in trigger_rooms[complexity]:
            trigger_rooms[complexity].remove('rh')
        for k, v in coordinates[complexity].items():
            if 'trigger' in v:
                if v['trigger'] == 'rh':
                    v.pop('trigger')

        # ----------------------------------------------------------------------
        # Correct the bug where a player triages a victim but is not in the room
        # where the player is. This inserts room location data at the previous
        # location message, using the room where the victim is triaged.
        # ----------------------------------------------------------------------
        print("Correcting location errors...")
        try:
            last_loc_i = 0
            room = None
            for i, r in df.iterrows():
                if (
                    r['data_locations'] not in (np.nan, np.NaN, '', 'nan', 'NaN') and
                    r['topic'] == 'observations/events/player/location'
                ):
                    room = r['data_locations'][0]['id']
                    if room == 'UNKNOWN': room = None
                elif (
                    r['data_connections'] != np.NaN
                    and r['data_locations'] in (np.nan, np.NaN, '', 'nan', 'NaN')
                    and r['topic'] == 'observations/events/player/location'
                ):
                    # print(i, ': misfire:', r['data_connections'])
                    last_loc_i = i
                elif (r['data_triage_state']=='SUCCESSFUL'):
                    loc = (r['data_victim_x'], r['data_victim_y'], r['data_victim_z'])
                    # print(i, ':', 'Triage in room', victim_list[loc]['room'])
                    if room != victim_list[loc]['room']:
                        # print("**********NO MATCH", last_loc_i)
                        df.at[last_loc_i, 'data_locations'] = [{'id': victim_list[loc]['room']}]
        except Exception as e:
            write_error("There was an error in the location data that could not be resolved")
            continue

        # ----------------------------------------------------------------------
        # Create room entered and exited events, as well as the last and next room.
        # ----------------------------------------------------------------------
        last_room = ''
        last_i = -1
        for x in ('data_entered_area_id', 'data_exited_area_id', 'ext_last_room_id',
            'ext_next_room_id', 'ext_sanity_room_loc'
        ):
            df[x] = None # Always best practice to pre-populate non-numerical columns
        entered_a_room = False
        try:
            for i, r in df.loc[df['data_locations'].notnull()].iterrows():
                loc = r['data_locations'][0]['id']
                if loc == 'UNKNOWN': continue
                # We only want parent rooms
                if loc in room_to_parent[complexity]:
                    loc = room_to_parent[complexity][loc]
                # A sanity check for what room we are in from original messages
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
        except Exception as e:
            write_error("There is no location data in the file")
            continue
        # If they never entered a room, the data must be bad
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
        print("Creating room_victims list...")
        room_victims = {'total': {'Green': 0, 'Yellow': 0, 'type': 0}}
        for v in df['data_mission_victim_list'][df['data_mission_victim_list'].notnull()].values[0]:
            r = v['room_name']
            room_id = get_room_id(r)
            if room_id not in room_victims:
                room_victims[room_id] = {'Green': 0, 'Yellow': 0, 'type': 0}
            if v['block_type'] == 'block_victim_1':
                room_victims[room_id]['Green'] += 1
            elif v['block_type'] == 'block_victim_2':
                room_victims[room_id]['Yellow'] += 1
        update_room_types(room_victims)
        # Create rooms in room_victims for rooms with zero victims
        for id, r in rooms[complexity].items():
            if id not in room_victims:
                if id in room_to_parent[d]:
                    x = room_to_parent[d][id]
                    if x not in room_victims:
                        room_victims[x] = {'Green': 0, 'Yellow': 0, 'type': 0}
                else:
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
        # 'ext_victims_in_view' and 'ext_blockages_in_view'. Also add the time
        # in seconds remaining that the victim was first seen.
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
        # first time, and also green victims. Insert it into the events list.
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
            if vnumber['Green'] > 0:
                v['green_search_time'] = vtime['Green'] / vnumber['Green']
            else:
                v['green_search_time'] = None
            if vnumber['Yellow'] > 0:
                v['yellow_search_time'] = vtime['Yellow'] / vnumber['Yellow']
            else:
                v['yellow_search_time'] = None
        df['ext_green_search_time'] = np.NaN
        df['ext_yellow_search_time'] = np.NaN
        for i, r in df[(df['ext_event']=='victim_triaged') | (df['ext_event']=='room_entered')].iterrows():
            sr = r['ext_seconds_remaining']
            if sr in (None, '', np.NaN, np.nan) or sr > 600:
                df.at[i, 'ext_green_search_time'] = None
                df.at[i, 'ext_yellow_search_time'] = None
                continue
            # print('-------------------')
            # print('sr from events:', sr)
            for k, v in sorted(victim_list.items(), key=lambda x: x[1].get('first_seen', 1000), reverse=True):
                fs = v.get('first_seen', None)
                gst = v.get('green_search_time', None)
                yst = v.get('yellow_search_time', None)
                if fs is None: continue
                if sr <= fs:
                    # print('fs:', fs, 'gst:', gst, 'yst:', yst)
                    df.at[i, 'ext_green_search_time'] = gst
                    df.at[i, 'ext_yellow_search_time'] = yst
        df['ext_green_search_time'].fillna(method='ffill', inplace=True)
        df['ext_yellow_search_time'].fillna(method='ffill', inplace=True)

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
                    continue
                vlx = []
                for k, v in vl.items():
                    # Can't have skipped current room
                    if r['ext_room_id'] == k: continue
                    vlx.append({'id': k, 'index': i})
                df.at[i, 'ext_rooms_skipped'] = vlx
                vl = {}
                continue
            # If there is no room skipped, continue
            if r['ext_room_skipped'] is None: continue
            # Add the room skipped to the set, accounting for the fact that
            # if it's after five minutes, all yellow victims are expired
            # NOTE: We are NOT saving the type of room that was skipped here
            # because we have to account for it later in the time-based system.
            # Instead we are saving the index row of when the room was skipped.
            vl[r['ext_room_skipped']] = i

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
        # trigger list if a victim was triaged? Was the room containing the
        # victim that was triaged actually the room the player was in?
        # ----------------------------------------------------------------------
        # is_error = False
        # try:
        #     for i, row in event_df.iterrows():
        #         if row['ext_event'] != 'victim_triaged': continue
        #         # print("In room:", row['ext_room_id'], "Victim in:", victim_list[coords]['room'])
        #         if rooms[complexity][row['ext_sanity_room_loc']]['name'] not in sanity_rooms[complexity]:
        #             write_error(f"***ERROR***: {i} :: SANITY ROOM {rooms[complexity][row['ext_sanity_room_loc']]['name']} NOT IN TRIGGER ROOMS")
        #             is_error = True
        #             break
        #         coords = (row['data_victim_x'], row['data_victim_y'], row['data_victim_z'])
        #         if row['ext_room_id'] != victim_list[coords]['room']:
        #             write_error(f"***ERROR***: {i} :: Player was in room {row['ext_room_id']} but victim was in {victim_list[coords]['room']}")
        #             is_error = True
        #             break
        # except Exception as e:
        #     pass
        # if is_error: continue

        # ----------------------------------------------------------------------
        # Fill in empty scores and timers
        # ----------------------------------------------------------------------
        event_df['data_score'].fillna(method='ffill', inplace=True)
        event_df['data_score'].fillna(value=0, inplace=True)
        event_df['ext_seconds_remaining'].fillna(value=600, inplace=True)

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
        # Let's try something different. Let's create a time series list of
        # of room_victims. This will be a of room_victims dictionaries but
        # specifically with the starting and ending index numbers that it's
        # good for. Then later we can find the specific room_victims dictionary
        # that we need for any given moment.
        # { 'i_begin': 16173,
        # 'i_end': 16750,
        # 'room_victims': { 'acr': {'Green': 0, 'Yellow': 0, 'type': 0},
        #                   'br': {'Green': 2, 'Yellow': 0, 'type': 2},
        # ----------------------------------------------------------------------
        rownums = list(event_df[event_df['ext_event']=='victim_triaged'].index)
        tsrv = [] # stands for time series room victims
        tmp_room_victims = duplicate_rv(room_victims)
        for i, row in event_df[event_df['ext_event']=='victim_triaged'].iterrows():
            r = row['ext_room_id']
            if len(tsrv) == 0:
            # Put a clean copy of room_victims at the start
                tsrv.append({
                    'i_begin': 1, # It starts at the beginning
                    'i_end': i-1, # It ends at the previous row
                    'room_victims': duplicate_rv(tmp_room_victims)
                } )
            if rownums.index(i) + 1 == len(rownums):
                next_i = 999999
            else:
                next_i = rownums[rownums.index(i) + 1] - 1
            # Else if the triaged victim was yellow, decrease yellows by 1
            if row['data_color'] == 'Yellow':
                tmp_room_victims[r]['Yellow'] -= 1
            # If the triaged victim was green, decrease greens by 1
            elif row['data_color'] == 'Green':
                tmp_room_victims[r]['Green'] -= 1
            # The type of room that it is has to be updated at each point
            update_room_types(tmp_room_victims)
            if not i < expire_index < next_i:
                tsrv.append({
                    'i_begin': i, # It starts now, at this row index
                    'i_end': next_i, # It ends at the next row index
                    'room_victims': duplicate_rv(tmp_room_victims)
                } )
                continue
            else:
                tsrv.append({
                    'i_begin': i, # It starts now, at this row index
                    'i_end': expire_index - 1, # It ends before the expire_index
                    'room_victims': duplicate_rv(tmp_room_victims)
                } )
                for k, v in tmp_room_victims.items():
                    if 'Yellow' in v: v['Yellow'] = 0
                update_room_types(tmp_room_victims)
                tsrv.append({
                    'i_begin': expire_index, # It starts at the expire_index
                    'i_end': next_i, # It ends at the next row index
                    'room_victims': duplicate_rv(tmp_room_victims)
                } )

        # ----------------------------------------------------------------------
        # Update the type of room that was skipped at each point
        # ----------------------------------------------------------------------
        def get_room_victims(rownum):
            for x in tsrv:
                if x['i_begin'] <= rownum <= x['i_end']:
                    return x['room_victims']
            print("ERROR: No room victims found.")
            print("i is", i)
            pprint(tsrv)
            sys.exit()
        for i, row in event_df[event_df['ext_event']=='room_entered'].iterrows():
            for room in row['ext_rooms_skipped']:
                # rv is the room_victims list for this exact moment in time
                rv = get_room_victims(room['index'])
                room['type'] = rv[room['id']]['type']

        # ----------------------------------------------------------------------
        # Determine green and yellow victims in current room, and other
        # calculations that rely on the current state of a room (not the original
        # state of the room).
        # ----------------------------------------------------------------------
        last_room_id = None
        cum_empty = 0
        cum_full = 0
        event_df['ext_exited_room_type'] = np.NaN
        for i, row in event_df[event_df['ext_event']=='room_entered'].iterrows():
            rv = get_room_victims(i)
            r = row['ext_room_id']
            # Set cumulative totals of types of rooms
            if rv[r]['type'] == 0: cum_empty += 1
            else: cum_full += 1
            event_df.at[i, 'ext_rooms_entered_empty'] = cum_empty
            event_df.at[i, 'ext_rooms_entered_not_empty'] = cum_full
            # Set number of victims in current room
            event_df.at[i, 'ext_yellow_victims_in_current_room'] = rv[r]['Yellow']
            event_df.at[i, 'ext_green_victims_in_current_room'] = rv[r]['Green']
            # Set room types of this room and last room
            event_df.at[i, 'ext_room_type'] = rv[r]['type']
            if last_room_id is not None:
                # print(f"i {i} thisroom {r} thistype {rv[r]['type']} lastroom {last_room_id} lasttype {rv[last_room_id]['type']}")
                event_df.at[i, 'ext_exited_room_type'] = rv[last_room_id]['type']
            last_room_id = r

        # ----------------------------------------------------------------------
        # Determine who was left behind when leaving a room.
        # ----------------------------------------------------------------------
        for i, row in event_df[event_df['ext_event']=='room_entered'].iterrows():
            rv = get_room_victims(i)
            r = row['data_exited_area_id']
            if r == '': continue
            event_df.at[i, 'ext_left_behind_green'] = rv[r]['Green']
            event_df.at[i, 'ext_left_behind_yellow'] = rv[r]['Yellow']

        # ----------------------------------------------------------------------
        # Determine victim strategy at each event. This logic encapsulates the
        # New Victim Strategies tab.
        # ----------------------------------------------------------------------
        def compute_victim_strategy(c, r):
            (y, m, s, g) = ('Yellow First', 'Mixed', 'Sequential', 'Green First')
            if   c == 'Yellow First': p = [y, m, y, y, m, m]
            elif c == 'Sequential':  p = [s, s, s, y, m, g]
            elif c == 'Mixed':       p = [m, m, s, y, m, g]
            elif c == 'Green First':  p = [m, g, g, m, m, g]
            if r['ext_event'] == 'victim_triaged':
                if r['data_color'] == 'Yellow': return p[0]
                if r['data_color'] == 'Green': return p[1]
            if r['ext_exited_room_type'] == 0: return p[2]
            if r['ext_exited_room_type'] == 2: return p[3]
            if r['ext_exited_room_type'] == 3: return p[4]
            if r['ext_exited_room_type'] == 1: return p[5]
            return c
            # raise Exception(f"ERROR: Could not determine victim strategy, current: {c}, color: {r['data_color']}, exited: {r['ext_exited_room_type']}")
        victim_strategy = orig_victim_strategy
        for i, r in event_df.iterrows():
            if i >= expire_index:
                victim_strategy = 'Green First'
            else:
                # print('--------------------')
                # print(f"i {i} event {r['ext_event']}")
                # print(f"old vs {victim_strategy}")
                # print(f"color {r['data_color']}")
                # print(f"exited room type {r['ext_exited_room_type']}")
                victim_strategy = compute_victim_strategy(victim_strategy, r)
                # print(f"new vs {victim_strategy}")
            event_df.at[i, 'ext_victim_strategy'] = victim_strategy

        # ----------------------------------------------------------------------
        # Determine navigation strategy at each event. This logic encapsulates
        # the Navigation Strategy tab.
        # ----------------------------------------------------------------------
        def compute_nav_strategy(c, r):
            (y, m, s, a, g) = ('Yellow First', 'Mixed', 'Sequential', 'Avoid Empty', 'Green First')
            id = r['data_entered_area_id']
            # Room and Skip Types: 0 = Empty, 1 = Yellow/Mixed, 2 = Green
            t = r['ext_room_type']
            if t == 3: t = 1 # Change Mixed (3) to Yellow/Mixed (1)
            skip = []
            if isinstance(r['ext_rooms_skipped'], list):
                for x in r['ext_rooms_skipped']:
                    ti = x['type']
                    if ti == 3: ti = 1 # Change Mixed (3) to Yellow/Mixed (1)
                    if ti not in skip: skip.append(ti)
            if c == y:
                if t == 1:
                    if len(skip) == 0: return y # 2
                    elif 1 in skip: return m # 3
                    elif 1 not in skip: return y # 4
                elif t == 2:
                    if len(skip) == 0: return s # 5
                    elif 1 not in skip and 2 not in skip: return a # 6
                    elif len(skip) == 1 and 1 in skip: return m # 7
                    elif 2 in skip: return m # 8
                    elif 2 not in skip: return g # 9
                elif t == 0:
                    if len(skip) == 0: return s # 10
                    elif len(skip) > 0: return m # 11
            elif c == a:
                if t == 1:
                    if len(skip) == 0: return a # 12
                    elif 1 not in skip and 2 not in skip: return a # 13
                    elif 1 in skip: return m # 14
                    elif 1 not in skip: return y # 15
                elif t == 2:
                    if len(skip) == 0: return a # 16
                    elif 1 not in skip and 2 not in skip: return a # 17
                    elif 2 in skip: return m # 18
                    elif 2 not in skip: return g # 19
                elif t == 0:
                    if len(skip) == 0: return s # 20
                    elif len(skip) > 0: return m # 21
            elif c == s:
                if t == 1:
                    if len(skip) == 0: return s # 22
                    elif 1 not in skip and 2 not in skip: return a # 23
                    elif 1 in skip: return m # 24
                    elif 1 not in skip: return y # 25
                elif t == 2:
                    if len(skip) == 0: return s # 26
                    elif 1 not in skip and 2 not in skip: return a # 27
                    elif 2 in skip: return m # 28
                    elif 2 not in skip: return g # 29
                elif t == 0:
                    if len(skip) == 0: return s # 30
                    elif len(skip) > 0: return m # 31
            elif c == g:
                if t == 1:
                    if len(skip) == 0: return s # 32
                    elif 1 not in skip and 2 not in skip: return a # 33
                    elif 1 in skip: return m # 34
                    elif 1 not in skip: return y # 35
                elif t == 2:
                    if len(skip) == 0: return g # 36
                    elif 2 in skip: return m # 37
                    elif 2 not in skip: return g # 38
                elif t == 0:
                    if len(skip) == 0: return s # 39
                    elif len(skip) > 0: return m # 40
            elif c == m:
                if t == 1:
                    if len(skip) == 0: return s # 41
                    elif 1 not in skip and 2 not in skip: return a # 42
                    elif 1 in skip: return m # 43
                    elif 1 not in skip: return y # 44
                elif t == 2:
                    if len(skip) == 0: return s # 45
                    elif 1 not in skip and 2 not in skip: return a # 46
                    elif 2 in skip: return m # 47
                    elif 2 not in skip: return m # 48
                elif t == 0:
                    if len(skip) == 0: return s # 49
                    elif len(skip) > 0: return m # 50
            print("ERROR: Nav Strategy not found")
            sys.exit()
        nav_strategy = orig_nav_strategy
        for i, row in event_df.iterrows():
            # Do not calculate a navigation strategy unless they've entered a
            # room that specifically has a trigger point
            if row['data_entered_area_id'] not in trigger_rooms[complexity]:
                event_df.at[i, 'ext_nav_strategy'] = nav_strategy
                continue
            nav_strategy = compute_nav_strategy(nav_strategy, row)
            event_df.at[i, 'ext_nav_strategy'] = nav_strategy

        # ----------------------------------------------------------------------
        # FROM PABLO: Figure out prior use of device. Every time a participant skips
        # an empty room (i.e. player enters trigger block > no beep > does
        # not enter room), or a room inconsistent with current strategy
        # (e.g. current strategy = “yellow only”, player enters trigger
        # block > one beep (“green only room”) > does not enter room) 
        # Keep the running total of each one of those two things.
        # victim strategies: ('Yellow First', 'Mixed', 'Sequential', 'Green First')
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
                    if vs in ('Yellow First', 'Mixed', 'Sequential'): inconsistent += 1
                    else: consistent += 1
                elif s['type'] == 2: # Green First room
                    if vs in ('Green First', 'Mixed', 'Sequential'): inconsistent += 1
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
        # 'Yellow First': {'time_spent': 34.0, 'score': , 'points_per_minute': }
        # ----------------------------------------------------------------------
        def get_strategy_data(event, strategy):
            prev_score = 0
            prev_sr = 600
            data = {}
            for i, row in event_df[event_df['ext_event']==event].iterrows():
                strat = row[strategy]
                if strat not in data: data[strat] = {'time_spent': 0, 'score': 0}
                sr = row['ext_seconds_remaining']
                score = row['data_score']
                points_added = score - prev_score
                data[strat]['score'] += points_added
                if sr >= 300:
                    time_elapsed = prev_sr - sr
                    data[strat]['time_spent'] += time_elapsed
                    prev_sr = sr
                    prev_score = score
                else:
                    time_elapsed = prev_sr - 300
                    data[strat]['time_spent'] += time_elapsed
                    break
            return data
        vs_data = get_strategy_data('victim_triaged', 'ext_victim_strategy')
        nav_data = get_strategy_data('room_entered', 'ext_nav_strategy')

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
                if v['time_spent'] != 0:
                    v['points_per_minute'] = v['score'] / (v['time_spent'] / 60)
                else:
                    v['points_per_minute'] = None

        # ----------------------------------------------------------------------
        # Put in Q7, Q8 and Q239 survey responses
        # ----------------------------------------------------------------------
        def get_average_response(colname):
            cols = [col for col in survey_df if col.startswith(colname)]
            return survey_df[cols].mean(axis=1, skipna=True)[subject_id]
        try:
            q7_average = get_average_response('Q7_')
            q8_average = get_average_response('Q8_')
        except Exception as e:
            q7_average = None
            q8_average = None
        q239 = survey_df.at[subject_id, 'Q239_new']

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
            'q239': q239,
            'workload': workload,
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
                'green_search_time': row['ext_green_search_time'],
                'yellow_search_time': row['ext_yellow_search_time']
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
