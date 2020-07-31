import pandas as pd
import numpy as np
import datetime
import ast    # Using AST for parsing str values from json
import json
import re

def sat_tendency(filename, cols):
    
    df = pd.read_csv(filename)
    
    # Score dictionary. This is used to map the answers to their score
    sat_tendency_dictionary = {
        "Strongly disagree\n(1)": 1,
        "Disagree\n(2)": 2,
        "Somewhat disagree\n(3)": 3,
        "Somewhat agree\n(4)":4,
        "Agree\n(5)": 5,
        "Strongly agree\n(6)": 6,
        '-99': 0
    }
    
    cols = cols
    sat_tendency_df = df[cols].copy()
    # Maps answers to dictionary. Cleans the answers. 
    for col in sat_tendency_df[cols[1:]]:
        for key, answer in sat_tendency_dictionary.items():
            sat_tendency_df[col] = sat_tendency_df[col].replace(key, answer)
            
    # Calculates score
    score = 0
    for col in sat_tendency_df[cols[1:]]:
        temp_score = sat_tendency_df[col][2:]
        score += temp_score
                               
    subject_id = sat_tendency_df[cols[0]][2:]
    # New columns to DF
    sat_tendency_df['sati'] = score
    sat_tendency_df['subject_id'] = subject_id
    
    # Only keeping score
    sat_tendency_df = sat_tendency_df[['sati','subject_id']]
    sat_tendency_df = sat_tendency_df[2:].reset_index()
    
    return sat_tendency_df


