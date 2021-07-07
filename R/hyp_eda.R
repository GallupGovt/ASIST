#' ---
#' title: "ASIST - Gallup Experiment 1 Exploratory Analysis"
#' author: "Pablo Diego-Rosell, PhD"
#' date: "November 27, 2020"
#' output:
#'    html_document:
#'      toc: true
#' theme: united
#' ---

#' #Setup

#--------------------------------------------------------------------------
# Set working directory, load libraries and data
#--------------------------------------------------------------------------

rm(list=ls(all=t))
setwd ("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Data/Phase_1") # Local execution
#setwd ("//gallup/dod_clients/DARPA_ASIST/CONSULTING/Analytics/Phase_1/Data/processed_data") # Server execution
if (!require("pacman")) install.packages("pacman")
library ("pacman")
pacman::p_load(rstatix, ggpubr, corrgram, lme4, lmerTest, dplyr, sjPlot, sjmisc, 
               ggeffects, lattice, see, randomForest, VSURF, tibble, tidyverse, 
               reshape2, plotly, MASS, rstanarm, bayesplot)
games <- read.csv ("results_data_proc.csv")
events <- read.csv ("results_events_proc.csv")
victims <- read.csv ("results_victims_proc.csv")
rooms <- read.csv ("results_rooms_proc.csv")

# Create auxiliary variables and subsets

rooms$quarters <- cut(rooms$seconds_remaining, 
                      breaks=c(-Inf, 150, 300, 450, Inf), 
                      labels=c(4,3,2,1))
rooms$trial_order <- as.factor(rooms$trial_order)
victims_first_half <- subset (victims, seconds_remaining >=300)
rooms_first_half <- subset (rooms, seconds_remaining >=300)

#--------------------------------------------------------------------------
# Exploratory analysis function 
#--------------------------------------------------------------------------

exp_func <- function (DV, IV, data) {
  print (paste("DESCRIPTIVE ANALYSIS OF DV =", DV, "& IV =", IV))
  depvar <- data[c(DV)][,1]
  indvar <- data[c(IV)][,1]
  formula = as.formula(paste(DV, IV, sep="~"))
  print(paste("indvar =", IV))
  if (class(depvar)=="factor" & class(indvar) =="factor") {
    print(table(indvar))
    print(prop.table(table(depvar, indvar), 2))
    plot(depvar, indvar, xlab=DV, ylab=IV)
    print(summary(glm(formula, data = data, family="binomial")))
  } else if (class(depvar)=="factor" & (class(indvar)=="integer" | class(indvar)=="numeric")) {
    print(paste("Sample size for IV =", length(indvar)))
    print(summary(indvar))
    print(aggregate(indvar~depvar,data=data, mean, na.rm=T))
    boxplot(indvar~depvar, data=data, xlab=DV, ylab=IV)
    
    print(summary(glm(formula = formula, data = data, family="binomial")))
  } else if ((class(depvar)=="integer" | class(depvar)=="numeric") & class(indvar)=="factor") {
    print(table(indvar))
    print(aggregate(depvar~indvar,data=data, mean, na.rm=T))
    boxplot(depvar~indvar,data=data, xlab=DV, ylab=IV)
    print(summary(glm(formula = formula, data = data, family="gaussian")))
  } else if ((class(depvar)=="integer" | class(depvar)=="numeric") & (class(indvar)=="integer" | class(indvar)=="numeric")) {  
    print(paste("Sample size for IV =", length(indvar)))
    print(summary(indvar))
    lm_results <- lm(formula = formula, data = data)
    with(data,plot(depvar, indvar))
    abline(lm_results)
    print(summary(lm_results))
  } else {
    print("NO OUTPUT")
  }
}

#--------------------------------------------------------------------------
# Modeling function
#--------------------------------------------------------------------------

hlm_func <- function (formula, data, family = "binomial", priors) {
  print ("HYPOTHESIS TEST")
  options(mc.cores = parallel::detectCores())
  nIters <- 2000
  if (family == "binomial"){
    freq_model <- glmer(formula, data = data, family = binomial, na.action = na.exclude)
    bayes_model<- stan_glmer(formula,data=data, family = binomial(link = "logit"),
                             prior = priors,
                             prior_intercept = cauchy(0, 2.5),
                             chains = 4, iter = nIters,
                             seed = 12345, refresh = 1000)
  } else {
    freq_model <- lmer(formula, data = data, na.action = na.exclude)
    bayes_model<- stan_glmer(formula,data=data, family = gaussian(link = "identity"),
                             prior = priors,
                             prior_intercept = cauchy(0, 2.5),
                             chains = 4, iter = nIters,
                             seed = 12345, refresh = 1000)
  }
  print(summary(freq_model))
  print(summary(bayes_model,pars = c("beta"), probs = c(0.025, 0.1, 0.5, 0.9, 0.975), digits = 2)) 
  print(plot(bayes_model, "areas", pars = c("beta"), prob = 0.95, prob_outer = 0.99)+
          geom_vline(xintercept = 0, linetype = "dashed")) +
    ggtitle("Posterior distribution of IV effects", "with medians and 95% intervals")
  print(plot(bayes_model, "trace", pars = c("beta")))
  return (list(bayes_model, freq_model))
}

