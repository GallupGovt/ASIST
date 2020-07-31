# Importing modules
from utils import *
import matplotlib
import matplotlib.pyplot as plt 
import pandas as pd
import os
  
import platform
if platform.system() == 'Darwin':
    matplotlib.use('MacOSX')
else:
    matplotlib.use('TkAgg')
    
pd.options.mode.chained_assignment = None

# Directories for data. You need to change this
MSG_DIR   = 'Data/messages/Falcon/'
SAT_DIR   = 'Data/surveys/'
WORLD_DIR = 'Data/Locations/'

# Game Files of interest
TRIAL_4  = 'ASIST_data_study_id_000001_condition_id_000006_trial_id_000004_messages.json'
TRIAL_7  = 'ASIST_data_study_id_000001_condition_id_000007_trial_id_000007_messages.json'
TRIAL_9  = 'ASIST_data_study_id_000001_condition_id_000005_trial_id_000009_messages.json'
TRIAL_11 = 'ASIST_data_study_id_000001_condition_id_000006_trial_id_000011_messages.json'
TRIAL_12 = 'ASIST_data_study_id_000001_condition_id_000007_trial_id_000012_messages.json'

# Satisficing Tendency File
SAT_FILE = 'Copy of ASIST+Experiment+1+Surveys_June+22,+2020_14.52.csv'
# Columns of interest for Satisficing file
SAT_COLS =  ['Q2', 'Q5_1', 'Q5_2', 'Q5_3', 'Q5_4', 'Q5_5', 'Q5_6', 'Q5_7', 'Q5_8', 'Q5_9', 'Q5_10']

# World Information
WORLD_FILE = 'Agents_IHMCLocationMonitor_ConfigFolder_Falcon.json'

# Converting names of files into list
tarname  = [TRIAL_4, TRIAL_7, TRIAL_9, TRIAL_11, TRIAL_12]

# Obtaining details from files. Study ID, Condition ID and Trial ID. This is needed for the Satisficing Tendency File and knowing 
# the conditions of the map, which type of game and so on. 
study_id = []
condition_id = []
trial_id = []
for i in tarname:
    temp_study_id     = i[11:26]
    temp_condition_id = i[27:46]
    temp_trial_id     = i[47:62]
    
    study_id.append(temp_study_id)
    condition_id.append(temp_condition_id)
    trial_id.append(temp_trial_id)
    
# Reading files
trial_4 = get_message_data(os.path.join(MSG_DIR, TRIAL_4))
trial_7 = get_message_data(os.path.join(MSG_DIR, TRIAL_7))
trial_9 = get_message_data(os.path.join(MSG_DIR, TRIAL_9))
trial_11 = get_message_data(os.path.join(MSG_DIR, TRIAL_11))
trial_12 = get_message_data(os.path.join(MSG_DIR, TRIAL_12))

# Satisficing Tendency
sat_tendency_df = sat_tendency(os.path.join(SAT_DIR, SAT_FILE), SAT_COLS)

# World Information
areas = get_area_information(os.path.join(WORLD_DIR, WORLD_FILE))
connections = get_connections_information(os.path.join(WORLD_DIR, WORLD_FILE))
locations = get_locations_information(os.path.join(WORLD_DIR, WORLD_FILE))


# Including trial, condition, study and subject id into each file. 
# Subject ID is needed to link the satisficing tendency file
files = [trial_4, trial_7, trial_9, trial_11, trial_12]
i = 0
while i < len(files):
    for j in files:
        j['study_id'] = study_id[i]
        j['condition_id'] = condition_id[i]
        j['trial_id'] = trial_id[i]
    
         #Putting the subject id into the data
        if (condition_id[i] == 'condition_id_000005' and trial_id[i] == 'trial_id_000009'):
            j['subject_id'] = 'subject_id_000013'
        elif (condition_id[i] == 'condition_id_000005' and trial_id[i] == 'trial_id_000015'):
            j['subject_id'] = 'subject_id_000016'
        elif (condition_id[i] == 'condition_id_000005' and trial_id[i] == 'trial_id_000021'):
            j['subject_id'] = 'subject_id_000019'
        elif (condition_id[i] == 'condition_id_000006' and trial_id[i] == 'trial_id_000004'):
            j['subject_id'] = 'subject_id_000011'
        elif (condition_id[i] == 'condition_id_000006' and trial_id[i] == 'trial_id_000011'):
            j['subject_id'] = 'subject_id_000014'
        elif (condition_id[i] == 'condition_id_000006' and trial_id[i] == 'trial_id_000017'):
            j['subject_id'] = 'subject_id_000017'
        elif (condition_id[i] == 'condition_id_000007' and trial_id[i] == 'trial_id_000007'):
            j['subject_id'] = 'subject_id_000012'
        elif (condition_id[i] == 'condition_id_000007' and trial_id[i] == 'trial_id_000012'):
            j['subject_id'] = 'subject_id_000015'
        elif (condition_id[i] == 'condition_id_000007' and trial_id[i] == 'trial_id_000019'):
            j['subject_id'] = 'subject_id_000018'
        
        i += 1
        
# strings to lowercase in mission state
for i in files:
    i['mission_state'] = [str(x).lower() for x in i['mission_state']]
    
    
# Obtaining the satisficing tendency score
trial_4 = pd.merge(trial_4, sat_tendency_df[['sati', 'subject_id']], on='subject_id')
trial_7 = pd.merge(trial_7, sat_tendency_df[['sati', 'subject_id']], on='subject_id')
trial_9 = pd.merge(trial_9, sat_tendency_df[['sati', 'subject_id']], on='subject_id')
trial_11 = pd.merge(trial_11, sat_tendency_df[['sati', 'subject_id']], on='subject_id')
trial_12 = pd.merge(trial_12, sat_tendency_df[['sati', 'subject_id']], on='subject_id')


