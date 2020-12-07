#--------------------------------------------------------------------------
# Load libraries and set working directory
#--------------------------------------------------------------------------

if (!require("pacman")) install.packages("pacman")
library ("pacman")
pacman::p_load(rstatix, ggpubr, corrgram)
#dd <- ("//gallup/dod_clients/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Data/processed_data") # Server execution
dd <- "C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Data/Phase_1" # Local execution
knitr::opts_knit$set(root.dir = dd)

#--------------------------------------------------------------------------
# Check pre-processing errors
#--------------------------------------------------------------------------

setwd("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Data/Phase_1/errors")
list_of_files <- list.files(getwd(), pattern = '\\.txt$')
errors <- lapply(list_of_files, readLines)
errors <- data.frame(matrix(unlist(errors), nrow=length(errors), byrow=T))
files <- data.frame(matrix(unlist(list_of_files), nrow=length(list_of_files), byrow=T))
errors <- cbind (files, errors)
colnames(errors) <- c("error_file", "error")
write.csv(errors, "errors.csv")

#--------------------------------------------------------------------------
# Load experiment-level data ("results_data.csv")
#--------------------------------------------------------------------------

setwd(dd)
games <- read.csv ("results_data.csv", stringsAsFactors = F)

#--------------------------------------------------------------------------
# Generate trial ordering variable 
#--------------------------------------------------------------------------

games <- games %>% 
  group_by(member_id) %>%  mutate(trial_order = order(order(trial_id, decreasing=F)))

#--------------------------------------------------------------------------
# Data checks
#--------------------------------------------------------------------------

length(unique(games$subject_id)) # Should have 75 unique subjects
length(unique(games$trial_id)) # Should have 225 unique trials
table(games$complexity) # Should be balanced by complexity (e.g. 225/3 = 75 in each level)
table(games$training) # Should be balanced by training (e.g. 225/3 = 75 in each level)

#--------------------------------------------------------------------------
# Function to summarize continuous variables, standardize and check distribution
#--------------------------------------------------------------------------

normality_test <- function (test_variable) {
  print(summary(test_variable))
  scaled_variable <- scale(test_variable)
  plot(hist(scaled_variable))
  plot(ggqqplot(scaled_variable))
  plot(ggdensity(scaled_variable, fill = "lightgray"))
  print(shapiro_test(scaled_variable[0:5000]))
  return(scaled_variable)
}

#--------------------------------------------------------------------------
# Screen variables and transform for analysis
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
## Training condition - create dummies for hypothesis testing
#--------------------------------------------------------------------------

games$tradeoff <- as.factor(ifelse(grepl("NoTriage", games$training), c("NoTradeOff"), c("TradeOff")))
games$device <- as.factor(ifelse(grepl("TriageSignal", games$training), c("YesDevice"), c("NoDevice")))
games$q239_cat <- as.factor(ifelse(games$q239=="Yes", "Learned", "Not Learned"))

#--------------------------------------------------------------------------
## Satisficing tendency
#--------------------------------------------------------------------------

games$sat_tendency_std <- normality_test (games$q7_average) 
# Comment: 3 NA values
# Comment: Looks reasonably normal, though shapiro significant

#--------------------------------------------------------------------------
# Load recomputed satisficing tendency factor scores after dropping item 7 ("noseven.csv")
#--------------------------------------------------------------------------

noseven <- read.csv ("noseven.csv", stringsAsFactors = F)
noseven <- subset(noseven, select = c(member_id, V10))
colnames(noseven) <- c("member_id", "sat_tendency_std2")
games <- merge(games, noseven, by=c("member_id"), all.x = TRUE)
games$sat_tendency_std2 <- normality_test (games$sat_tendency_std2)

#--------------------------------------------------------------------------
## Prioritized navigation strategy
#--------------------------------------------------------------------------

table (games$original_nav_strategy)
games$original_nav_strat_yellow <- as.factor(ifelse(
  games$original_nav_strategy =="Yellow First",
  c("Yellow First"), c("Other")))

games$original_nav_strat_yelempt <- as.factor(ifelse(
  games$original_nav_strategy =="Yellow First" |
    games$original_nav_strategy =="Avoid Empty",
  c("Yellow First - Avoid Empty"), c("Other")))

games$original_nav_strat_seq <- as.factor(ifelse(
  games$original_nav_strategy =="Sequential",
  c("Sequential"), c("Other")))