vague_priors <- normal(location = 0, scale = 2.5) # Use weakly informative priors for exploratory purposes

#--------------------------------------------------------------------------
# Model plotting function
#--------------------------------------------------------------------------

hlm_plots <- function (model, data, type, group="device") {
  if (type == "re") {
    print (plot_model(model, type = "re"))
    }
  if (type == "int") {
    print (plot_model(model, type = "int"))
    print (plot_model(model, terms=c("event_ID_2", "member_id"), type = "re"))
    }
  data2 <- mutate(data, fv2 = predict(model))
  re <- ranef(model)$member_id
  b <- fixef(model)
  map <- data2$member_id
  ggplot(data2, aes(event_ID_2, fv2, group=member_id, color=data2[,group])) + geom_line()
}

#--------------------------------------------------------------------------
# Variable selection function
#--------------------------------------------------------------------------

rf_eda <- function (outcome, predictors, dataset) {
  variables <- c(predictors, outcome)
  rf_data <- dataset[variables]
  rf_data <- rf_data[complete.cases(rf_data),]
  print(paste("Complete cases:", length(rf_data$training)))
  formula <- as.formula(paste(outcome, "~."))
  
  print("randomForest Importance")
  fittedRF <- randomForest(formula, rf_data, ntree=10)
  print(varImpPlot(fittedRF))
  
  #print("VSURF Importance")
  #games.vsurf <- VSURF(formula, data=dataset[variables], ntree=10, mtry = 100, verbose = F)
  #plot(games.vsurf, step = "thres", imp.sd = F, var.names = T)
  #print(colnames(rf_data[games.vsurf$varselect.thres]))
  
  print("Les Importance")
  rf_bld_1 <- ranger::ranger(formula, data = rf_data, importance = 'impurity_corrected')
  print(rf_bld_1)
  les_importance <- ranger::importance(rf_bld_1) %>%
    enframe("Variable", "Importance") %>%
    mutate(Variable = fct_reorder(Variable, Importance),
           New = Variable  %in% setdiff(names(rf_data), names(rf_data)))  %>%
    arrange(desc(Importance)) %>% 
    dplyr::slice(1:10) 
  print(les_importance)
  ggplot(aes(x = Variable, y = Importance), data=as.data.frame(les_importance)) + geom_col() + coord_flip() + labs(title = "Variable Importance")
}

#' #Game-level correlations

corrgram(games[, grepl("_std", names(games))], 
         lower.panel=panel.cor,
         upper.panel=panel.pie)

#' #Variable selection by outcome - Victim Strategies
#--------------------------------------------------------------------------
# Variable selection by outcome - Victim Strategies
#--------------------------------------------------------------------------

#' ##1.   "Prioritized strategy" predictions
# 1.1. Predictions for full dataset

#non_missing_game_vars <- colnames(games)[colSums(is.na(games)) == 0]
games_original_vic_vars  <- c('complexity',
                              'training',
                              'original_nav_strategy',
                              'trial_order',
                              'sat_tendency_std',
                              'spatial_ability_std',
                              'videogame_experience_std',
                              'competency_score_std',
                              'empty_max_trial_prev_std',
                              'not_empty_max_trial_prev_std')

rf_eda(outcome = "original_vic_strat_yellow", predictors = games_original_vic_vars, dataset = games)
rf_eda(outcome = "original_vic_strat_seq", predictors = games_original_vic_vars, dataset = games)

### Navigation strategy and competency strong predictors of prioritized victim strategy.

exp_func (DV="original_vic_strat_yellow", IV="competency_score_std", data=games)
exp_func (DV="original_vic_strat_seq", IV="competency_score_std", data=games)

ggplot(games, aes(original_victim_strategy, ..count..)) +  
  geom_bar(aes(fill=original_nav_strategy), position="stack") + 
  ggtitle("Original Victim Strategy by Original Navigation Strategy") 

ggplot(games, aes(x=competency_score_std, fill=factor(original_victim_strategy))) +  
  geom_density(position="identity") + 
  ggtitle("Competency scores by Original Victim Strategy") 

ggplot(games, aes(x=competency_score_std, fill=factor(original_nav_strategy))) +  
  geom_density(position="identity") + 
  facet_wrap(~original_victim_strategy, ncol=3) + 
  ggtitle("Competency scores x Original Victim Strategy x Original Navigation Strategy") 

### Navigation strategy and spatial ability strong predictors of sequential victim strategy. 
### Spatial ability possibly playing same role as competency score to pick out the "mixed"

ggplot(games, aes(x=spatial_ability_std, fill=factor(original_vic_strat_seq))) +  
  geom_density(position="identity") + 
  facet_wrap(~original_nav_strategy, ncol=3) + 
  ggtitle("Spatial ability x Original Victim Strategy x Original Navigation Strategy") 

# 1.2. Predictions for second and third trial, including information from prior trials. 

games_original_vic_vars2  <- c(games_original_vic_vars,
                              'vic_strat_yel_prev_most_time',
                              'vic_strat_yel_prev_original',
                              'vic_strat_seq_prev_most_time',
                              'nav_strat_seq_prev_most_time',
                              'nav_strat_seq_prev_original',
                              'nav_strat_yel_prev_most_time')