# Sorting timestamp
# Obtaining the index of the mission start after sorting. Used to select from mission start and forward. 
# We're not interested in the time before the mission starts
trial_4 = trial_4.sort_values(by=['timestamp'], ascending=True)
trial_4 = trial_4.reset_index()
index = trial_4.index[trial_4['mission_state']=='start']
trial_4 = trial_4.iloc[index[0]:].copy()

trial_7 = trial_7.sort_values(by=['timestamp'], ascending=True)
trial_7 = trial_7.reset_index()
index = trial_7.index[trial_7['mission_state']=='start']
trial_7 = trial_7.iloc[index[0]:].copy()

trial_9 = trial_9.sort_values(by=['timestamp'], ascending=True)
trial_9 = trial_9.reset_index()
index = trial_9.index[trial_9['mission_state']=='start']
trial_9 = trial_9.iloc[index[0]:].copy()

trial_11 = trial_11.sort_values(by=['timestamp'], ascending=True)
trial_11 = trial_11.reset_index()
index = trial_11.index[trial_11['mission_state']=='start']
trial_11 = trial_11.iloc[index[0]:].copy()

trial_12 = trial_12.sort_values(by=['timestamp'], ascending=True)
trial_12 = trial_12.reset_index()
index = trial_12.index[trial_12['mission_state']=='start']
trial_12 = trial_12.iloc[index[0]:].copy()


last_timestamps = []
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # Calculating the mean of the satisficing score for each file
    #df['sati'] = df['sati'] / 10
    
    # Forward filling the coordinates for each df
    df['x'] = df['x'].ffill()
    df['y'] = df['y'].ffill()
    df['z'] = df['z'].ffill()
    
    # Obtaining time left in the mission from the timestamp for each df
    time_left = []
    # Obtaining last timestamp. Last timestamp is when a player enters the 'me or mission end'. We're grabbing the first instance of 
    # when this happens
    last_timestamp = [x for (x, y, z) in zip(df.index, 
                                             df['event'], 
                                             df['entered_area_id']) if z=='me'][0]
    last_timestamps.append(last_timestamp)
    # Getting the time left
    for time in df['timestamp'][:]:
        temp_time = df['timestamp'][last_timestamp] - time
        time_left.append(temp_time)

    df['time_left'] = time_left

    # Five minute indicator for keeping track of yellow and green players
    # This five minute indicator allows us to 'kill' yellow victims after 5 minutes
    start_time = df['time_left'].iloc[0]
    five_minute_indicator = [] 
    for time in df['time_left']:
        if (start_time - time) < (datetime.timedelta(minutes=5)):
            five_minute_indicator.append(0)
        else:
            five_minute_indicator.append(1)

    df['five_minute_indicator'] = five_minute_indicator
    
    
# Choosing data only to mission end
trial_4 = trial_4.iloc[:last_timestamps[0]]
trial_7 = trial_7.iloc[:last_timestamps[1]]
trial_9 = trial_9.iloc[:last_timestamps[2]]
trial_11 = trial_11.iloc[:last_timestamps[3]]
trial_12 = trial_12.iloc[:last_timestamps[4]]


# Obtaining the coordinates and victim type, entrances coordinates
# Security Office---------------------------------------------------------------------------------------------------------------------------
so_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'], 
                                          connections['connections_y2'],
                                          connections['connections_name']) if z =='Door to the Security Office'][0]
so_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =='l1'][0]
# Break room--------------------------------------------------------------------------------------------------------------------------------
br_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                          connections['connections_y2'], 
                                          connections['connections_name']) if z =='Opening between the Left Hallway and the Break Room'][0]
br_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =='l2'][0]
br_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =='l3'][0]
# Computer Farm-----------------------------------------------------------------------------------------------------------------------------
cf_left_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                               connections['connections_y2'], 
                                               connections['connections_name']) if z =='Door to the Computer Farm from the Left Hallway'][0]
cf_right_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                                connections['connections_y2'], 
                                                connections['connections_name']) if z =='Door to the Computer Farm from the Right Hallway'][0]
cf_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =='l4'][0]
cf_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =='l5'][0]
cf_victim_xy_2 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =='l6'][0]
# Executive Suite---------------------------------------------------------------------------------------------------------------------------
es2_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                           connections['connections_y2'], 
                                           connections['connections_name']) if z =='Door to Executive Suite 2'][0]
es2_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                   locations['location_y'],
                                                   locations['victim'], 
                                                   locations['location_id']) if z =="l7"][0]
# Terrace King------------------------------------------------------------------------------------------------------------------------------
tkt_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                           connections['connections_y2'], 
                                           connections['connections_name']) if z =="Door from to the Terrace from King Chris's Office"][0]
tkt_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                   locations['location_y'],
                                                   locations['victim'], 
                                                   locations['location_id']) if z =="l8"][0]
# Herbalife Conf Room ----------------------------------------------------------------------------------------------------------------------
hcr_top_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                               connections['connections_y2'], 
                                               connections['connections_name']) if z =="Top Hallway Door to the Herbalife Conference Room"][0]
hcr_middle_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                                  connections['connections_y2'], 
                                                  connections['connections_name']) if z =='Middle Hallway Door to the Herbalife Conference Room'][0]
hcr_victim_xy = [(w, x, y) for (w,x,y,z) in zip(locations['location_x'],
                                                locations['location_y'],
                                                locations['victim'], 
                                                locations['location_id']) if z =="l9"][0]
hcr_victim_xy_1 = [(w, x, y) for (w,x,y,z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =="l10"][0]
hcr_victim_xy_2 = [(w, x, y) for (w,x,y,z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =="l11"][0]
hcr_victim_xy_3 = [(w, x, y) for (w,x,y,z) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =="l12"][0]
# Mary Kay Conf. Room-------------------------------------------------------------------------------------------------------------------------
mkcr_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =="Door to Mary Kay Conference Room"][0]
mkcr_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l13"][0]

# Amway Conf Room-----------------------------------------------------------------------------------------------------------------------------
acr_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                           connections['connections_y2'],
                                           connections['connections_name']) if z =="Door to Amway Conference Room"][0]
acr_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                   locations['location_y'],
                                                   locations['victim'], 
                                                   locations['location_id']) if z =="l14"][0]
