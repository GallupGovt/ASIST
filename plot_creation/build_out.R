# Build R Script - for testing only
test_json <- stream_in(file('W:/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Maps/random_trials/HSRData_TrialMessages_CondBtwn-NoTriageNoSignal_CondWin-FalconMed-StaticMap_Trial-43_Team-na_Member-26_Vers-3.metadata'))
test_json_flat <- flatten(test_json)

vic_order <- test_json_flat %>%
  filter(data.triage_state == 'SUCCESSFUL') %>% 
  select(data.victim_z, data.victim_x, data.victim_y, data.color, data.mission_timer, '@timestamp') %>%
  arrange(desc(data.mission_timer)) %>%
  mutate(victim_order = 1:n()) %>%
  select(-data.victim_y) %>%
  mutate(string_vic_order = paste0('V', victim_order)) 

# Stopped here. 

player_movement <- test_json_flat %>%
  select(data.y, data.x, data.z, data.motion_y, data.motion_x, data.motion_z, data.mission_timer, '@timestamp') %>%
  filter(!is.na(data.y), 
         data.mission_timer != 'Mission Timer not initialized.') %>% 
  mutate(time = ms(data.mission_timer)) %>%
  mutate(seconds = seconds(time)) %>% 
  select(-time) %>% 
  mutate(seconds = as.numeric(seconds)) %>%
  mutate(player_color = case_when(
    between(seconds, 0, 300) ~ 1,
    between(seconds, 301, 450) ~ 2,
    between(seconds, 451, 600) ~ 3,
    TRUE ~ 4
  ))
  


skimr::skim(json_db$data.mission_timer)

test <- test_json_flat %>%
  filter(data.triage_state == 'SUCCESSFUL')


asist_plot <- ggplot() + 
  geom_rect(data = area, mapping = aes(xmin = x1, ymin = y1, xmax = x2, ymax = y2), color = 'black', alpha = .2) + 
  geom_rect(data = connections, mapping = aes(xmin = x, ymin = y, xmax = x2, ymax = y2), color = 'white', fill = 'white') + 
  geom_text(data = area, aes(x=x1+(x2-x1)/2, y=y1+(y2-y1)/2, label= name, color = 'grey50'), size = 3) +
  geom_point(data = player_movement, aes(x = data.x, y = data.z, color = if_else(player_color == 1, 'green', 
                                                                                  if_else(player_color == 2, 'blue', 'black'))), size = .8, alpha = .2) +
  geom_point(data = mission_victim_list, aes(x = x, y = z, color = if_else(green == 1, 'green', 'gold1')), size = 3, shape = 15) + 
  geom_circle(data = vic_order, aes(x0 = data.victim_x, y0 = data.victim_z, r = .8)) + 
  geom_text(data = vic_order, aes(x = data.victim_x, y = data.victim_z, label = string_vic_order, vjust = -1.5), size = 3, check_overlap = TRUE) +
  scale_color_identity() + 
  theme_classic() +
  theme(
    axis.title = element_blank(),
    axis.text = element_blank()
  )

asist_plot
