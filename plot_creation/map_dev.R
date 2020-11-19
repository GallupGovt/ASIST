# Full Function ----

# Needed libraries 
library(tidyverse)
library(tidylog)
library(jsonlite)
library(ggforce)
library(lubridate)
source('source.R')


files <- dir('W:/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Data/trial_data/', pattern = 'metadata')

# Get original map area and connections ----
agent_file <- 'W:/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Maps/agents/Agents_IHMCLocationMonitor_ConfigFolder_Falcon.json'
agent_file_json <- fromJSON(agent_file, flatten = TRUE)
area <- agent_file_json[['areas']]
connections <- agent_file_json[['connections']]

# A function to orchestrate all other functions in source.R
process_maps <- function(x) {
  json_ingest(x)
  victim_list(json_flat)
  player_mov(json_flat)
  victim_order(json_flat)
  trial_num <- json_flat %>%
    filter(!is.na(data.trial_number)) %>%
    select(data.trial_number) %>% distinct()
  trial_number <<- as.vector(trial_num[1,])

 plot_it_all(area, connections, mission_victim_list, player_movement)
}

# Iterate it all 
# Make it safe
safe_process_maps <- safely(process_maps)

map(files, safe_process_maps)