#--------------------------------------------------------------------------
## Strategy planned in next trial 
#--------------------------------------------------------------------------

games_next <- subset(games, select = c(trial_id, member_id, original_nav_strat_yelempt))
games_next$trial_id <- games_next$trial_id-1 # Subtract trial_id - 1 to create an index of "next trials". 
colnames (games_next)[3] <- c("next_nav_strat_yelempt") # Change column names
games <- merge(games,games_next, by=c("member_id","trial_id"), all.x = TRUE) # Merge new variables

#--------------------------------------------------------------------------
## Prioritized victim strategy - Explore and recode into binaries
#--------------------------------------------------------------------------

table (games$original_victim_strategy)
games$original_vic_strat_yellow <- as.factor(ifelse(
  games$original_victim_strategy =="Yellow First",
  c("Yellow First"), c("Other")))

games$original_vic_strat_seq <- as.factor(ifelse(
  games$original_victim_strategy =="Sequential",
  c("Sequential"), c("Other")))

#--------------------------------------------------------------------------
## Spatial ability
#--------------------------------------------------------------------------

games$spatial_ability_std <- normality_test (games$q8_average) 
# Comment: 3 NA values
# Comment: Looks reasonably normal, though shapiro significant

#--------------------------------------------------------------------------
## Video-gaming experience
#--------------------------------------------------------------------------

games$videogame_experience_std <- normality_test (games$videogame_experience) 
# Comment: Possible bimodal

#--------------------------------------------------------------------------
## Workload
#--------------------------------------------------------------------------

games$workload_std <- normality_test (games$workload) 
# Comment: Heavy negative skew, possible ceiling effect

#--------------------------------------------------------------------------
## Final score
#--------------------------------------------------------------------------

games$final_score_std <- normality_test (games$final_score)
# Comment: Negative skew, long left tail

#--------------------------------------------------------------------------
## Competency_score
#--------------------------------------------------------------------------

games$competency_score_std <- - normality_test (games$competency_score) # Standardized and reversed to facilitate interpretation (higher score, greater competency)
# Comment: Positive skew, long right tail

#--------------------------------------------------------------------------
## Calculate most frequently used victim and navigation strategies
#--------------------------------------------------------------------------
allVars <- colnames(games)
vic_time_vars <- games[allVars [grepl("victim", allVars) & grepl("time", allVars)]]
games$most_time_vic_strat <- colnames(vic_time_vars)[apply(vic_time_vars,1,which.max)]
games$most_time_vic_strat <- gsub("victim_strategy_data.|.time_spent", "", games$most_time_vic_strat)
games$most_time_vic_strat_yellow <- as.factor(ifelse(games$most_time_vic_strat =="Yellow.First", "Yellow.First","Other"))
games$most_time_vic_strat_seq <- as.factor(ifelse(games$most_time_vic_strat =="Sequential", "Sequential","Other"))

nav_time_vars <- games[allVars [grepl("navigation", allVars) & grepl("time", allVars)]]
games$most_time_nav_strat <- colnames(nav_time_vars)[apply(nav_time_vars,1,which.max)]
games$most_time_nav_strat <- gsub("navigation_strategy_data.|.time_spent", "", games$most_time_nav_strat)
games$most_time_nav_strat_seq <- as.factor(ifelse(games$most_time_nav_strat =="Sequential", "Sequential","Other"))
games$most_time_nav_strat_yel <- as.factor(ifelse(games$most_time_nav_strat =="Yellow.First", "Yellow.First","Other"))

#--------------------------------------------------------------------------
## Calculate most beneficial victim and navigation strategies (points per minute)
#--------------------------------------------------------------------------

vic_rate_vars <- games[allVars [grepl("victim", allVars) & grepl("points", allVars)]]
games$most_points_vic_strat <- colnames(vic_rate_vars)[apply(vic_rate_vars,1,which.max)]
games$most_points_vic_strat <- gsub("victim_strategy_data.|.points_per_minute", "", games$most_points_vic_strat)
games$most_points_vic_strat_yellow <- as.factor(ifelse(games$most_points_vic_strat =="Yellow.First", "Yellow.First","Other"))
games$most_points_vic_strat_seq <- as.factor(ifelse(games$most_points_vic_strat =="Sequential", "Sequential","Other"))