rf_eda(outcome = "original_vic_strat_yellow", predictors = games_original_vic_vars2, dataset = games)
rf_eda(outcome = "original_vic_strat_seq", predictors = games_original_vic_vars2, dataset = games)

### Nothing special beyond the confirmed prediction that prior strategy use is strongly related to current strategy prioritization. 

#' ##2. "Execute strategy" predictions

games_most_time_vars  <- c(games_original_vic_vars,
                           'original_victim_strategy', 
                           'original_nav_strategy')

rf_eda(outcome = "most_time_vic_strat_yellow", predictors = games_most_time_vars, dataset = games)
rf_eda(outcome = "most_time_vic_strat_seq", predictors = games_most_time_vars, dataset = games)
rf_eda(outcome = "victim_strategy_data.Sequential.time_spent", predictors = games_most_time_vars, dataset = games)
rf_eda(outcome = "victim_strategy_data.Yellow.First.time_spent", predictors = games_most_time_vars, dataset = games)

# Spatial ability, competency and experience add predictive power to original victim strategy

ggplot(games, aes(most_time_vic_strat, ..count..)) +  
  geom_bar(aes(fill=original_victim_strategy), position="stack") + 
  ggtitle("Executed victim strategy and self-reported prioritized strategy") 

ggplot(games, aes(x=spatial_ability_std, fill=most_time_vic_strat_seq)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Spatial ability and Executed victim strategy") 

ggplot(games, aes(x=videogame_experience_std, fill=most_time_vic_strat)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Videogaming Experience and Executed victim strategy") 

ggplot(games, aes(x=competency_score_std, fill=most_time_vic_strat)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Minecraft Competency and Executed victim strategy") 

ggplot(games, aes(x=spatial_ability_std, fill=factor(original_victim_strategy))) +  
  geom_density(position="identity") + 
  facet_wrap(~most_time_vic_strat, ncol=3) + 
  ggtitle("Competency scores x Original Victim Strategy x Original Navigation Strategy") 


#' ##3. "Workload" predictions

games_workload_vars  <- c(games_original_vic_vars,
                          'navigation_strategy_data.Sequential.time_spent',
                          'navigation_strategy_data.Sequential.score',
                          'navigation_strategy_data.Sequential.points_per_minute',
                          'most_time_nav_strat',
                          'most_time_nav_strat_seq',
                          'most_time_nav_strat_yel',
                          'empty_max_trial_std',
                          'not_empty_max_trial_std',
                          'rooms_entered_empty',
                          'rooms_entered_not_empty_std',
                          'left_behind_yellow',
                          'left_behind_yellow_max_std',
                          'left_behind_yellow_cat', 
                          'most_points_nav_strat',
                          "most_time_vic_strat_yellow", 
                          "most_time_vic_strat_seq")

rf_eda(outcome = "workload_std", predictors = games_workload_vars, dataset = games)

games$sat_tendency_std_cut <- cut(games$sat_tendency_std,breaks=c(-2, -1, 0, 1, 2))
ggplot(data=subset(games, !is.na(sat_tendency_std_cut)), 
       aes(x=factor(sat_tendency_std_cut), y=workload_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Average workload and satisficing tendency")

ggplot(games, aes(x=workload_std, y=sat_tendency_std)) +
  geom_point(size=2, shape=23)+
  stat_smooth(aes(x=workload_std, y=sat_tendency_std), method = lm, se = T) +
  ggtitle ("Self-reported workload by satisficing tendency")

ggplot(games, aes(x=factor(training), y=workload_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Average workload and training condition")

ggplot(data=subset(games, most_time_vic_strat !="Green.First"), 
                   aes(x=factor(most_time_vic_strat), y=workload_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Average workload and executed victim strategy")

#' ##4. "Current Utility" predictions

games_utility_vars  <- c(games_workload_vars, 
                          "workload_std")

rf_eda(outcome = "final_score_std", predictors = games_utility_vars, dataset = games)

ggplot(games, aes(x=final_score_std, y=navigation_strategy_data.Sequential.points_per_minute)) +
  geom_point(size=2, shape=23)+
  stat_smooth(aes(x=final_score_std, y=navigation_strategy_data.Sequential.points_per_minute), method = lm, se = T) +
  ggtitle ("Final Score by points per minute while using a sequential navigation strategy")

ggplot(games, aes(x=final_score_std, y=rooms_entered_not_empty_std)) +
  geom_point(size=2, shape=23)+
  stat_smooth(aes(x=final_score_std, y=rooms_entered_not_empty_std), method = lm, se = T) +
  ggtitle ("Final Score by non-empty rooms entered")

ggplot(games, aes(x=most_time_nav_strat, y=final_score_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Average score by most frequently used navigation strategy")

ggplot(subset(games, most_time_vic_strat!="Green.First"), 
              aes(x=most_time_vic_strat, y=final_score_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Average score by most frequently used victim strategy")


#' ##5. "Update Strategy" predictions

victims_first_half <- subset (victims, seconds_remaining >=300)

victims_update_vars  <- c("next_victim_distance",
                          "complexity",
                          "trial_order",
                          "training",
                          "tradeoff",
                          "device",
                          "five_minutes",
                          "total_yellow_victims_remaining_std",
                          "all_yellow_rescued",
                          "yellow_per_minute_std",
                          "green_per_minute_std",
                          "sat_tendency_std", 
                          "seconds_remaining_std")
victims_update_vars2  <- c(victims_update_vars,
                          "victim_strategy_prev",
                          "green_search_time_std",
                          "yellow_search_time_std",
                          "spare_time_yellows_std")

# 5.1. Predictions for full dataset

rf_eda(outcome = "vic_strat_yellow", predictors = victims_update_vars, dataset = victims_first_half)
rf_eda(outcome = "victim_strategy_update", predictors = victims_update_vars, dataset = victims_first_half)

victims_first_half_notna <- subset(victims_first_half, !is.na(victim_strategy_update))

ggplot(victims_first_half_notna, aes(x=green_per_minute_std, fill=victim_strategy_update)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Probability of victim strategy update by rescue rates") 

ggplot(victims_first_half_notna, aes(x=yellow_per_minute_std, fill=victim_strategy_update)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Probability of victim strategy update by yellow rate") 

ggplot(victims_first_half_notna, aes(x=seconds_remaining, fill=victim_strategy_update)) +  
  geom_density(position="identity", alpha = 0.4) + 
  ggtitle("Probability of victim strategy update by seconds remaining") 

# 5.2. Predictions for partial dataset

rf_eda(outcome = "vic_strat_yellow", predictors = victims_update_vars2, dataset = victims_first_half)
rf_eda(outcome = "victim_strategy_update", predictors = victims_update_vars2, dataset = victims_first_half)

victims_first_half_notna$victim_strategy_update_num <- 
  ifelse(victims_first_half_notna$victim_strategy_update=="Update", 1, 0)
ggplot(victims_first_half_notna, aes(x=victim_strategy_prev, y=victim_strategy_update_num)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Probability of victim strategy update by victim strategy used in previous trial")

#' #Variable selection by outcome - Navigation Strategies
#--------------------------------------------------------------------------
# Variable selection by outcome - Navigation Strategies
#--------------------------------------------------------------------------

#' ##1. "Prioritized strategy" predictions
# 1.1. Predictions for full dataset

games_original_nav_vars  <- c('complexity',
                              'training',
                              'original_victim_strategy',
                              'trial_order',
                              'sat_tendency_std',
                              'spatial_ability_std',
                              'videogame_experience_std',
                              'competency_score_std',
                              'empty_max_trial_prev_std',
                              'not_empty_max_trial_prev_std')

rf_eda(outcome = "original_nav_strat_yellow", predictors = games_original_nav_vars, dataset = games)
rf_eda(outcome = "original_nav_strat_seq", predictors = games_original_nav_vars, dataset = games)

ggplot(games, aes(original_nav_strategy, ..count..)) +  
  geom_bar(aes(fill=training), position="stack") + 
  ggtitle("Original Navigation Strategy by training condition") 

ggplot(games, aes(original_nav_strategy, ..count..)) +  
  geom_bar(aes(fill=original_victim_strategy), position="stack") + 
  ggtitle("Original Navigation Strategy by Original Victim Strategy") 

ggplot(games, aes(x=sat_tendency_std, fill=factor(original_nav_strategy))) +  
  geom_density(position="identity") + 
  ggtitle("Satisficing tendency scores by Original Navigation Strategy") 

#' ##2. "Execute strategy" predictions
# 2.1. Predictions for full dataset

games_most_time_vars  <- c(games_original_nav_vars,
                           'original_nav_strategy')

rf_eda(outcome = "most_time_nav_strat_yel", predictors = games_most_time_vars, dataset = games)
rf_eda(outcome = "most_time_nav_strat_seq", predictors = games_most_time_vars, dataset = games)

ggplot(games, aes(most_time_nav_strat, ..count..)) +  
  geom_bar(aes(fill=training), position="stack") + 
  ggtitle("Executed Navigation Strategy by training condition") 

ggplot(games, aes(x=competency_score_std, fill=factor(most_time_nav_strat))) +  
  geom_density(position="identity") + 
  ggtitle("Competency scores by Executed Navigation Strategy") 

ggplot(games, aes(x=most_time_nav_strat, y=empty_max_trial_prev_std)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Executed strategy by number of empty rooms entered in previous trial")

#' ##3. "Update strategy" predictions
# 3.1. Predictions for full dataset

rooms_update_vars  <- c("yellow_victims_in_current_room",
                           "green_victims_in_current_room",
                           "nav_strategy",
                           "room_type",
                           "rooms_entered_empty",
                           "rooms_entered_not_empty",
                           "prior_use_consistent",
                           "prior_use_inconsistent",
                           "openings_seen",
                           "complexity",
                           "trial_order",
                           "training",
                           "tradeoff",
                           "device",
                           "seconds_remaining_std",
                           "five_minutes",
                           "event_ID_2",
                           "rooms_entered_empty_running",
                           "rooms_entered_not_empty_running",
                           "rooms_entered_empty_std",
                           "rooms_entered_not_empty_std")

rf_eda(outcome = "nav_strategy_update", predictors = rooms_update_vars, dataset = rooms_first_half)

rooms_first_half$nav_strategy_update_num <- 
  ifelse(rooms_first_half$nav_strategy_update=="Update", 1, 0)

ggplot(rooms_first_half, aes(x=nav_strategy, y=nav_strategy_update_num)) + 
  stat_summary(fun="mean", geom="bar") +
  stat_summary(fun.data = mean_se, geom = "errorbar", width=0.3, size = 1.5) +
  ggtitle ("Probability of Navigation strategy update by current navigation strategy")

rooms_first_half_notna <- subset(rooms_first_half, !is.na(nav_strategy_update))
ggplot(rooms_first_half_notna, aes(x=prior_use_consistent, fill=factor(nav_strategy_update))) +  
  geom_density(position="identity", alpha=0.5) + 
  ggtitle("Consistent use of device by Executed Navigation Strategy") 

ggplot(rooms_first_half_notna, aes(x=prior_use_inconsistent, fill=factor(nav_strategy_update))) +  
  geom_density(position="identity", alpha=0.5) + 
  ggtitle("Inconsistent use of device by Executed Navigation Strategy") 

# 3.1. Predictions for partial dataset

rooms_update_vars2 <- c(rooms_update_vars, 
                        "exited_room_type",
                        "left_behind_yellow",
                        "left_behind_green",
                        "navigation_strategy_prev", 
                        'victim_strategy_data.Sequential.time_spent',
                        'victim_strategy_data.Sequential.score',
                        'victim_strategy_data.Sequential.points_per_minute',
                        'prior_use_consistent_std')

rf_eda(outcome = "nav_strategy_update", predictors = rooms_update_vars, dataset = rooms_first_half)

#' ##4. Learning Functions - Device Use
#--------------------------------------------------------------------------
# 4. Learning Functions - Device Use
#--------------------------------------------------------------------------

# 4.1. Exposure to positive and negative incentives following device beeps will increase the probability of learning the device (per post-strategy survey).  
# Explore learning as a growth curve model
# Differences between device training and no device training groups

std.error <- function(x) sqrt(var(x)/length(x))
time_series <- rooms %>% group_by(device, event_ID) %>% 
  summarise(empty_mean = mean(rooms_entered_empty),
            empty_lower = mean(rooms_entered_empty)-2*(std.error(rooms_entered_empty)), 
            empty_upper = mean(rooms_entered_empty)+2*(std.error(rooms_entered_empty)), 
            consistent_use_mean = mean(prior_use_consistent),
            consistent_use_lower = mean(prior_use_consistent)-2*(std.error(prior_use_consistent)), 
            consistent_use_upper = mean(prior_use_consistent)+2*(std.error(prior_use_consistent)))

ggplot(data=time_series, aes(x = event_ID, y = empty_mean, colour=device)) + geom_line() +
  geom_ribbon(aes(ymin=time_series$empty_lower, ymax=time_series$empty_upper), linetype=2, alpha=0.1)

ggplot(data=time_series, aes(x = event_ID, y = consistent_use_mean, colour=device)) + geom_line() +
  geom_ribbon(aes(ymin=time_series$consistent_use_lower, ymax=time_series$consistent_use_upper), 
              linetype=2, alpha=0.1)

# Variation among "no device" group, who are the learners

rooms_nodevice <- subset (rooms, device == "NoDevice")
table(rooms_nodevice$rooms_entered_empty_running)

ggplot(rooms_nodevice, aes(x=event_ID_2, y=rooms_entered_empty, group=trial_id)) + 
  geom_line()

ggplot(rooms_nodevice, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=trial_order))

ggplot(rooms, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=trial_order))

ggplot(rooms, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=device))

# Individual differences in curves

#trellis.device(color=T)
xyplot(rooms_entered_empty_running ~ event_ID_2 | member_id, data=rooms, 
       main="Emtpy Rooms Entered", 
       panel=function(x, y) {
         panel.xyplot(x, y)
         panel.lmline(x, y, lty=4)
       })

# Since all start at 0, a random slope model should account for all differences
# Growth curve modelling
# Random intercepts model

rooms$member_id <- as.factor(rooms$member_id)
ri_form <- as.formula (rooms_entered_empty_running ~ event_ID_2 + (1 | member_id))
ri_mod <- hlm_func(formula= ri_form, data = rooms, family="gaussian", priors = vague_priors)
hlm_plots (ri_mod[[2]], rooms, "re")

# Random intercepts and slopes model

ris_form <- as.formula (rooms_entered_empty_running ~ event_ID_2 + (event_ID_2|member_id))
ris_mod <- hlm_func(formula= ris_form, data = rooms, family="gaussian", priors = vague_priors)
hlm_plots (ris_mod[[2]], rooms, "re")

# Random intercepts + slopes + interaction model

risi_form <- as.formula (rooms_entered_empty_running ~ event_ID_2*device + (event_ID_2|member_id))
risi_model <- hlm_func(formula= risi_form, data=rooms, family="gaussian", priors = vague_priors)
hlm_plots (risi_model[[2]], rooms, "int")
# Running into convergence issues, plus random intercepts not really necessary

# Random slopes + interaction model

rsi_form <- as.formula (rooms_entered_empty_running ~ event_ID_2*device + (0+event_ID_2|member_id))
rsi_model <- hlm_func(formula= rsi_form, data=rooms, family="gaussian", priors = vague_priors)
hlm_plots (rsi_model[[2]], rooms, "int")

# Random slopes + interactions model (add minecraft competency)

competency <- subset (games, select = c(competency_score_std, 
                                        videogame_experience_std, 
                                        original_nav_strategy,
                                        trial_id))

rooms <- merge (rooms, competency, by=c("trial_id"), all.x = TRUE)
rsi2_form <- as.formula (rooms_entered_empty_running ~ 
                          event_ID_2*device*competency_score_std + 
                          (0+event_ID_2|member_id))
rsi2_model <- hlm_func(formula= rsi2_form, data=rooms, family="gaussian", priors = vague_priors)
hlm_plots (rsi2_model[[2]], rooms, "int")

# Competency amplifies the effect of device training.
# At low competency levels, device training generates a small advantage on empty rooms. 
# At high competency levels, device training generates a large advantage on empty rooms.

rsi3_form <- as.formula (rooms_entered_empty_running ~ 
                           event_ID_2*device*competency_score_std*videogame_experience_std + 
                           (0+event_ID_2|member_id))
rsi3_model <- hlm_func(formula= rsi3_form, data=rooms, family="gaussian", priors = vague_priors)
hlm_plots (rsi3_model[[2]], rooms, "int")

# Look at no device group only to pinpoint their learning point

rooms_nodevice <- subset (rooms, device=="NoDevice")
rsi4_form <- as.formula (rooms_entered_empty_running ~ 
                           event_ID_2*competency_score_std*videogame_experience_std + 
                           (0+event_ID_2|member_id))
rsi4_model <- hlm_func(formula= rsi4_form, data=rooms_nodevice, family="gaussian", priors = vague_priors)
hlm_plots (rsi4_model[[2]], rooms_nodevice, "int")

# Split by whether participants indicate they plan to use device

table(games$next_nav_strat_yelempt, games$device)
next_nav_strat_yelempt <- subset (games, select = c(next_nav_strat_yelempt, trial_id))

rooms <- merge(rooms, next_nav_strat_yelempt, by=c("trial_id"), all.x = TRUE)
rooms_nodevice_next_strat <- subset (rooms, device=="NoDevice" & !is.na(next_nav_strat_yelempt))
rooms_nodevice_yelempt <- subset(rooms_nodevice_next_strat, next_nav_strat_yelempt !="Other")
rooms_nodevice_other <- subset(rooms_nodevice_next_strat, next_nav_strat_yelempt =="Other")

#trellis.device(color=T)
xyplot(rooms_entered_empty_running ~ event_ID_2 | member_id, data=rooms_nodevice_yelempt, 
       main="Emtpy Rooms Entered", 
       panel=function(x, y) {
         panel.xyplot(x, y)
         panel.lmline(x, y, lty=4)
       })

#trellis.device(color=T)
xyplot(rooms_entered_empty_running ~ event_ID_2 | member_id, data=rooms_nodevice_other, 
       main="Emtpy Rooms Entered", 
       panel=function(x, y) {
         panel.xyplot(x, y)
         panel.lmline(x, y, lty=4)
       })

# Plot progression of learners vs rest in nodevice group
learners <- unique(rooms_nodevice_yelempt$member_id)
rooms_nodevice$learners <- ifelse(rooms_nodevice$member_id %in% learners, "Learner", "Not Learner")
rooms_nodevice_learners <- subset(rooms_nodevice, learners =="Learner")

ggplot(rooms_nodevice_learners, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=learners))
ggplot(rooms_nodevice, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=learners))

risi_form <- as.formula (rooms_entered_empty_running ~ event_ID_2*learners + (0+event_ID_2|member_id))
risi_model <- hlm_func(formula= risi_form, data=rooms_nodevice, family="gaussian", priors = vague_priors)
hlm_plots (risi_model[[2]], rooms_nodevice, "int")

# Explore differences by quarters

ggplot(rooms, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=quarters))

ggplot(rooms_nodevice, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=quarters))

ggplot(rooms_nodevice_learners, aes(x=event_ID_2, y=rooms_entered_empty_running, group=trial_id)) + 
  geom_line(aes(color=quarters))

rsi_form <- as.formula (rooms_entered_empty_running ~ event_ID_2 + quarters*device + (0+event_ID_2|member_id))
rsi_model <- hlm_func(formula= rsi_form, data=rooms, family="gaussian", priors = vague_priors)
hlm_plots (rsi_model[[2]], rooms, "int")

#' #4. Utility: Rational Agent vs. Human

# Calculate total victims seen by adding victims saved and left_behind during the first half

victims_saved <- as.data.frame(table(victims_first_half$trial_id, 
                                     victims_first_half$victim_color))

# table(victims_saved$Freq, victims_saved$Var2)

sorted_rooms <- subset(rooms_first_half, select=c(trial_id, room_id, event_index_number, left_behind_yellow, left_behind_green))
sorted_rooms <- sorted_rooms[with(sorted_rooms, order(trial_id, event_index_number)), ]
sorted_rooms <- sorted_rooms %>% group_by(trial_id) %>% mutate(index = row_number())

sorted_rooms_prev <- subset (sorted_rooms, select =-c(room_id, event_index_number))
sorted_rooms_prev$index <- sorted_rooms_prev$index-1
sorted_rooms <- subset (sorted_rooms, select =-c(left_behind_yellow, left_behind_green))
sorted_rooms <- merge (sorted_rooms, sorted_rooms_prev, by=c("trial_id", "index"), all.x = TRUE)
left_behind_room <- aggregate(cbind(left_behind_yellow, left_behind_green) ~ trial_id + room_id, 
                              sorted_rooms, min)
left_behind_trial <- aggregate(cbind(left_behind_yellow, left_behind_green) ~ trial_id, 
                               left_behind_room, sum)
#summary(left_behind_trial) 
left_behind_trial$left_behind_yellow[left_behind_trial$left_behind_yellow==-1] <- 0 # Three negative yellow victims due to processing errors. Fix manually. 

yellow_triaged <- subset(victims_saved, Var2=="Yellow", select = c(Var1, Freq))
green_triaged <- subset(victims_saved, Var2=="Green", select = c(Var1, Freq))
colnames(green_triaged) <- c("trial_id", "green_triaged")
colnames(yellow_triaged) <- c("trial_id", "yellow_triaged")
triaged_trial <- merge (green_triaged, yellow_triaged, by=c("trial_id"), 
                        all.x = TRUE, all.y = TRUE)
probs_trial <- merge (triaged_trial, left_behind_trial, by=c("trial_id"), 
                        all.x = TRUE, all.y = TRUE)

probs_trial$total_seen_green <- probs_trial$left_behind_green + probs_trial$green_triaged 
probs_trial$total_seen_yellow <- probs_trial$left_behind_yellow + probs_trial$yellow_triaged 

hist(probs_trial$total_seen_green) # As expected, positively skewed, with max of 24
hist(probs_trial$total_seen_yellow) # As expected, negatively skewed, with max of 10

probs_trial$prob_yellow <- probs_trial$yellow_triaged/probs_trial$total_seen_yellow
probs_trial$prob_green <- probs_trial$green_triaged/probs_trial$total_seen_green
#summary(probs_trial)
hist(probs_trial$prob_yellow)
hist(probs_trial$prob_green)

### Merge Search times (earlier approach, inaccurate, calculate search times directly)
# search_times <- subset (victims_first_half, 
#                        select = c(trial_id, 
#                                   green_search_time, 
#                                   yellow_search_time, 
#                                   event_index_number))

#search_times <- search_times %>% group_by(trial_id) %>%
#  mutate(max_event = max(as.numeric(event_index_number)))
#search_times <- subset(search_times, event_index_number==max_event, 
#                       select=-c(event_index_number, max_event))

#probs_search_trial <- merge (probs_trial, search_times, by=c("trial_id"), 
#                      all.x = TRUE, all.y = TRUE)

### Calculate search times directly from number seen
# Victims seen
#total_victims_seen <- probs_search_trial$total_seen_yellow + probs_search_trial$total_seen_green
yellow_seen <- probs_trial$total_seen_yellow
green_seen <- probs_trial$total_seen_green

# Subtract triage times from search times
# Calculate total triaging time for greens and yellows. 

# Total time triaging victims
# Subtract one triaging event from each list, as we assume the last triaged victim event is not added to the average search time, which is calculated at the time of seeing the victim.
total_triaging_time <- ((probs_trial$yellow_triaged-1)*15)+((probs_trial$green_triaged-1)*7.5)

# Total time searching for victims (includes time triaging victims)  (Earlier approach, inaccurate)
#total_search_time <- (probs_search_trial$yellow_search_time*probs_search_trial$total_seen_yellow) +
#                     (probs_search_trial$green_search_time*probs_search_trial$total_seen_green)
#yellow_search_time <- (probs_search_trial$yellow_search_time*yellow_seen)
#green_search_time <- (probs_search_trial$green_search_time*green_seen)

# Average search times after removing time triaging victims  (Earlier approach, inaccurate)
#total_search_time_minus_triage_time <- total_search_time-total_triaging_time
#probs_search_trial$yellow_search_time2 <- (yellow_search_time-total_triaging_time)/yellow_seen
#probs_search_trial$green_search_time2 <- (green_search_time-total_triaging_time)/green_seen

probs_trial$yellow_search_time2 <- (300-total_triaging_time)/yellow_seen
probs_trial$green_search_time2 <- (300-total_triaging_time)/green_seen

hist(probs_trial$yellow_search_time2)
summary(probs_trial$yellow_search_time2)
hist(probs_trial$green_search_time2)
summary(probs_trial$green_search_time2)

# Merge into "games" dataset

games <- merge (probs_trial, games, by=c("trial_id"), all.x=T, all.y=T)

# Plot probabilities

ggplot(games, aes(x=final_score, y=prob_yellow)) +
  geom_point(size=2, shape=23)+
  stat_smooth(aes(x=final_score, y=prob_yellow), method = lm, se = T) +
  ggtitle ("Score by prob. of rescuing yellow victims in FoV (First Half)")

ggplot(probs_trial, aes(x=prob_yellow, y=prob_green)) +
  geom_point(size=2, shape=23) + 
  xlim(0.5,1) + ylim (0, 1) + 
  ggtitle ("Probability of rescuing yellow victims in FoV (First Half)")

# Plot utility curves

ggplot(probs_trial, aes(x=yellow_search_time2, y=prob_green)) +
  geom_point(size=2, shape=23) + 
  xlim(15,80) + ylim (0, 1) +
  stat_smooth(aes(x=yellow_search_time2, y=prob_green), method = lm, 
             formula = y ~ poly(x, 2), se = T) +
  ggtitle ("Probability of rescuing green victims in FoV (First Half) by yellow search time")

ggplot(games, aes(x=final_score, y=prob_green)) +
  geom_point(size=2, shape=23)+
  stat_smooth(aes(x=final_score, y=prob_yellow), method = lm, 
              formula = y ~ x, se = T) +
  ggtitle ("Score by prob. of rescuing green victims in FoV (First Half)")

# Summarize to compare with predictions by discretizing search times

probs_trial$yellow_search_time_10<-case_when(
  (probs_trial$yellow_search_time2>=20 & probs_trial$yellow_search_time2<30)~20,
  (probs_trial$yellow_search_time2>=30 & probs_trial$yellow_search_time2<40)~30,
  (probs_trial$yellow_search_time2>=40 & probs_trial$yellow_search_time2<50)~40,
  (probs_trial$yellow_search_time2>=50 & probs_trial$yellow_search_time2<60)~50)

probs_trial$green_search_time_10<-case_when(
  (probs_trial$green_search_time2>=10 & probs_trial$green_search_time2<30)~10,
  (probs_trial$green_search_time2>=20 & probs_trial$green_search_time2<30)~20,
  (probs_trial$green_search_time2>=30 & probs_trial$green_search_time2<40)~30,
  (probs_trial$green_search_time2>=40 & probs_trial$green_search_time2<50)~40)

# probs_trial$yellow_search_time_10 <- cut(probs_trial$yellow_search_time2, breaks=yellow_breaks, labels = F) # Stopped using cut as dealing with labels was difficult
#probs_trial$green_search_time_10 <- cut(probs_trial$green_search_time2, breaks=green_breaks)  # Stopped using cut as dealing with labels was difficult

optim1 <- aggregate(prob_green~green_search_time_10+yellow_search_time_10, data=probs_trial, mean, na.rm=T)

# 5 second intervals looking choppy
# probs_trial$yellow_search_time_5 <- cut(probs_trial$yellow_search_time2, breaks=seq(15, 60, 5))
# probs_trial$green_search_time_5 <- cut(probs_trial$green_search_time2, breaks=seq(10, 40, 5))

# Rational Agent

yellow_breaks <- seq(0, 60, 10)
green_breaks <- seq(0, 60, 10)
optim2 <- read.csv("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Analytics/Phase_1/optim_green.csv")
optim2 <- optim2[which(optim2$py==1), ]
#optim2$yellow_search_time_10 <- cut(optim2$search_y, breaks=yellow_breaks, labels = F)
#optim2$green_search_time_10 <- cut(optim2$search_g1, breaks=green_breaks, labels = F)
optim2 <- aggregate(optim_pg1~search_g1+search_y, data=optim2, mean, na.rm=T)
colnames(optim2)<- c("yellow_search_time", 
                     "green_search_time",
                     "prob_green")

p <- plot_ly(data = optim1,  
            x=optim1$yellow_search_time_10, 
            y=optim1$green_search_time_10, 
            z=optim1$prob_green, 
            type="mesh3d")
p <- add_trace(p, data = optim2,  
            x=optim2$yellow_search_time, 
            y=optim2$green_search_time, 
            z=optim2$prob_green, 
            type="mesh3d")
p <- layout(p, title = "Search times and green probabilities during first half", 
         scene = list(
           xaxis = list(title = "Mean Yellow Search Time"),
           yaxis = list(title = "Mean Green Search Time"),
           zaxis = list(title = "Prob. of green")
         ))
p <- layout(p, 
  title = "Button Restyle",
  updatemenus = list(
    list(
      type = "buttons",
      y = 0.8,
      buttons = list(
        list(method = "restyle",
             args = list("visible", c(F,T)),
             label = "Rational Agent"),
        list(method = "restyle",
             args = list("visible", c(T,F)),
             label = "People in Exp1"),
        list(method = "restyle",
             args = list("visible", c(T,T)),
             label = "Both")))
  ))
p

htmlwidgets::saveWidget(p, "search_times.html")

z <- acast(optim1, yellow_search_time_10~green_search_time_10, value.var="prob_green")
persp(z, phi = 30, theta = -50,
      xlab = "Search time yellow", 
      ylab = "Search time green", 
      zlab = "Probability of green", 
      ticktype="detailed", col = "orange", shade=0.4)
plot(optim1$green_search_time_10, optim1$prob_green)
plot(optim1$yellow_search_time_10, optim1$prob_green)


ggplot(data = subset(probs_trial, yellow_search_time2<100), 
       aes(x=yellow_search_time2, 
           y=prob_green)) +
  geom_point() +
  geom_smooth(method = "glm", 
              method.args = list(family = "binomial"), 
              se = FALSE)

# Test effect on score of probabilities of yellow and green, adjusting for competency

formula_score <- as.formula (final_score_std ~
                               prob_green +
                               prob_yellow +
                               competency_score_std +
                               (1 | member_id))
model_score <- hlm_func(formula = formula_score, data = games, family="gaussian", priors = vague_priors)