acr_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                     locations['location_y'],
                                                     locations['victim'], 
                                                     locations['location_id']) if z =="l15"][0]
acr_victim_xy_2 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                     locations['location_y'],
                                                     locations['victim'], 
                                                     locations['location_id']) if z =="l16"][0]

# ROOM 102 ------------------------------------------------------------------------------------------------------------------------------------
r102_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =="Door to Room 102"][0]
r102_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l17"][0]
r102_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l18"][0]
r102_victim_xy_2 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l19"][0]
# Room 104------------------------------------------------------------------------------------------------------------------------------------
r104_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =="Door to Room 104"][0]
r104_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l20"][0]
# Room 105------------------------------------------------------------------------------------------------------------------------------------
r105_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =="Door to Room 105"][0]
r105_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l21"][0]
# Room 107------------------------------------------------------------------------------------------------------------------------------------
r107_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =="Door to Room 107"][0]
r107_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l22"][0]
r107_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l23"][0]
r107_victim_xy_2 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l24"][0]
# Room 108------------------------------------------------------------------------------------------------------------------------------------
r108_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =='Door to Room 108'][0]
r108_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l25"][0]
r108_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l26"][0]
# Room 111------------------------------------------------------------------------------------------------------------------------------------
r111_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                            connections['connections_y2'], 
                                            connections['connections_name']) if z =='Door to Room 111'][0]
r111_victim_xy = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l27"][0]
r111_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                      locations['location_y'],
                                                      locations['victim'], 
                                                      locations['location_id']) if z =="l28"][0]
# Men's Bathroom-------------------------------------------------------------------------------------------------------------------------------
mb_door_xy = [(x, y) for (x, y, z) in zip(connections['connections_x2'],
                                          connections['connections_y2'], 
                                          connections['connections_name']) if z =="Door to Men's Room"][0]
mb_victim_xy = [(w, x, y) for (w, x, y,z ) in zip(locations['location_x'],
                                                  locations['location_y'],
                                                  locations['victim'], 
                                                  locations['location_id']) if z =="l29"][0]
mb_victim_xy_1 = [(w, x, y) for (w, x, y, z) in zip(locations['location_x'],
                                                    locations['location_y'],
                                                    locations['victim'], 
                                                    locations['location_id']) if z =="l30"][0]

