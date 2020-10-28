import json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta


##################################################
# Helper Functions
##################################################

# converts message stream into json list
def loadMetadata(filepath):
  with open(filepath) as f:
    messages = f.readlines()
  return messages

# helper to get subhect IDs
def getSubject(messages):
  return json.loads(messages[0])['data']['subjects'][0]

# calculate time elapsed along each row (in seconds)
def calculateElapsedTime(df):
  elapsedTime = []
  t0 = pd.Timestamp(df.timestamp[0])
  for tx in df.timestamp:
    elapsedTime.append((pd.Timestamp(tx) - t0).total_seconds())

  df['timeElapsed'] = elapsedTime
  return df

# calculate time spent along each row (in seconds)
def calculateSpentTime(df):
  spentTime = []
  for i in range (len(df.timestamp) - 1):
    spentTime.append((pd.Timestamp(df.timestamp[i+1])\
                    - pd.Timestamp(df.timestamp[i])).total_seconds())

  spentTime.append(-1)
  df['timeSpent'] = spentTime
  return df

# get score for player
def playerScore(messages, score_identifier, mission_identifier):

  # filter messages
  m_score = list(filter(lambda k: score_identifier in k, messages))
  m_mission = list(filter(lambda k: mission_identifier in k, messages))

  # initialize score dataframe
  df_score = pd.DataFrame(index=np.arange(0,len(m_mission)+len(m_score)),
                          columns=['timestamp', 'player', 'score'])

  # parse mission events (start and end)
  for i in range(0,len(m_mission)):
    d = json.loads(m_mission[i])
    df_score.loc[i] = [d['header']['timestamp'],
                       d['data']['mission']+ "-" + d['data']['mission_state'],
                       0]

  # parse score changes
  for i in range(0,len(m_score)):
    d = json.loads(m_score[i])
    scores = d['data']['scoreboard']
    df_score.loc[len(m_mission)+i] = [d['msg']['timestamp'],
                                      list(scores.keys())[0],
                                      list(scores.values())[0]]

  df_score = df_score.dropna()
  df_score = df_score.sort_values(by='timestamp')
  df_score = df_score.reset_index(drop=True)
  df_score = calculateElapsedTime(df_score)

  return df_score

# get triage data for victims
def victimState(messages, triage_identifier, mission_identifier):

  # filter messages
  m_triage = list(filter(lambda k: triage_identifier in k, messages))
  m_mission = list(filter(lambda k: mission_identifier in k, messages))

  # initialize victim dataframe
  cols=['timestamp', 'mission_timer', 'triage_state', 'color',
        'victim_z', 'victim_x', 'playername','victim_y',]
  df_triage = pd.DataFrame(index=np.arange(0,len(m_mission)+len(m_triage)),
                           columns=cols)

  # parse mission events (start and end)
  for i in range(0,len(m_mission)):
    d = json.loads(m_mission[i])
    df_triage.loc[i] = [d['header']['timestamp'],
                        d['data']['mission_timer'],
                        '', '', '', '',
                        d['data']['mission']+ "-" + d['data']['mission_state'],
                        '']

  # parse triage changes
  for i in range(0,len(m_triage)):
    d = json.loads(m_triage[i])
    triage_state = d['data']
    df_triage.loc[len(m_mission)+i,] = triage_state
    df_triage.loc[len(m_mission)+i, 'timestamp'] = d['msg']['timestamp']

  df_triage = df_triage.sort_values(by='timestamp')
  df_triage = df_triage.reset_index(drop=True)
  df_triage = calculateElapsedTime(df_triage)
  df_triage = calculateSpentTime(df_triage)
  df_triage.timeSpent = df_triage.timeSpent.shift(1) # adjust for time column

  return df_triage

# get location data for player
def playerLocation(messages, location_identifier, mission_identifier):

  # filter messages
  m_location = list(filter(lambda k: location_identifier in k, messages))
  m_mission = list(filter(lambda k: mission_identifier in k, messages))

  # initialize location dataframe
  cols=['timestamp', 'player', 'entered_area_id', 'entered_area_name']
  df_location = pd.DataFrame(index=np.arange(0,len(m_mission)+len(m_location)),
                             columns=cols)

  # parse mission events (start and end)
  for i in range(0,len(m_mission)):
    d = json.loads(m_mission[i])
    df_location.loc[i] = [d['header']['timestamp'],
                        d['data']['mission']+ "-" + d['data']['mission_state'],
                        '',
                        '']

  # parse all location changes (IHMCLocationMonitor)
  for i in range(0,len(m_location)):
    d = json.loads(m_location[i])
    df_location.loc[len(m_mission)+i] = [d['msg']['timestamp'],
                                         d['data']['playername'],
                                         d['data']['entered_area_id'],
                                         d['data']['entered_area_name']]

  df_location = df_location.dropna()
  df_location = df_location.sort_values(by='timestamp')
  df_location = df_location.reset_index(drop=True)
  df_location = calculateElapsedTime(df_location)
  df_location = calculateSpentTime(df_location)

  return df_location