nav_rate_vars <- games[allVars [grepl("navigation", allVars) & grepl("points", allVars)]]
games$most_points_nav_strat <- colnames(nav_rate_vars)[apply(nav_rate_vars,1,which.max)]
games$most_points_nav_strat <- gsub("navigation_strategy_data.|.points_per_minute", "", games$most_points_nav_strat)
games$most_points_nav_strat_seq <- as.factor(ifelse(games$most_points_nav_strat =="Sequential", "Sequential","Other"))
games$most_points_nav_strat_yel <- as.factor(ifelse(games$most_points_nav_strat =="Yellow.First", "Yellow.First","Other"))

#--------------------------------------------------------------------------
## Merge strategy use variables from previous trial
#--------------------------------------------------------------------------

# Select subset of variables of interest. 
games_prev <- subset(games, select=c(
  victim_strategy_data.Yellow.First.time_spent, 
  victim_strategy_data.Yellow.First.points_per_minute,
  victim_strategy_data.Sequential.time_spent,             
  victim_strategy_data.Sequential.points_per_minute,
  most_time_vic_strat_yellow, original_vic_strat_yellow, most_points_vic_strat_yellow,
  most_time_vic_strat_seq, most_points_vic_strat_seq,
  navigation_strategy_data.Yellow.First.time_spent,	
  navigation_strategy_data.Yellow.First.points_per_minute,
  navigation_strategy_data.Sequential.time_spent,	
  navigation_strategy_data.Sequential.points_per_minute,
  most_time_nav_strat_seq, original_nav_strat_seq, most_points_nav_strat_seq,
  most_time_nav_strat_yel, most_points_nav_strat_yel, 
  subject_id, trial_id))

# Subtract trial_id - 1 to create an index of "previous trials". 
games_prev$trial_id <- games_prev$trial_id+1

# Change column names
colnames (games_prev)[1:18] <- c("vic_strat_yel_prev_time", 
                                "vic_strat_yel_prev_rate", 
                                "vic_strat_seq_prev_time", 
                                "vic_strat_seq_prev_rate",
                                "vic_strat_yel_prev_most_time",
                                "vic_strat_yel_prev_original",
                                "vic_strat_yel_prev_most_points",
                                "vic_strat_seq_prev_most_time",
                                "vic_strat_seq_prev_most_points",
                                "nav_strat_yel_prev_time", 
                                "nav_strat_yel_prev_rate",
                                "nav_strat_seq_prev_time",
                                "nav_strat_seq_prev_rate", 
                                "nav_strat_seq_prev_most_time",
                                "nav_strat_seq_prev_original", 
                                "nav_strat_seq_prev_most_points", 
                                "nav_strat_yel_prev_most_time", 
                                "nav_strat_yel_prev_most_points")
# Merge new variables
games <- merge(games,games_prev, by=c("subject_id","trial_id"), all.x = TRUE)

games$vic_strat_yel_prev_time_std <- normality_test (games$vic_strat_yel_prev_time)
games$vic_strat_yel_prev_rate_std <- normality_test (games$vic_strat_yel_prev_rate)
games$vic_strat_seq_prev_time_std <- normality_test (games$vic_strat_seq_prev_time )
games$vic_strat_seq_prev_rate_std <- normality_test (games$vic_strat_seq_prev_rate)
games$nav_strat_yel_prev_time_std <- normality_test (games$nav_strat_yel_prev_time )
games$nav_strat_yel_prev_rate_std <- normality_test (games$nav_strat_yel_prev_rate)
games$nav_strat_seq_prev_time_std <- normality_test (games$nav_strat_seq_prev_time)
games$nav_strat_seq_prev_rate_std <- normality_test (games$nav_strat_seq_prev_rate )

#--------------------------------------------------------------------------
# Load event-level data ("events_data.csv") and subset into victim and room events
#--------------------------------------------------------------------------

events <- read.csv ("results_events.csv", stringsAsFactors = F)
table(events$event, useNA="always")

#--------------------------------------------------------------------------
# Merge complexity levels
#--------------------------------------------------------------------------

complexity <- subset(games, select = c(trial_id, complexity))
events <- merge(events, complexity, by=c("trial_id"), all.x = TRUE)

#--------------------------------------------------------------------------
# Merge trial ordering variable 
#--------------------------------------------------------------------------

trial_order <- subset(games, select = c(trial_id, trial_order))
str(trial_order)
events <- merge(events, trial_order, by=c("trial_id"), all.x = TRUE)

events$trial_order <- as.factor(events$trial_order)

#--------------------------------------------------------------------------
## Training conditions - merge with events data
#--------------------------------------------------------------------------