# Applying methods to all dataframes
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # Calculating the distance to the room victim, room and getting the victim type
    # SO --------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_so_door']          = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(so_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(so_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_so_victim']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(so_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(so_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'so_victim_type']            = np.repeat(so_victim_xy[2], len(df))
    # BR ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_br_door']          = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(br_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(br_door_xy[1], 
                                                                                                                  len(df)))]
    #VICTIM 0
    df.loc[:, 'distance_br_victim']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(br_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(br_victim_xy[1],
                                                                                                                  len(df)))]
    df.loc[:, 'br_victim_type']            = np.repeat(br_victim_xy[2], len(df))
    #VICTIM 1
    df.loc[:, 'distance_br_victim1']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(br_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(br_victim_xy_1[1],
                                                                                                                  len(df)))]
    df.loc[:, 'br_victim1_type']           = np.repeat(br_victim_xy_1[2], len(df))
    # CF ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_left_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(cf_left_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(cf_left_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_right_door']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(cf_right_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(cf_right_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_cf_victim']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(cf_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(cf_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'cf_victim_type']            = np.repeat(cf_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_cf_victim1']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(cf_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(cf_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'cf_victim1_type']          = np.repeat(cf_victim_xy_1[2], len(df))
    ## Victim 2
    df.loc[:, 'distance_cf_victim2']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(cf_victim_xy_2[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(cf_victim_xy_2[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'cf_victim2_type']          = np.repeat(cf_victim_xy_2[2], len(df))
    # ES ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_es2_door']         = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(es2_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(es2_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_es2_victim']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(es2_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(es2_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'es2_victim_type']           = np.repeat(es2_victim_xy[2], len(df))
    # TKT ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_tkt_door']         = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(tkt_door_xy[0],
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(tkt_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_tkt_victim']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(tkt_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(tkt_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'tkt_victim_type']           = np.repeat(tkt_victim_xy[2], len(df))
    # HCR ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_hcrtop_door']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_top_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(hcr_top_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_hcrmiddle_door']   = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_middle_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(hcr_middle_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_hcr_victim']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_victim_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(hcr_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'hcr_victim_type']           = np.repeat(hcr_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_hcr_victim1']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(hcr_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'hcr_victim1_type']          = np.repeat(hcr_victim_xy_1[2], len(df))
    # Victim 2
    df.loc[:, 'distance_hcr_victim2']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_victim_xy_2[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(hcr_victim_xy_2[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'hcr_victim2_type']          = np.repeat(hcr_victim_xy_2[2], len(df))
    # Victim 3
    df.loc[:, 'distance_hcr_victim3']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(hcr_victim_xy_3[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(hcr_victim_xy_3[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'hcr_victim3_type']          = np.repeat(hcr_victim_xy_3[2], len(df))
    # MKCR ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_mkcr_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(mkcr_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(mkcr_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_mkcr_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(mkcr_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(mkcr_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'mkcr_victim_type']          = np.repeat(mkcr_victim_xy[2], len(df))
    # ACR ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_acr_door']         = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(acr_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(acr_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_acr_victim']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(acr_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(acr_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'acr_victim_type']           = np.repeat(acr_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_acr_victim1']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(acr_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(acr_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'acr_victim1_type']          = np.repeat(acr_victim_xy_1[2], len(df))
    # Victim 2
    df.loc[:, 'distance_acr_victim2']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(acr_victim_xy_2[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(acr_victim_xy_2[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'acr_victim2_type']          = np.repeat(acr_victim_xy_2[2], len(df))
    # R102 ---------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r102_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r102_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(r102_door_xy[1], 
                                                                                                                  len(df)))]
    #Victim 0
    df.loc[:, 'distance_r102_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r102_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r102_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r102_victim_type']          = np.repeat(r102_victim_xy[2], len(df))
    #Victim 1
    df.loc[:, 'distance_r102_victim1']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r102_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r102_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r102_victim1_type']          = np.repeat(r102_victim_xy_1[2], len(df))
    #Victim 2
    df.loc[:, 'distance_r102_victim2']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r102_victim_xy_2[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r102_victim_xy_2[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r102_victim2_type']          = np.repeat(r102_victim_xy_2[2], len(df))
    # R104------------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r104_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r104_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(r104_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_r104_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r104_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r104_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r104_victim_type']          = np.repeat(r104_victim_xy[2], len(df))
    # Room 105------------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r105_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r105_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r105_door_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'distance_r105_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r105_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r105_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r105_victim_type']          = np.repeat(r105_victim_xy[2], len(df))
    # Room 107------------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r107_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r107_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(r107_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_r107_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r107_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r107_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r107_victim_type']          = np.repeat(r107_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_r107_victim1']     = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r107_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r107_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r107_victim1_type']         = np.repeat(r107_victim_xy_1[2], len(df))
    # Victim 2
    df.loc[:, 'distance_r107_victim2']     = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r107_victim_xy_2[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r107_victim_xy_2[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r107_victim2_type']         = np.repeat(r107_victim_xy_2[2], len(df))
    # Room 108------------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r108_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r108_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(r108_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_r108_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r108_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r108_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r108_victim_type']          = np.repeat(r108_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_r108_victim1']     = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r108_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r108_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r108_victim1_type']         = np.repeat(r108_victim_xy_1[2], len(df))
    # Room 111------------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_r111_door']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r111_door_xy[0], 
                                                                                                                  len(df)), 
                                                                                               df['z'], np.repeat(r111_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_r111_victim']      = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r111_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r111_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r111_victim_type']          = np.repeat(r111_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_r111_victim1']     = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(r111_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(r111_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'r111_victim1_type']         = np.repeat(r111_victim_xy_1[2], len(df))
    # Men's Bathroom-------------------------------------------------------------------------------------------------------------------------------
    df.loc[:, 'distance_mb_door']          = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(mb_door_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(mb_door_xy[1], 
                                                                                                                  len(df)))]
    # Victim 0
    df.loc[:, 'distance_mb_victim']        = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(mb_victim_xy[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(mb_victim_xy[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'mb_victim_type']            = np.repeat(mb_victim_xy[2], len(df))
    # Victim 1
    df.loc[:, 'distance_mb_victim1']       = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], np.repeat(mb_victim_xy_1[0], 
                                                                                                                  len(df)),
                                                                                               df['z'], np.repeat(mb_victim_xy_1[1], 
                                                                                                                  len(df)))]
    df.loc[:, 'mb_victim1_type']           = np.repeat(mb_victim_xy_1[2], len(df))
    
    # Distance to closest victim
    df.loc[:, 'distance_victim']           = [distance(x, x1, z, z1) for (x, x1, z, z1) in zip(df['x'], df['victim_x'], df['z'], df['victim_z'])]
    
    
# Creating separate dataframes for the visualizations. Creating here before we forward fill entered_area_id. 
trial_4_viz = trial_4.copy()
trial_7_viz = trial_7.copy()
trial_9_viz = trial_9.copy()
trial_11_viz = trial_11.copy()
trial_12_viz = trial_12.copy()

# Dropping columns
cols_to_drop = ['motion_x', 'motion_y', 'motion_z', 'total_time', 'observation_number', 'exited_area_name', 'equipped_item_name', 
                'sprinting', 'door_x', 'door_y', 'door_z', 'data_open', 'lever_y', 'lever_z', 'powered', 'item_x', 'item_y', 'item_z',
                'woof_x', 'woof_y', 'woof_z', 'message', 'lever_x']

for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    df.drop(cols_to_drop, 1, inplace=True)
    df['entered_area_id'] = df['entered_area_id'].ffill()
    
    
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # Obtaining time in progress
    triage_time_progress = [x for (x, y) in zip(df['time_left'], 
                                                df['triage_state']) if y=='IN_PROGRESS']
    # Obtaining time between successful events
    triage_time_successful = [x for (x, y) in zip(df['time_left'], 
                                                  df['triage_state']) if y=='SUCCESSFUL' or y=='UNSUCCESSFUL']
    # Obtaining the index between successful events
    triage_time_successful_index = [x for (x, y, z) in zip(df.index, 
                                                           df['time_left'], 
                                                           df['triage_state']) if z=='SUCCESSFUL' or z=='UNSUCCESSFUL']
    # How long does it take to triage a victim between progress and successful
    time_to_triage = [x - y for (x, y) in zip(triage_time_progress, 
                                              triage_time_successful)]

    # Calculating average of time between progress and successful events
    # Window size of the average
    window_size = 2
    i = 0
    time_triage_MA = []
    while i < len(time_to_triage) - window_size + 1:
        this_window = time_to_triage[i : i + window_size]
        moving_average = (this_window[0] + this_window[1]) / window_size
        time_triage_MA.append(moving_average)
        i += 1
    
    # Joining to the df based on the index of successful times
    j = 0
    while j < len(time_to_triage) - 1:
        k = time_triage_MA[j]
        for idx, i in df.iterrows():
            if idx == triage_time_successful_index[j]:
                df.loc[idx, 'time_triage_MA'] = k
        j += 1
        
        
    # Calculating moving average between successful events
    i = 0
    time_between_success_MA = []
    while i < len(triage_time_successful) - window_size + 1:
        this_window = triage_time_successful[i : i + window_size]
        time_between_success_MA_temp = this_window[0] - this_window[1]
        time_between_success_MA.append(time_between_success_MA_temp)
        i += 1

    j = 0
    while j < len(triage_time_successful) - 1:
        k = time_between_success_MA[j]
        for idx, i in df.iterrows():
            if idx == triage_time_successful_index[j]:
                df.loc[idx, 'time_between_success'] = k
        j += 1
        
    # Moving Average
    i = 0
    moving_averages = []
    while i < len(triage_time_successful) - window_size + 1:
        this_window = triage_time_successful[i : i + window_size]
        moving_average = (this_window[0] - this_window[1]) / window_size
        moving_averages.append(moving_average)
        i += 1

    j = 0
    while j < len(triage_time_successful) - 1:
        k = moving_averages[j]
        for idx, i in df.iterrows():
            if idx == triage_time_successful_index[j]:
                df.loc[idx, 'moving_average'] = k
        j += 1
        
        
# How many victims each rooms has
yellow = {'so': 1, 'br': 1, 'cf': 2, 'hcr': 2, 'acr': 1, 'r102': 1, 'r107': 1, 'r111': 1 , 'es2': 0, 'tkt': 0, 'mkcr': 0, 'r104': 0,
          'r105': 0, 'r108': 0, 'mb': 0, 'r110': 0, 'el': 0, 'ew': 0, 'jc': 0, 'r106': 0, 'kco2': 0, 'r103': 0, 'es1': 0, 'me': 0, 
          'rh': 0, 'fy1': 0, 'r109': 0, 'chm': 0, 'cht': 0, 'kcoe': 0, 'lh1': 0, 'fy2': 0, 'kco1': 0, 'lh2': 0, 'ms': 0, 
          'chb': 0, 'wb': 0}

green = {'so': 0, 'br': 1, 'cf': 1, 'hcr': 2, 'acr': 2, 'r102': 2, 'r107': 2, 'r111': 1 , 'es2': 1, 'tkt': 1, 'mkcr': 1, 'r104': 1,
          'r105': 1, 'r108': 2, 'mb': 2, 'r110': 0, 'el': 0, 'ew': 0, 'jc': 0, 'r106': 0, 'kco2': 0, 'r103': 0, 'es1': 0, 'me': 0, 
          'rh': 0, 'fy1': 0, 'r109': 0, 'chm': 0, 'cht': 0, 'kcoe': 0, 'lh1': 0, 'fy2': 0, 'kco1': 0, 'lh2': 0, 'ms': 0, 
          'chb': 0, 'wb': 0}
# Mapping victims (green, yellow) counts, and whether a room has victims (which types or none)
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # Victims count
    df.loc[:, 'how_many_yellow_victims'] = df.loc[:, 'entered_area_id']
    df.loc[:, 'how_many_green_victims']  = df.loc[:, 'entered_area_id']
    
    df.loc[:, 'how_many_yellow_victims'] = df.loc[:, :].replace({'how_many_yellow_victims': yellow})
    
    
# 0: no victims, 1: yellow, 2: green, 3: green and yellow
victims_locations_di = {'so': 'yellow', 'br': 'both', 'cf': 'both', 'es2': 'green', 
                        'tkt': 'green', 'hcr': 'both', 'mkcr': 'green', 'acr': 'both', 
                        'r102': 'both', 'r104': 'green', 'r105': 'green', 'r107': 'both' , 
                        'r108':'green' , 'r111': 'both' ,'mb': 'green', 'ms': 'no victims',
                        'me': 'no victims', 'ew': 'no victims', 'fy1': 'no victims',
                        'fy2': 'no victims', 'el': 'no victims', 'lh1': 'no victims',
                        'lh2': 'no victims', 'rh': 'no victims', 'chb': 'no victims', 
                        'chm': 'no victims', 'cht': 'no victims', 'es1': 'no victims',
                        'jc': 'no victims', 'es2': 'no victims','kco2': 'no victims',
                        'kco1': 'no victims', 'r101': 'no victims', 'r103': 'no victims', 
                        'r106': 'no victims', 'r108': 'no victims', 'r110': 'no victims',
                        'wb': 'no victims', 'mb': 'no victims'}

# Mapping victims (green, yellow) counts, and whether a room has victims (which types or none)
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # Victims count
    df.loc[:, 'how_many_yellow_victims'] = df.loc[:, 'entered_area_id']
    df.loc[:, 'how_many_green_victims']  = df.loc[:, 'entered_area_id']
    df.loc[:, 'how_many_yellow_victims'] = df.loc[:, :].replace({'how_many_yellow_victims': yellow})
    df.loc[:, 'how_many_green_victims']  = df.loc[:, :].replace({'how_many_green_victims': green})
    # Types of victims
    df.loc[:, 'has_victims'] = df.loc[:, 'entered_area_id']
    df.loc[:, 'has_victims'] = df.loc[:, :].replace({'has_victims': victims_locations_di})
    

    # Changing critical to yellow, non-critical to green, after 5 minutes yellow to red
    df.loc[:, :] = df.loc[:, :].replace('non_critical', 'green')
    df.loc[:, :] = df.loc[:, :].replace('critical', 'yellow')
    
    # Changing the yellow victims to red once the 5 min indicator has passed
    for col in df.filter(regex='type',axis=1):
        df.loc[(df['five_minute_indicator'] == 1) & 
                      (df[col] == 'yellow'), col] = 'red'
        
    # Changing yellows to red on has_victims when 5 minute indicator comes alive
    for co in df.filter(regex='has_victims', axis=1):
        df.loc[(df['five_minute_indicator'] == 1) &
              (df[col] == 'yellow'), col] = 'red'
        
        
# Calculating how many victims are in the world
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    green_victims_number     = []
    yellow_victims_number    = [] 

    for victim in locations['victim']:
        if victim == 'non_critical':
            green_victims_number.append(victim)
        else:
            yellow_victims_number.append(victim) 
        
    df.loc[:, 'green_victims_count']  = np.repeat(len(green_victims_number),  len(df))
    df.loc[:, 'yellow_victims_count'] = np.repeat(len(yellow_victims_number), len(df))
    
    
# Subtracting from the global count when a victim is triaged. Function from utilities
trial_4  = subtract_victims(trial_4)
trial_7  = subtract_victims(trial_7)
trial_9  = subtract_victims(trial_9)
trial_11 = subtract_victims(trial_11)
trial_12 = subtract_victims(trial_12)


# Mapping for the world conditions
conditions_between_dictionary = {'condition_id_000001': 'trained about signal & triage tradeoff',
                                 'condition_id_000002': 'trained about triage trade off',
                                 'condition_id_000003': 'untrained',
                                 'condition_id_000004': 'untrained, dynamic map',
                                 'condition_id_000005': 'trained about signal & triage tradeoff',
                                 'condition_id_000006': 'trained about triage tradeoff',
                                 'condition_id_000007': 'untrained',
                                 'condition_id_000008': 'untrained, dynamic map'}

conditions_within_dictionary = {'condition_id_000001': 'easy mission Sparky lights on',
                                'condition_id_000002': 'easy mission Sparky lights on',
                                'condition_id_000003': 'easy mission Sparky lights on',
                                'condition_id_000004': 'easy mission Sparky lights on, dynamic map off in first half and on in second half',
                                'condition_id_000005': 'hard mission Falcon',
                                'condition_id_000006': 'hard mission Falcon',
                                'condition_id_000007': 'hard mission Falcon',
                                'condition_id_000008': 'hard mission Falcon, dynamic map off in first half and on in second half'}

# Mapping world conditions to the trials
for df in trial_4, trial_7, trial_9, trial_11, trial_12:

    df.loc[:, 'conditions_between_ss'] = df.loc[:, 'condition_id']
    df.loc[:, 'conditions_between_ss'] = df.loc[:, :].replace({'conditions_between_ss': conditions_between_dictionary})
    df.loc[:, 'conditions_within_ss'] = df.loc[:, 'condition_id']
    df.loc[:, 'conditions_within_ss'] = df.loc[:, :].replace({'conditions_within_ss': conditions_within_dictionary})
    
    
# Zeroing out after yellows after the 5-minute mark (death)
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # for columns mathcing the description 'yellow victims count'
    # identify where the five minute indicator equals 1 and the column of interest if greater than 0, and then zero-out those records
    for col in df.filter(regex='yellow_victims_count', axis=1):
        df.loc[(df['five_minute_indicator'] == 1) &
                      (df[col] > 0 ), col] = 0
        
    # Zeroing the how_many_yellow_victims after this marker as well
    for col in df.filter(regex='how_many_yellow_victims', axis=1):
        df.loc[(df['five_minute_indicator'] == 1) &
              (df[col] != '0'), col] = 0
        
    # Changing both in 'has_victims' to green if it had both after the 5-minute indicator
    for col in df.filter(regex='has_victims', axis=1):
        df.loc[(df['five_minute_indicator'] ==1 ) &
              (df[col] == 'both'), col] = 'green'
        
        
# Restricting dfs to mission end
end_index = []
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    # mission end index
    temp_end_index = df[df['entered_area_name']=='Mission End'].index[0] + 1
    end_index.append(temp_end_index)

# Restricting dfs to mission end
trial_4  = trial_4.iloc[:end_index[0]]
trial_7  = trial_7.iloc[:end_index[1]]
trial_9  = trial_9.iloc[:end_index[2]]
trial_11 = trial_11.iloc[:end_index[3]]
trial_12 = trial_12.iloc[:end_index[4]]

# Forward filling entered area name
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    df['entered_area_name'] = df['entered_area_name'].ffill()
    
    
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    
    # Zeroing out how many victims based on the triaged event
    # Obtaining indices of when a player changes area
    previous_area       = [df['entered_area_id'][0]]
    area_changes        = []
    for idx, i in df.iterrows():
        if idx > 0:
            current_area = i['entered_area_id']
            previous_area.append(current_area)
            if current_area != previous_area[idx-1]:
                area_changes.append(idx)

    # Obtaining indices of when a yellow is triaged
    previous_yellow        = [df['yellow_victims_count'][0]]
    previous_green         = [df['green_victims_count'][0]]
    yellow_indices  = []
    green_indices   = []
    for idx, i in df.iterrows():
        if idx > 0:
            current_yellow = i['yellow_victims_count']
            current_green  = i['green_victims_count']
            previous_yellow.append(current_yellow)
            previous_green.append(current_green)
            if current_yellow < previous_yellow[idx-1]:
                yellow_indices.append(idx)
            if current_green < previous_green[idx-1]:
                green_indices.append(idx)

    # Obtaining indices of when a yellow is triaged
    previous_area       = [df['entered_area_id'][0]]
    area_changes        = []
    areas_seen          = [df['entered_area_id'][0]]
    for idx, i in df.iterrows():
        if idx > 0:
            current_area = i['entered_area_id']
            previous_area.append(current_area)
            if current_area != previous_area[idx-1]:
                areas_seen.append(current_area)
                area_changes.append(idx)

    # Obtaining the closest value for each green and yellow index from above            
    # yellow end
    yellow_indices_end = []
    for i in yellow_indices:
        arr = np.array(area_changes)
        closest = arr[arr > i].min()
        yellow_indices_end.append(closest)

    # Green end    
    green_indices_end = []   
    for i in green_indices:
        arr = np.array(area_changes)
        closest = arr[arr > i].min()
        green_indices_end.append(closest)

    # Subtracting -1 for these ranges
    for i, j in zip(yellow_indices, yellow_indices_end):
        df.loc[i:j-1, 'how_many_yellow_victims'] = df.loc[i:j-1, 'how_many_yellow_victims'] - 1

    for i, j in zip(green_indices, green_indices_end):
        df.loc[i:j-1, 'how_many_green_victims'] = df.loc[i:j-1, 'how_many_green_victims'] - 1
        
for df in trial_4, trial_7, trial_9, trial_11, trial_12:

    # Getting which victims are triaged
    i = 0
    j = 0 # green
    k = 0 # yellow
    rescued = []
    index_rescued_yellow = []
    index_rescued_green = []
    while i < len(df):
        green = df['green_victims_count'][i]
        yellow = df['yellow_victims_count'][i]
        n_green = df['green_victims_count'][j]
        n_yellow = df['yellow_victims_count'][k]    
        green_rescued = n_green - green
        yellow_rescued = n_yellow - yellow

        if green_rescued != 0:
            rescued_temp = 'green'
            rescued.append(rescued_temp)
            index_rescued_green.append(i)
            j = i
        elif yellow_rescued != 0:
            rescued_temp = 'yellow'
            rescued.append(rescued_temp)
            index_rescued_yellow.append(i)
            k = i
        i += 1

    for idx, i in df.iterrows():
        for j in index_rescued_green:
            if idx == j:
                df.loc[idx, 'rescued'] = 'green'

    for idx, i in df.iterrows():
        for j in index_rescued_yellow:
            if idx == j:
                df.loc[idx, 'rescued'] = 'yellow'
                
## Visualization
# Date = 7/31/2020
# As of the latest iteration, the maps are needed to ascertain which initial strategy is being used. This is then inputed into each separate dataframe
for df in trial_4_viz, trial_7_viz, trial_9_viz, trial_11_viz, trial_12_viz:
    # columns of interest
    df_data = df[['trial_id','x', 'y', 'z','entered_area_id', 'victim_x', ' victim_y', 'victim_z', 'triage_state', 'five_minute_indicator']]
    
    # Getting the names of the room, locations of rooms and victims locations, and getting unique ones
    movement_x_five_1 = [x for (x, y) in zip(df_data['x'], 
                                             df_data['five_minute_indicator']) if y == 1]    # Getting locations for after 5 min
    movement_z_five_1 = [x for (x, y) in zip(df_data['z'], 
                                             df_data['five_minute_indicator']) if y == 1]    # Getting locations for after 5 min
    movement_x_five_0 = [x for (x, y) in zip(df_data['x'], 
                                             df_data['five_minute_indicator']) if y == 0]     # Getting locations for before 5 min
    movement_z_five_0 = [x for (x, y) in zip(df_data['z'], 
                                             df_data['five_minute_indicator']) if y == 0]     # Getting locations for before 5 min
    entered_area_id   = [x for x in df_data['entered_area_id'] if x != None]    # Names of the areas
    entered_area_x    = [x for (x, y) in zip(df_data['x'], 
                                             df_data['entered_area_id']) if y != None]    # location x of entered area
    entered_area_z    = [x for (x, y) in zip(df_data['z'], 
                                             df_data['entered_area_id']) if y != None]    # location z of entered area
    victim_area_x     = [x for x in df_data['victim_x'] if x!= None]    # Location x of victim
    victim_area_z     = [x for x in df_data['victim_z'] if x!= None]    # Location z of victim
    triaged           = [x for x in df_data['triage_state'] if x=='SUCCESSFUL']    #triage state if triaged is successful
    successfull_triaged_number = [x for x in range(0, len(triaged))]
    triaged_x         = [x for (x, y) in zip(df_data['victim_x'], 
                                            df_data['triage_state']) if y=='SUCCESSFUL']
    triaged_z         = [x for (x, y) in zip(df_data['victim_z'], 
                                           df_data['triage_state']) if y=='SUCCESSFUL']
    
    # Obtaining the victims locations
    yellow_victims_x = [x for (x, y) in zip(locations['location_x'], 
                                            locations['victim']) if y =='critical']
    yellow_victims_y = [x for (x, y) in zip(locations['location_y'], 
                                            locations['victim']) if y =='critical']
    green_victims_x  = [x for (x, y) in zip(locations['location_x'], 
                                            locations['victim']) if y =='non_critical']
    green_victims_y  = [x for (x, y) in zip(locations['location_y'], 
                                            locations['victim']) if y =='non_critical']
    
    # Obtaining the entrances to the rooms
    entrances_x = [np.mean([x, y]) for (x, y) in zip(connections['connections_x1'], 
                                                     connections['connections_x2'])]
    entrances_y = [np.mean([x, y]) for (x, y) in zip(connections['connections_y1'], 
                                                     connections['connections_y2'])]
    
    # Obtaining the widths and height of the rooms
    areas['width']  = [(y - x) for (x, y) in zip(areas['areas_x1'], 
                                                areas['areas_x2'])]
    areas['height'] = [(y - x) for (x, y) in zip(areas['areas_y1'], 
                                                 areas['areas_y2'])]
    
    df_data['entered_area_id'] = df_data['entered_area_id'].replace(np.nan, '')

    plt.rcParams.update({'font.size': 8})
    plt.figure(figsize=(30,30))
    ax = plt.figure().add_subplot(111)
    plt.scatter(movement_x_five_0, movement_z_five_0, s=0.5, marker=',', color='darkgray')
    plt.scatter(movement_x_five_1, movement_z_five_1, s=0.5, marker=',', color='red')
    plt.scatter(entrances_x, entrances_y, marker='s', color='blue')
    plt.plot()
    room_name = []
    for x, y, z in zip(entered_area_x, entered_area_z, entered_area_id):
        if z not in room_name:
            plt.text(x, y, z)
            room_name.append(z)
    triaged_seen = []
    for x, y, z in zip(triaged_x, triaged_z, successfull_triaged_number):
        if z not in triaged_seen:
            plt.text(x+1, y, z)
            triaged_seen.append(z)    
    plt.scatter(yellow_victims_x, yellow_victims_y, color='orange')
    plt.scatter(green_victims_x, green_victims_y, color='lime')
    for idx, i in areas.iterrows():
        rect1 = matplotlib.patches.Rectangle((i['areas_x1'], i['areas_y1']),
                                             i['width'], i['height'], 
                                             fc=None,
                                             ec ='g',
                                             fill=False,
                                             color='grey')
        ax.add_patch(rect1) 
    plt.xlim([-2200, -2000]) 
    plt.ylim([140, 200])
    title = df_data['trial_id'].iloc[0]
    plt.title(title)

    plt.show()
    
# Manually input the skipping strategy by the maps
for df in trial_4, trial_7, trial_9, trial_11, trial_12:
    
    # Obtaining which skip strategy it is
    current_map = df['trial_id'].iloc[0]
    print('Current map: {}'.format(current_map))
    df.loc[:, 'player_skips'] = input(str('Please enter the skipping strategy observed in the maps: '))
    # input strategy. forces the strategy to lowercase as logic is built in lowercase
    df.loc[:, 'current_strategy'] = input(str('Please enter the most current strategy observed in the maps: ')).lower()    
    print('-----------------------------------')
    first_triaged = df[~pd.isnull(df['rescued'])].index[0]
    
    current_strategy = df.loc[0:0, 'current_strategy']
    # Final Strategy - 
    for idx, i in df.iterrows():
        five_minute_indicator = i['five_minute_indicator']
        if five_minute_indicator == 0:
            if idx < first_triaged:
                df.loc[idx:idx, 'updated_strategy'] = current_strategy
            else:
                # Sequential Strategy - Yellow
                if (i['current_strategy'] == 'sequential' and i['rescued'] == 'yellow'):
                    if i['player_skips'] == 'one or more green':
                        df.loc[idx, 'updated_strategy'] = 'yellow only'
                    elif i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'sequential'
                    elif (i['player_skips'] == 'one of more yellow' or i['player_skips'] == 'at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                # Sequential Strategy - Green
                elif (i['current_strategy'] == 'sequential' and i['rescued'] == 'green'):
                    if (i['player_skips'] == 'one or more green' or i['player_skips'] == 'at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                    elif i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'sequential'
                    elif i['player_skips'] == 'one of more yellow':
                        df.loc[idx, 'updated_strategy'] = 'green only'
                # Yellow only Strategy - Yellow
                elif (i['current_strategy'] == 'yellow only' and i['rescued'] == 'yellow'):
                    if i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'yellow only'
                    elif (i['player_skips'] == 'one of more yellow' or i['player_skips'] == 'at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                # Yellow only Strategy - Green
                elif (i['current_strategy'] == 'yellow only' and i['rescued'] == 'green'):
                    if (i['player_skips'] == 'one or more green' or i['player_skips'] == 'at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                    elif i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'sequential'
                    elif i['player_skips'] == 'one or more yellow':
                        df.loc[idx, 'updated_strategy'] = 'green only'
                # Green only Strategy - Yellow
                elif (i['current_strategy'] == 'green only' and i['rescued'] == 'yellow'):
                    if i['player_skips'] == 'one or more green':
                        df.loc[idx, 'updated_strategy'] = 'yellow only'
                    elif i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'sequential'
                    elif (i['player_skips']=='one or more yellow' or i['player_skips']=='at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                # Green only Strategy - Green
                elif (i['current_strategy'] == 'green only' and i['rescued'] == 'green'):
                    if (i['player_skips'] == 'one or more green' or i['player_skips']=='at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                    elif (i['player_skips'] == 'none' or i['player_skips']=='one or more yellow'):
                        df.loc[idx, 'updated_strategy'] = 'green only'
                # Mixed only Strategy - Yellow
                elif (i['current_strategy'] == 'mixed' and i['rescued'] == 'yellow'):
                    if i['player_skips'] == 'one or more green':
                        df.loc[idx, 'updated_strategy'] = 'yellow only'
                    elif i['player_skips'] == 'none':
                        df.loc[idx, 'updated_strategy'] = 'sequential'
                    elif (i['player_skips'] == 'one or more yellow' or i['player_skips']=='at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                # Mixed only strategy - Green
                elif (i['current_strategy'] == 'mixed' and i['rescued'] == 'green'):
                    if (i['player_skips'] == 'one or more green' and i['player_skips']=='at least one yellow and one green'):
                        df.loc[idx, 'updated_strategy'] = 'mixed'
                    elif (i['player_skips'] == 'none' or i['player_skips']=='one or more yellow'):     
                        df.loc[idx, 'updated_strategy'] = 'green only'
        else:
            # Green only Strategy - Yellow
            if (i['current_strategy'] == 'green only' and i['rescued'] == 'yellow'):
                if i['player_skips'] == 'one or more green':
                    df.loc[idx, 'updated_strategy'] = 'yellow only'
                elif i['player_skips'] == 'none':
                    df.loc[idx, 'updated_strategy'] = 'sequential'
                elif (i['player_skips']=='one or more yellow' or i['player_skips']=='at least one yellow and one green'):
                    df.loc[idx, 'updated_strategy'] = 'mixed'
            # Green only Strategy - Green
            elif (i['current_strategy'] == 'green only' and i['rescued'] == 'green'):
                if (i['player_skips'] == 'one or more green' or i['player_skips']=='at least one yellow and one green'):
                    df.loc[idx, 'updated_strategy'] = 'mixed'
                elif (i['player_skips'] == 'none' or i['player_skips']=='one or more yellow'):
                    df.loc[idx, 'updated_strategy'] = 'green only'
            # Mixed only Strategy - Yellow
            elif (i['current_strategy'] == 'mixed' and i['rescued'] == 'yellow'):
                if i['player_skips'] == 'one or more green':
                    df.loc[idx, 'updated_strategy'] = 'yellow only'
                elif i['player_skips'] == 'none':
                    df.loc[idx, 'updated_strategy'] = 'sequential'
                elif (i['player_skips'] == 'one or more yellow' or i['player_skips']=='at least one yellow and one green'):
                    df.loc[idx, 'updated_strategy'] = 'mixed'
            # Mixed only strategy - Green
            elif (i['current_strategy'] == 'mixed' and i['rescued'] == 'green'):
                if (i['player_skips'] == 'one or more green' and i['player_skips']=='at least one yellow and one green'):
                    df.loc[idx, 'updated_strategy'] = 'mixed'
                elif (i['player_skips'] == 'none' or i['player_skips']=='one or more yellow'):     
                    df.loc[idx, 'updated_strategy'] = 'green only'
                    
                    
# Concatenating all dfs
final_df = pd.concat([trial_4, trial_7, trial_9, trial_11, trial_12])
# Exporting to csv
final_df.to_csv('final_falcon.csv')