##################################################
# Competency Test Functions
##################################################

def competencyTestState(messages, competencyTask_identifier):

  # filter messages
  m_task = list(filter(lambda k: competencyTask_identifier in k, messages))

  # initialize task dataframe
  df_task = pd.DataFrame(index=np.arange(0,len(m_task)),
                         columns=['timestamp', 'task_message'])

  # parse competency task events
  for i in range(0,len(m_task)):
    d = json.loads(m_task[i])
    df_task.loc[i] = [d['header']['timestamp'], d['data']['task_message']]

  df_task = df_task.sort_values(by='timestamp')
  df_task = df_task.drop_duplicates(subset=['task_message'], keep='last')
  df_task = df_task.reset_index(drop=True)
  df_task = calculateElapsedTime(df_task)
  df_task = calculateSpentTime(df_task)
  df_task.timeSpent = df_task.timeSpent.shift(1) # adjust for time column

  return df_task



##################################################
# GSheet Functions
##################################################
# import gspread
# from google.colab import auth
# from gspread_dataframe import set_with_dataframe
# from oauth2client.client import GoogleCredentials
#
# def loadGSheet(data_sheet_name):
#   """
#   Loads GSheet with auth check
#   """
#   auth.authenticate_user()
#   # print("   User Authenticated ... ")
#   gc = gspread.authorize(GoogleCredentials.get_application_default())
#   sheets = gc.open(data_sheet_name)
#   return sheets
#
# def readDictFromGSheets(data_sheet_name):
#   """
#   Read existing data from gsheets into dict format
#   Returns dictionary of dataframes: dict[sheet_names] = data
#   """
#   sheets = loadGSheet(data_sheet_name)
#   print("   Reading GSheet: " + data_sheet_name +" ...")
#   data_dict = {}
#   for sheet in sheets.worksheets():
#     rows = sheet.get_all_values()
#     data = pd.DataFrame.from_records(rows[1:], columns=rows[0])
#     data = data.set_index(data.columns.values[0])
#     # data.index = pd.to_datetime(data.index)
#     data_dict[sheet.title] = data
#   return data_dict
#
# def readDfFromGSheetTab(data_sheet_name, tab_name):
#   """
#   Read existing data from a tab in gsheet
#   Returns dataframe
#   """
#   sheet = loadGSheet(data_sheet_name).worksheet(tab_name)
#   print("   Reading GSheet: " + data_sheet_name + " > " + tab_name + " ...")
#   rows = sheet.get_all_values()
#   return pd.DataFrame.from_records(rows[1:], columns=rows[0])
#
# def writeDictToGSheets(data_sheet_name, data_dict):
#   """
#   Write dict to gsheets
#   Creates workbook with keys as sheet names
#   """
#   sheets = loadGSheet(data_sheet_name)
#   print("   Writing GSheet: " + data_sheet_name +" ...")
#   for key in sorted(data_dict.keys()):
#     try:
#       sheet = sheets.worksheet(key)
#       sheet.clear()
#     except:
#       sheet = sheets.add_worksheet(key, 10, 10)
#     set_with_dataframe(sheet, data_dict[key], include_index=True)
#   return
#
# def writeDfToGSheetTab(data_sheet_name, tab_name, df):
#   """
#   Write df to tab in gsheet
#   Creates workbook with keys as sheet names
#   """
#   sheets = loadGSheet(data_sheet_name)
#   print("   Writing GSheet: " + data_sheet_name + " > " + tab_name + " ...")
#   try:
#     sheet = sheets.worksheet(tab_name)
#     sheet.clear()
#   except:
#     sheet = sheets.add_worksheet(tab_name, 10, 10)
#   set_with_dataframe(sheet, df, include_index=True)
#   return
#
# def deleteGSheetTabs(data_sheet_name, tab_names):
#   """
#   Deletes list of tabs from GSheet
#   """
#   sheets = loadGSheet(data_sheet_name)
#   for tab in tab_names:
#     print("   Deleting GSheet: " + data_sheet_name + " > " + tab + " ...")
#     sheets.del_worksheet(sheets.worksheet(tab))
#   return