training_vars <- subset (games, select = c(trial_id, training, tradeoff, device))
events <- merge(events,training_vars, by=c("trial_id"), all.x = TRUE)

#--------------------------------------------------------------------------
## Remaining seconds
#--------------------------------------------------------------------------

events$seconds_remaining_std <- normality_test (events$seconds_remaining)
# By definition, a uniform distribution

#--------------------------------------------------------------------------
## Remaining yellow victims expire (seconds_remaining<320 | seconds_remaining>280)
#--------------------------------------------------------------------------

events$five_minutes <- as.factor(ifelse(events$seconds_remaining< 340 & events$seconds_remaining>300,
  c("Minutes 5-6"), c("Minutes 0-4:6-10")))

#--------------------------------------------------------------------------
## Subset into victims and rooms
#--------------------------------------------------------------------------

victims <- subset (events, event == "victim_triaged") 
rooms <- subset (events, event == "room_entered") 

#--------------------------------------------------------------------------
## victim_color
#--------------------------------------------------------------------------

table(victims$victim_color, useNA="always")

#--------------------------------------------------------------------------
## Remaining yellow victims
#--------------------------------------------------------------------------

victims$total_yellow_victims_remaining_std <- normality_test (victims$total_yellow_victims_remaining)

victims$all_yellow_rescued <- as.factor(ifelse(
  victims$total_yellow_victims_remaining == 0,
  c("Yellows rescued"), c("Yellow remain")))
table(victims$all_yellow_rescued)

#--------------------------------------------------------------------------
## Yellow and green victims in current room
#--------------------------------------------------------------------------

table(rooms$yellow_victims_in_current_room, useNA="always")
table(rooms$green_victims_in_current_room, useNA="always")

#--------------------------------------------------------------------------
## room_type
#--------------------------------------------------------------------------

table(rooms$room_type, useNA="always")

#--------------------------------------------------------------------------
## victim_strategy - Code dummies for yellow first
#--------------------------------------------------------------------------

table(victims$victim_strategy, useNA="always")

victims$vic_strat_yellow <- as.factor(ifelse(
  victims$victim_strategy =="Yellow First",
  c("Yellow First"), c("Other")))

#--------------------------------------------------------------------------
## victim_strategy update - Create index within trial and compare strategies
#--------------------------------------------------------------------------

victims <- victims[with(victims, order(trial_id, event_index_number)),]
victims <- victims %>% 
  group_by(trial_id) %>%
  mutate(event_ID = dplyr::row_number())

vic_strat_prev <- subset(victims, select=c(victim_strategy, member_id, trial_id, event_ID))
vic_strat_prev$event_ID <- vic_strat_prev$event_ID+1
colnames (vic_strat_prev)[1] <- c("victim_strategy_prev")
victims <- merge(victims,vic_strat_prev, by=c("member_id","trial_id", "event_ID"), all.x = TRUE)
victims$victim_strategy_update <- as.factor(
  ifelse(victims$victim_strategy==victims$victim_strategy_prev,
         c("No Update"), c("Update")))

#--------------------------------------------------------------------------
## Victim rates
#--------------------------------------------------------------------------

victims$yellow_per_minute_std <- normality_test (victims$yellow_per_minute)
victims$green_per_minute_std <- normality_test (victims$green_per_minute)
victims$expected_green_rate_std <- normality_test (victims$expected_green_rate)
#cor(victims$expected_green_rate_std, victims$green_per_minute_std) # expected_green_rate is redundant

#--------------------------------------------------------------------------
## Average victim search times
#--------------------------------------------------------------------------

victims$green_search_time_std <- normality_test (victims$green_search_time)
victims$yellow_search_time_std <- normality_test (victims$yellow_search_time)

#--------------------------------------------------------------------------
## Spare time to rescue remaining yellow victims - 
## Time to 5-minute mark - (number of remaining yellow victims * (average search time + time to be rescued (15 seconds))) 
#--------------------------------------------------------------------------

victims$spare_time_yellows <- victims$seconds_remaining - 
  ((victims$total_yellow_victims_remaining) * (victims$yellow_search_time + 15))
victims$spare_time_yellows_std <- normality_test (victims$spare_time_yellows)

#--------------------------------------------------------------------------
## navigation_strategy
#--------------------------------------------------------------------------

table(rooms$nav_strategy, useNA="always")

rooms$nav_strat_yellow <- as.factor(ifelse(
  rooms$nav_strategy =="Yellow First",
  c("Yellow First"), c("Other")))

