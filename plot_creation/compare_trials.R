# Script to compare full trial data files to plots that were created to examine which 
# files were not successful at plot creation. 
json_files <- dir('W:/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Data/trial_data/', pattern = 'metadata')
plots <- dir('W:/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Maps/plots')

json_files_df <- as_tibble(json_files)
plots_df <- as_tibble(plots)

json_trials <- json_files_df %>% 
  separate(value, sep = '_', into = c('a', 'b', 'c', 'd', 'e')) %>%
  select(trial_name = e) %>%
  separate(trial_name, sep = '-', into = c('no', 'value')) %>%
  select(-no) %>%
  mutate(value = as.numeric(value))

plots_trials <- plots_df %>%
  mutate(value = str_remove(value, '.jpeg'),
         value = str_remove(value, 'T'),
         value = str_remove(value, '^0+'),
         value = as.numeric(value))
  
not_plotted <- anti_join(json_trials, plots_trials)