def get_message_data(filename):
    
    messages = pd.read_json(filename, lines=True)
    
    events    = []
    mission_state = []
    timestamp = []
    x = [np.nan]
    y = [np.nan]
    z = [np.nan]
    yaw = [np.nan]
    pitch = [np.nan]
    motion_x = [np.nan]
    motion_y = [np.nan]
    motion_z = [np.nan]
    total_time = [np.nan]
    observation_number = [np.nan]
    life = [np.nan]
    entered_area_name = [np.nan]
    entered_area_id = [np.nan]
    exited_area_name = [np.nan]
    equipped_item_name = [np.nan]
    sprinting = [np.nan]
    door_y = [np.nan]
    door_x = [np.nan]
    door_z = [np.nan]
    data_open = [np.nan]
    woof_x = [np.nan]
    woof_y = [np.nan]
    woof_z = [np.nan]
    message = [np.nan]
    lever_x = [np.nan]
    lever_y = [np.nan]
    lever_z = [np.nan]
    powered = [np.nan]
    item_x = [np.nan]
    item_y = [np.nan]
    item_z = [np.nan]
    victim_x = [np.nan]
    victim_y = [np.nan]
    victim_z = [np.nan]
    triage_state = [np.nan]
    scoreboard = [np.nan]
    
    for event in messages['topic']:
            evt = event.split('/')[-1]
            events.append(evt)
    for idx, msg in messages['header'].iteritems():
        if idx == 0:
            temp_timestamp = msg.get('timestamp')
            temp_timestamp = datetime.datetime.strptime(temp_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp.append(temp_timestamp)
        elif idx > 0:
            temp_timestamp = msg.get('timestamp')
            if len(temp_timestamp) > 20:    # Because some timestamps have no microseconds
                temp_timestamp = datetime.datetime.strptime(temp_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                timestamp.append(temp_timestamp)
            else:
                # Removing the last character (Z) to keep just the seconds
                temp_timestamp = datetime.datetime.strptime(temp_timestamp[:-1], '%Y-%m-%dT%H:%M:%S')  
                timestamp.append(temp_timestamp)
                
    for idx, msg in messages['data'].iteritems():
        if idx > 0:
            try:
                temp_data_x = msg.get('x')
                if temp_data_x == None:
                    x.append(np.nan)
                else:
                    x.append(temp_data_x)
                temp_data_y = msg.get("y")
                y.append(temp_data_y)
                temp_data_z = msg.get("z")
                z.append(temp_data_z)
                temp_data_yaw = msg.get("yaw")
                if temp_data_yaw == None:
                    yaw.append(np.nan)
                else:
                    temp_data_yaw = float(temp_data_yaw)
                    yaw.append(temp_data_yaw)
                temp_data_pitch = msg.get("pitch")
                pitch.append(temp_data_pitch)
                temp_data_motion_x = msg.get("motion_x")
                motion_x.append(temp_data_motion_x)
                temp_data_motion_y = msg.get("motion_y")
                motion_y.append(temp_data_motion_y)
                temp_data_motion_z = msg.get("motion_z")
                motion_z.append(temp_data_motion_z)
                temp_data_total_time = msg.get("total_time")
                total_time.append(temp_data_total_time)
                temp_data_observation_number = msg.get("observation_number")
                if temp_data_observation_number == None:
                    observation_number.append(np.nan)
                else:
                    observation_number.append(temp_data_observation_number)
                temp_data_life = msg.get("life")
                life.append(temp_data_life)         
                temp_data_entered_area_name = msg.get("entered_area_name")
                entered_area_name.append(temp_data_entered_area_name)
                temp_data_entered_area_id = msg.get("entered_area_id")
                entered_area_id.append(temp_data_entered_area_id)
                temp_data_exited_area_name = msg.get("exited_area_name")
                exited_area_name.append(temp_data_exited_area_name)
                temp_data_equipped_item_name = msg.get("equippediteamname")
                equipped_item_name.append(temp_data_equipped_item_name)
                temp_data_sprinting = msg.get("sprinting")
                sprinting.append(temp_data_sprinting)
                temp_data_door_x = msg.get("door_x")
                door_x.append(temp_data_door_x)
                temp_data_door_y = msg.get("door_y")
                door_y.append(temp_data_door_y)
                temp_data_door_z = msg.get("door_z")
                door_z.append(temp_data_door_z)
                temp_data_open = msg.get("open")
                data_open.append(temp_data_open)
                temp_data_woof_x = msg.get("woof_x")
                woof_x.append(temp_data_woof_x)
                temp_data_woof_y = msg.get("woof_y")
                woof_y.append(temp_data_woof_y)
                temp_data_woof_z = msg.get("woof_z")
                woof_z.append(temp_data_woof_z)
                temp_data_message = msg.get("message")
                message.append(temp_data_message)
                temp_data_lever_x = msg.get("lever_x")
                lever_x.append(temp_data_lever_x)
                temp_data_lever_y = msg.get("lever_y")
                lever_y.append(temp_data_lever_y)
                temp_data_lever_z = msg.get("lever_z")
                lever_z.append(temp_data_lever_z)
                temp_data_powered = msg.get("powered")
                powered.append(temp_data_powered)
                temp_data_item_x = msg.get("item_x")
                item_x.append(temp_data_item_x)
                temp_data_item_y = msg.get("item_y")
                item_y.append(temp_data_item_y)
                temp_data_item_z = msg.get("item_z")
                item_z.append(temp_data_item_z)
                temp_data_victim_x = msg.get("victim_x")
                victim_x.append(temp_data_victim_x)
                temp_data_victim_y = msg.get("victim_y")
                victim_y.append(temp_data_victim_y)
                temp_data_victim_z = msg.get("victim_z")
                victim_z.append(temp_data_victim_z)
                temp_data_triage_state = msg.get("triage_state")
                triage_state.append(temp_data_triage_state)
                temp_data_scoreboard = msg.get("scoreboard")
                scoreboard.append(temp_data_scoreboard)
                temp_data_mission_state = msg.get('mission_state')
                mission_state.append(temp_data_mission_state)
            except AttributeError:
                x.append(np.nan)
                y.append(np.nan)
                z.append(np.nan)
                yaw.append(np.nan)
                pitch.append(np.nan)
                motion_x.append(np.nan)
                motion_y.append(np.nan)
                motion_z.append(np.nan)
                total_time.append(np.nan)
                observation_number.append(np.nan)
                life.append(np.nan)
                entered_area_name.append(np.nan)
                entered_area_id.append(np.nan)
                exited_area_name.append(np.nan)
                equipped_item_name.append(np.nan)
                sprinting.append(np.nan)
                door_y.append(np.nan)
                door_x.append(np.nan)
                door_z.append(np.nan)
                data_open.append(np.nan)
                woof_x.append(np.nan)
                woof_y.append(np.nan)
                woof_z.append(np.nan)
                message.append(np.nan)
                lever_x.append(np.nan)
                lever_y.append(np.nan)
                lever_z.append(np.nan)
                powered.append(np.nan)
                item_x.append(np.nan)
                item_y.append(np.nan)
                item_z.append(np.nan)
                victim_x.append(np.nan)
                victim_y.append(np.nan)
                victim_z.append(np.nan)
                triage_state.append(np.nan)
                scoreboard.append(np.nan)
                mission_state.append(np.nan)
                
    
    df = pd.DataFrame(list(zip(events, mission_state, timestamp, x, y, z, yaw, pitch, motion_x, motion_y, motion_z,
           total_time, observation_number, life, entered_area_name, entered_area_id, 
           exited_area_name, equipped_item_name, sprinting, door_x, door_y, door_z, data_open,
           woof_x, woof_y, woof_z, message, lever_x, lever_y, lever_z, powered, item_x, 
           item_y,item_z, victim_x, victim_y, victim_z, triage_state, scoreboard)),columns=['event','mission_state', 'timestamp', 'x', 'y', 'z', 'yaw', 'pitch', 
                                     'motion_x','motion_y', 'motion_z',
                                     'total_time', 'observation_number', 'life', 
                                     'entered_area_name', 'entered_area_id','exited_area_name',
                                     'equipped_item_name', 'sprinting', 'door_x', 'door_y',
                                     'door_z', 'data_open', 'woof_x', 'woof_y', 'woof_z',
                                     'message', 'lever_x', 'lever_y', 'lever_z', 'powered',
                                     'item_x', 'item_y', 'item_z', 'victim_x',' victim_y',
                                     'victim_z', 'triage_state', 'scoreboard'])
    
    return df
    
    
def get_area_information(filename):
    
    with open(filename) as json_data:
        data = json.load(json_data)

    agents = data
    
    areas_id = []
    areas_name = []
    areas_type = []
    areas_x1 = []
    areas_x2 = []
    areas_y1 = []
    areas_y2 = []   
    
    for area in agents['areas']:
        temp_area_id = area.get('id')
        areas_id.append(temp_area_id)
        temp_area_name = area.get('name')
        areas_name.append(temp_area_name)
        temp_area_type = area.get('type')
        areas_type.append(temp_area_type)
        temp_area_x1 = area.get('x1')
        areas_x1.append(temp_area_x1)
        temp_area_x2 = area.get('x2')
        areas_x2.append(temp_area_x2)
        temp_area_y1 = area.get('y1')
        areas_y1.append(temp_area_y1)
        temp_area_y2 = area.get('y2')
        areas_y2.append(temp_area_y2) 
        
    areas = pd.DataFrame(list(zip(areas_id, areas_name, areas_type, areas_x1, areas_x2, areas_y1, areas_y2
                          )), columns=['areas_id', 'areas_name', 'areas_type', 'areas_x1', 'areas_x2', 'areas_y1', 'areas_y2'])
    
    return areas
    
def get_connections_information(filename):
    
    with open(filename) as json_data:
        data = json.load(json_data)

    agents = data

    connections_id = []
    connections_name = []
    connections_type = []
    connections_x1 = []
    connections_x2 = []
    connections_y1 = []
    connections_y2 = []
    connections_area1 = []
    connections_area2 = []

    for connection in agents['connections']:
        temp_connection_id = connection.get('id')
        connections_id.append(temp_connection_id)
        temp_connection_name = connection.get('name')
        connections_name.append(temp_connection_name)
        temp_connection_type = connection.get('type')
        connections_type.append(temp_connection_type)
        temp_connection_x1 = connection.get('x')
        connections_x1.append(temp_connection_x1)
        temp_connection_x2 = connection.get('x2')
        connections_x2.append(temp_connection_x2)
        temp_connection_y1 = connection.get('y')
        connections_y1.append(temp_connection_y1)
        temp_connection_y2 = connection.get('y2')
        connections_y2.append(temp_connection_y2)
        temp_connection_area1 = connection.get('area_1')
        connections_area1.append(temp_connection_area1)
        temp_connection_area2 = connection.get('area_2')
        connections_area2.append(temp_connection_area2)

        
    connections = pd.DataFrame(list(zip(connections_id, connections_name, connections_type, connections_x1, connections_x2, connections_y1, connections_y2, 
                                connections_area1, connections_area2)), columns=['connections_id', 'connections_name', 'connections_type', 
                                                                                 'connections_x1', 'connections_x2', 'connections_y1', 'connections_y2', 
                                                                                 'connections_area1', 'connections_area2'])
        
    return connections
    
def get_locations_information(filename):
    
    with open(filename) as json_data:
        data = json.load(json_data)

    agents = data 
    
    location_id = []
    location_area_id = []
    location_x = []
    location_y = []
    victim = []
    
    for location in agents['locations']:
        temp_location_id = location.get('id')
        location_id.append(temp_location_id)
        temp_location_area_id = location.get('area_id')
        location_area_id.append(temp_location_area_id)
        temp_location_x = location.get('x')
        location_x.append(temp_location_x)
        temp_location_y = location.get('y')
        location_y.append(temp_location_y)
        temp_location_victim = location.get('victims')
        temp_location_victim = temp_location_victim.keys()
        temp_location_victim = re.sub(r'[()]', '', str(temp_location_victim)[10:-1])
        temp_location_victim = temp_location_victim.strip("[]")
        temp_location_victim = temp_location_victim.strip("''")
        victim.append(temp_location_victim)

    locations = pd.DataFrame(list(zip(location_id, location_area_id, location_x, location_y, victim)), columns=['location_id', 'location_area_id', 'location_x', 
                                                                                                                'location_y', 'victim'])
    
    return locations
    
def distance(x1, x2, y1, y2):
    x1 = x1
    x2 = x2
    y1 = y1
    y2 = y2
    
    d = np.round(np.sqrt(np.square(x2 - x1) + np.square(y2 - y1)), 1)
    
    return d

def subtract_victims(df):
    
    index_of_interest  = []
    how_many_green     = []
    how_many_yellow    = []
    
    df = df.reset_index()

    # Obtaining the index of interest which is where triage state is successful offset by one. In other words, the one above successful
    for idx, move in df.iterrows():
        if (move['event'] == 'triage' and move['triage_state'] == 'SUCCESSFUL'):
            index = idx - 1
            index_of_interest.append(index)
            
    for idx, move in df.iterrows():
        for i in index_of_interest:
            if idx == i:
                # Look at all the distances
                victim_distance = [[move['distance_so_victim'],    move['so_victim_type']],
                                   [move['distance_tkt_victim'],   move['tkt_victim_type']], 
                                   [move['distance_hcr_victim'],   move['hcr_victim_type']], 
                                   [move['distance_hcr_victim1'],  move['hcr_victim1_type']],
                                   [move['distance_hcr_victim2'],  move['hcr_victim2_type']], 
                                   [move['distance_hcr_victim3'],  move['hcr_victim3_type']], 
                                   [move['distance_mkcr_victim'],  move['mkcr_victim_type']], 
                                   [move['distance_acr_victim'],   move['acr_victim_type']],
                                   [move['distance_acr_victim1'],  move['acr_victim1_type']], 
                                   [move['distance_acr_victim2'],  move['acr_victim2_type']],
                                   [move['distance_r102_victim'],  move['r102_victim_type']], 
                                   [move['distance_r102_victim1'], move['r102_victim1_type']], 
                                   [move['distance_r102_victim2'], move['r102_victim2_type']], 
                                   [move['distance_r104_victim'],  move['r104_victim_type']], 
                                   [move['distance_r105_victim'],  move['r105_victim_type']], 
                                   [move['distance_r107_victim'],  move['r107_victim_type']],
                                   [move['distance_r107_victim1'], move['r107_victim1_type']],
                                   [move['distance_r107_victim2'], move['r107_victim2_type']],
                                   [move['distance_r107_victim'],  move['r108_victim_type']],
                                   [move['distance_r108_victim1'], move['r108_victim1_type']],
                                   [move['distance_r111_victim'],  move['r111_victim_type']],
                                   [move['distance_r111_victim1'], move['r111_victim1_type']],
                                   [move['distance_mb_victim1'],   move['mb_victim1_type']],
                                   [move['distance_mb_victim'],    move['mb_victim_type']],
                                   [move['distance_es2_victim'],   move['es2_victim_type']],
                                   [move['distance_cf_victim2'],   move['cf_victim2_type']],
                                   [move['distance_cf_victim1'],   move['cf_victim1_type']],
                                   [move['distance_cf_victim'],    move['cf_victim_type']],
                                   [move['distance_br_victim1'],   move['br_victim1_type']],
                                   [move['distance_br_victim'],    move['br_victim_type']]]

                # Get the minimum of the distances and the indices
                minimum = [x for (x, y) in victim_distance]
                min_of_list = np.min(minimum)
                index_of_min = minimum.index(min_of_list)
                if victim_distance[index_of_min][1] == 'green':
                    how_many_green.append(idx) 
                else:
                    how_many_yellow.append(idx)

    #Subtracting when a green victim is triaged from the green victims count. 
    for i in range(0, len(how_many_green)):
        df['green_victims_count'].iloc[how_many_green[i]:how_many_green[-1]+1] = df['green_victims_count'] - 1

    df.loc[:, 'green_victims_count'].iloc[how_many_green[-1]+1:] = df.loc[:, 'green_victims_count'].iloc[how_many_green[-1]]

    for i in range(0, len(how_many_yellow)):
        df['yellow_victims_count'].iloc[how_many_yellow[i]:how_many_yellow[-1]+1] = df['yellow_victims_count'] - 1

    df.loc[:, 'yellow_victims_count'].iloc[how_many_yellow[-1]+1:] = df.loc[:, 'yellow_victims_count'].iloc[how_many_yellow[-1]]
    
    return df
    