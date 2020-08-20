#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 08:58:25 2020

@author: cynthia_song
"""

import json
import numpy as np
import pandas as pd


# main program
def main():
    # read in the file that contains the path of each file.
    file1 = open('path.txt', 'r') 
    Lines = file1.readlines() 
    file_names = []
    for line in Lines: 
        file_names.append(line.strip())
        
    directory = file_names[0]
    fname = file_names[1]
    agent_file = file_names[2]
    condition_path = file_names[3]
    survey_path = file_names[4]
    
    data = read_raw(directory, fname)
    temp_df = norm_table(data)
    subject_id = get_sub_id(temp_df)
    df = get_table(temp_df)
    df = set_elapsed_time(df)
    df = forward_fill_na(df)
    room_df = get_room_table(df)
    triage_df = get_triage_table(df)
    event_df = get_next_victim_is_yellow(room_df, triage_df)
    new_df = get_distance(event_df)
    data = read_agent(agent_file)
    new_loc_df = get_new_loc(data)
    new_df = calculate_remain_yellow_victims(new_loc_df, new_df)
    new_df = get_cur_room_victims(new_df, new_loc_df)
    new_df = next_room_has_yellow_victim(new_df, new_loc_df)
    condition_df = read_condition(condition_path)
    new_df = join_condition(condition_df, fname, subject_id, new_df)
    survey_df = get_survey_table(survey_path)
    survey_df = map_survey(survey_df)
    new_df = calculate_join_avg_survey(survey_df, new_df)
    write_final_csv(new_df, fname)

# read in the json file 
def read_raw(directory, fname):
    with open(directory+fname) as f:
        data = json.loads("[" + f.read().replace("}\n{", "},\n{") + "]")
    return data

# flaten nested json into python dataframe
def norm_table(data):   
    temp_df = pd.json_normalize(data)
    temp_df.columns = temp_df.columns.map(lambda x: x.replace(".", "_"))
    return temp_df

# get the subject id from msg_subjects column since there's no subject id information in the file name
def get_sub_id(temp_df):
    temp_df['msg_subjects'] = temp_df['msg_subjects'].apply(lambda x: x[0] if x==x else x)
    sub_arr = list(temp_df['msg_subjects'].unique())
    sub_id = [val for val in sub_arr if str(val) != 'nan'][0].lower()
    subject_id = sub_id[:7]+'_id'+sub_id[7:]
    return subject_id

# extract the columns that start with data and continue work with them
def get_table(temp_df):
    filter_col = [col for col in temp_df if col.startswith('data')]
    df = temp_df[filter_col]
    return df

# Find when the game start and calculate elapsed time based on that
def set_elapsed_time(df):
    df['data_timestamp'] = pd.to_datetime(df['data_timestamp'], format="%Y-%m-%dT%H:%M:%S")
    start_index = df[df['data_mission_state'].str.lower()=='start'].index.values[0]
    start_time = df.at[start_index-1,'data_timestamp']
    df['time_elapsed_minutes'] = (df['data_timestamp']-start_time)/np.timedelta64(1,'m')
    return df

# fill the event rows which has no necessary information with their previous row. 
def forward_fill_na(df):
    cols = ['data_x', 'data_y', 'data_z', 'data_timestamp', 'time_elapsed_minutes']
    df.loc[:,cols] = df.loc[:,cols].ffill()
    return df

# extract the entering room event rows as a dataframe
def get_room_table(df):
    room_df = df[pd.notna(df['data_entered_area_id'])]
    return room_df

# extract the triage event rows as a dataframe
def get_triage_table(df):
    triage_df = df[df['data_triage_state']=='SUCCESSFUL']
    return triage_df

# calculate if next victim triaged is yellow or not    
def get_next_victim_is_yellow(room_df, triage_df):
    room_df['next_room'] = room_df['data_entered_area_id'].shift(-1)
    event_df = room_df.append(triage_df).sort_index()
    event_df['next_room'] = event_df['next_room'].ffill()
    event_df['next_victim_is_yellow'] = event_df['data_color'].bfill()
    event_df['next_victim_is_yellow'] = event_df['next_victim_is_yellow']=='Yellow'
    return event_df

# get the distance from current location to the next triaged victim's location 
def get_distance(event_df):
    event_df['next_victim_x'] = event_df['data_victim_x'].bfill()
    event_df['next_victim_y'] = event_df['data_victim_y'].bfill()
    event_df['next_victim_z'] = event_df['data_victim_z'].bfill()
    event_df['next_victim_triaged_distance'] = ((event_df['data_x']-event_df['next_victim_x'])**2+ (event_df['data_z']-event_df['next_victim_z'])**2+ (event_df['data_y']-event_df['next_victim_y'])**2)**(1/2)
    new_df = event_df.reset_index(drop=True)
    return new_df

# load the agent file that contains area, connection and location information
def read_agent(agent_file):
    with open(agent_file) as f:
        data = json.loads("[" + f.read() + "]")
    return data

# group the victims by room and sum up.
def get_new_loc(data):
    location_df = pd.json_normalize(data ,"locations")  
    new_loc_df = location_df.groupby(['area_id'])[['victims.critical', 'victims.non_critical']].sum().reset_index() 
    return new_loc_df

# calculate remaining yellow victims in the game
def calculate_remain_yellow_victims(new_loc_df, new_df):
    total_yellow_victim = sum(new_loc_df['victims.critical'])    
    new_df['remain_yellow_victim'] = np.where(new_df['data_color'] == 'Yellow', 1, 0)
    new_df['remain_yellow_victim'] = total_yellow_victim - new_df['remain_yellow_victim'].cumsum()  
    return new_df

# calculate current room green and yellow victimes
def get_cur_room_victims(new_df, new_loc_df):  
    new_df['cur_room'] = new_df['data_entered_area_id'].ffill()    
    new_df = pd.merge(new_df, new_loc_df, left_on='cur_room', right_on='area_id', how='left')    
    new_df[['cur_room_yellow_victims', 'cur_room_green_victims']] = new_df[['victims.critical', 'victims.non_critical']].fillna(value=0)
    return new_df    

# calculate if next room entered has yellow vicims or not    
def next_room_has_yellow_victim(new_df, new_loc_df):   
    room_yellow_victim_df =  new_loc_df[['area_id']]  
    room_yellow_victim_df['next_room_has_yellow_victim'] = new_loc_df['victims.critical']==1.0   
    new_df = pd.merge(new_df, room_yellow_victim_df, left_on='next_room', right_on='area_id', how='left')    
    new_df['next_room_has_yellow_victim'] = new_df['next_room_has_yellow_victim'].fillna(value=False)    
    return new_df

# read in the condition file that contains Ss information
def read_condition(condition_path):
    condition_df = pd.read_csv(condition_path)
    return condition_df      

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

# pre-process the survey file
def get_survey_table(survey_path):
    survey_df = pd.read_csv(survey_path)    
    survey_df = survey_df.drop([0, 1]).reset_index(drop=True)    
    survey_df=survey_df[['Q2', 'Q5_1','Q5_2','Q5_3','Q5_4','Q5_5','Q5_6','Q5_7','Q5_8','Q5_9','Q5_10']]    
        
    survey_df['Q5_1'] = survey_df['Q5_1'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_2'] = survey_df['Q5_2'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_3'] = survey_df['Q5_3'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_4'] = survey_df['Q5_4'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_5'] = survey_df['Q5_5'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_6'] = survey_df['Q5_6'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_7'] = survey_df['Q5_7'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_8'] = survey_df['Q5_8'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_9'] = survey_df['Q5_9'].apply(lambda x: x[:-4] if len(x)>3 else x)
    survey_df['Q5_10'] = survey_df['Q5_10'].apply(lambda x: x[:-4] if len(x)>3 else x)   
    return survey_df

# transform the text into value
def map_survey(survey_df):
    mapping = {'Strongly disagree': 1, 'Disagree': 2, 'Somewhat disagree': 3, 'Somewhat agree': 4, 'Agree': 5, 'Strongly agree': 6, '-99': -99}
    survey_df = survey_df.replace({'Q5_1': mapping, 'Q5_2': mapping, 'Q5_3': mapping, 'Q5_4': mapping, 'Q5_5': mapping, 'Q5_6': mapping, 'Q5_7': mapping, 'Q5_8': mapping, 'Q5_9': mapping, 'Q5_10': mapping})
    return survey_df

# calculate the average of each row, ignore the -99 case
def calculate_join_avg_survey(survey_df, new_df):
    survey_df['sat_tendency'] = survey_df[survey_df[['Q5_1', 'Q5_2', 'Q5_3', 'Q5_4', 'Q5_5', 'Q5_6', 'Q5_7', 'Q5_8', 'Q5_9', 'Q5_10']] >0].mean(1)
    satisfy_df = survey_df[['Q2', 'sat_tendency']]    
    new_df = pd.merge(new_df, satisfy_df, left_on='subject_id', right_on='Q2', how='left')    
    return new_df

# output the desired columns
def write_final_csv(new_df, fname):    
    final_df = new_df[['next_victim_is_yellow', 'condition_within_Ss', \
                  'next_victim_triaged_distance', 'sat_tendency', 'remain_yellow_victim',\
                  'time_elapsed_minutes', 'cur_room_yellow_victims', 'cur_room_green_victims', \
                  'next_room_has_yellow_victim', 'condition_between_Ss', 'trial_id']]
    
    final_df.to_csv(fname[:-5]+'.csv')    
    
if __name__ == "__main__":
    main()    
    
    