#--------------------------------------------------------------------------
## nav_strategy update - Create index within trial and compare strategies
#--------------------------------------------------------------------------

rooms <- rooms[with(rooms, order(trial_id, event_index_number)),]
rooms <- rooms %>% 
  group_by(trial_id) %>%
  mutate(event_ID = dplyr::row_number())

nav_strat_prev <- subset(rooms, select=c(nav_strategy, member_id, trial_id, event_ID))
nav_strat_prev$event_ID <- nav_strat_prev$event_ID+1
colnames (nav_strat_prev)[1] <- c("navigation_strategy_prev")
rooms <- merge(rooms,nav_strat_prev, by=c("member_id","trial_id", "event_ID"), all.x = TRUE)
rooms$nav_strategy_update <- as.factor(
  ifelse(rooms$nav_strategy==rooms$navigation_strategy_prev,
         c("No Update"), c("Update")))

#--------------------------------------------------------------------------
## Learning - Create index within participant to track progression from trial to trial
#--------------------------------------------------------------------------

rooms <- rooms[with(rooms, order(trial_id, event_index_number)),]
rooms <- rooms %>% group_by(member_id) %>% mutate(event_ID_2 = dplyr::row_number())

#--------------------------------------------------------------------------
## Learning - Create player aggregate number of empty rooms entered across trials
#--------------------------------------------------------------------------

rooms_max <- aggregate(cbind(rooms_entered_empty,rooms_entered_not_empty) ~ trial_id + member_id, rooms, max)
#rooms_max <- data.frame(trial_id=rooms_max$trial_id, 
#                        member_id=rooms_max$member_id,
#                        rooms_entered_empty_running=rooms_max$rooms_entered_empty, 
#                        rooms_entered_not_empty_running=rooms_max$rooms_entered_not_empty)

rooms_max_prev_1 <- data.frame(trial_id=rooms_max$trial_id+1, 
                               member_id=rooms_max$member_id,
                               empty_max_prev_1=rooms_max$rooms_entered_empty, 
                               not_empty_max_prev_1=rooms_max$rooms_entered_not_empty)

rooms_max_prev_2 <- data.frame(trial_id=rooms_max$trial_id+2, 
                               member_id=rooms_max$member_id,
                               empty_max_prev_2=rooms_max$rooms_entered_empty, 
                               not_empty_max_prev_2=rooms_max$rooms_entered_not_empty)

rooms <- merge(rooms,rooms_max_prev_1, by=c("member_id","trial_id"), all.x = TRUE)
rooms$empty_max_prev_1[is.na(rooms$empty_max_prev_1)] <- 0
rooms$not_empty_max_prev_1[is.na(rooms$not_empty_max_prev_1)] <- 0

rooms$rooms_entered_empty_running <- rooms$rooms_entered_empty
rooms$rooms_entered_not_empty_running <- rooms$rooms_entered_not_empty

rooms$rooms_entered_empty_running <- rooms$rooms_entered_empty_running + rooms$empty_max_prev_1
rooms$rooms_entered_not_empty_running <- rooms$rooms_entered_not_empty_running + rooms$not_empty_max_prev_1

rooms <- merge(rooms,rooms_max_prev_2, by=c("member_id","trial_id"), all.x = TRUE)
rooms$empty_max_prev_2[is.na(rooms$empty_max_prev_2)] <- 0
rooms$not_empty_max_prev_2[is.na(rooms$not_empty_max_prev_2)] <- 0

rooms$rooms_entered_empty_running <- rooms$rooms_entered_empty_running + rooms$empty_max_prev_2
rooms$rooms_entered_not_empty_running <- rooms$rooms_entered_not_empty_running + rooms$not_empty_max_prev_2

rooms <- rooms[,-which(names(rooms) %in% c("empty_max_prev_1",
                                           "empty_max_prev_2", 
                                           "not_empty_max_prev_1",
                                           "not_empty_max_prev_2"))]

#--------------------------------------------------------------------------
## Learning - Merge player aggregate number of empty rooms entered across trials to games data
#--------------------------------------------------------------------------

rooms_trial_max <- aggregate(cbind(rooms_entered_empty_running,rooms_entered_not_empty_running) ~ trial_id + member_id, rooms, max)
colnames(rooms_trial_max) <- c("trial_id", "member_id", "empty_max_trial", "not_empty_max_trial")
games <- merge(games,rooms_trial_max, by=c("member_id","trial_id"), all.x = TRUE)

games$empty_max_trial_std <- normality_test (games$empty_max_trial)
games$not_empty_max_trial_std <- normality_test (games$not_empty_max_trial)

#--------------------------------------------------------------------------
## Learning - Merge player aggregate number of empty rooms entered in the previous trial
#--------------------------------------------------------------------------

games_post <- subset(games, select=c(trial_id, member_id, empty_max_trial, not_empty_max_trial))
colnames(games_post)[3:4] <- c("empty_max_trial_prev", "not_empty_max_trial_prev")
games_post$trial_id <- games_post$trial_id+1
games <- merge(games,games_post, by=c("member_id","trial_id"), all.x = TRUE)

games$empty_max_trial_prev[is.na(games$empty_max_trial_prev)] <- 0
games$not_empty_max_trial_prev[is.na(games$not_empty_max_trial_prev)] <- 0

games$empty_max_trial_prev_std <- normality_test (games$empty_max_trial_prev)
games$not_empty_max_trial_prev_std <- normality_test (games$not_empty_max_trial_prev)

#--------------------------------------------------------------------------
## navigation_strategy
#--------------------------------------------------------------------------

table(rooms$nav_strategy, useNA="always")

#--------------------------------------------------------------------------
## rooms_entered_empty (device punishments)
#--------------------------------------------------------------------------

rooms$rooms_entered_empty_std <- normality_test (rooms$rooms_entered_empty)
# Extreme positive skew

#--------------------------------------------------------------------------
## rooms_entered_not_empty (device rewards)
#--------------------------------------------------------------------------

rooms$rooms_entered_not_empty_std <- normality_test (rooms$rooms_entered_not_empty)
# Some positive skew

#--------------------------------------------------------------------------
## Add device incentives and disincentives games-level dataset
#--------------------------------------------------------------------------

rooms_entered_empty <- aggregate(rooms_entered_empty ~ member_id+trial_id, data = events, max)
rooms_entered_not_empty <- aggregate(rooms_entered_not_empty ~ member_id+trial_id, data = events, max)
games <- merge(games,rooms_entered_empty, by=c("member_id","trial_id"), all.x = TRUE)
games <- merge(games,rooms_entered_not_empty, by=c("member_id","trial_id"), all.x = TRUE)

games$rooms_entered_empty_std <- normality_test (games$rooms_entered_empty)
games$rooms_entered_not_empty_std <- normality_test (games$rooms_entered_not_empty)

#--------------------------------------------------------------------------
## Add prior use of device summary data to games-level dataset
#--------------------------------------------------------------------------

prior_use <- aggregate(prior_use_consistent ~ member_id+trial_id, data = events, max)
prior_use$trial_id <- prior_use$trial_id+1
games <- merge(games,prior_use, by=c("member_id","trial_id"), all.x = TRUE)
games$prior_use_consistent_std <- normality_test (games$prior_use_consistent)

#--------------------------------------------------------------------------
## Add skipped yellow victims to games-level dataset
#--------------------------------------------------------------------------

skipped_yellow <- aggregate(left_behind_yellow ~ member_id+trial_id, data = events, max)
games <- merge(games,skipped_yellow, by=c("member_id","trial_id"), all.x = TRUE)
games$left_behind_yellow_max_std <- normality_test (games$left_behind_yellow)
games$left_behind_yellow_cat <- as.factor(
  ifelse(games$left_behind_yellow==0,
         c("Skipped 0 yellows"), c("Skipped 1 or more yellows")))

#--------------------------------------------------------------------------
## Add satisficing tendency measure to event-level dataset
#--------------------------------------------------------------------------

sat_tendency <- subset(games, select = c(trial_id, sat_tendency_std, sat_tendency_std2))
victims <- merge(
  victims, sat_tendency, by=c("trial_id"), all.x = TRUE)

#--------------------------------------------------------------------------
## Save processed data for analysis
#--------------------------------------------------------------------------

write.csv (games, "results_data_proc.csv")
write.csv (events, "results_events_proc.csv")
write.csv (victims, "results_victims_proc.csv")
write.csv (rooms, "results_rooms_proc.csv")

#--------------------------------------------------------------------------
## Render into notebook (run code below in separate script to test this one)
#--------------------------------------------------------------------------

#setwd ("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Analytics/Phase_1") # Local execution
#rmarkdown::render("data_prep.R")
