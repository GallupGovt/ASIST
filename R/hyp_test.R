#' ---
#' title: "ASIST - Gallup Experiment 1 Results"
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
pacman::p_load(rstatix, ggpubr, corrgram, lme4, lmerTest, dplyr, rstanarm, bayesplot)
games <- read.csv ("results_data_proc.csv")
events <- read.csv ("results_events_proc.csv")
victims <- read.csv ("results_victims_proc.csv")
rooms <- read.csv ("results_rooms_proc.csv")
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
# Hypothesis testing - modeling function
#--------------------------------------------------------------------------

# Assign priors based on adequate power to detect medium-sized effects (std. beta = 0.25, log odds = 0.9) 

MDES_l <- 0.9 # MDES in log odds, according to power analysis 
MDES_b <- 0.25 # MDES in standard betas, according to power analysis 

hlm_func <- function (formula, data, family = "binomial", priors) {
  print ("HYPOTHESIS TEST")
  options(mc.cores = parallel::detectCores())
  nIters <- 5000
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

#' #Hypothesis testing - Victim Strategies
#--------------------------------------------------------------------------
# Hypothesis testing - Victim Strategies
#--------------------------------------------------------------------------

#' ##1. "Prioritized strategy" predictions
# 1.1. Participants in the "trade-off" and "trade-off + device" training conditions will be more likely to mention "yellow-only" as their victim prioritization strategy in the pre-trial survey.
exp_func (DV="original_vic_strat_yellow", IV="tradeoff", data=games)
# 1.2. The amount of time a victim strategy has been used in the past will increase the likelihood that participants will mention that strategy in the pre-trial survey. 
#exp_func (DV="vic_strat_yel_prev_time", IV="original_vic_strat_yellow", data=games)
exp_func (DV="original_vic_strat_yellow", IV="vic_strat_yel_prev_most_time", data=games)
# 1.3. The average past benefit rate of a victim strategy will increase the likelihood that participants will mention that strategy in the pre-trial survey. 
#exp_func (DV="original_vic_strat_yellow", IV="vic_strat_yel_prev_rate", data=games)
exp_func (DV="original_vic_strat_yellow", IV="vic_strat_yel_prev_most_points", data=games)
# 1.4. Participants high in satisficing tendency will be less likely to mention "yellow-only" as their victim prioritization strategy in the pre-trial survey. 
exp_func (DV="original_vic_strat_yellow", IV="sat_tendency_std", data=games)
exp_func (DV="original_vic_strat_yellow", IV="sat_tendency_std2", data=games)
# 1.5. Participants with lower levels of spatial ability will be more likely to mention sequential search as their victim strategy in the pre-trial survey. 
exp_func (DV="original_vic_strat_yellow", IV="spatial_ability_std", data=games)
# 1.6. Participants with lower levels of videogaming experience will be more likely to mention sequential search as their victim strategy in the pre-trial survey. 
exp_func (DV="original_vic_strat_yellow", IV="videogame_experience_std", data=games)

# Test 1.1., 1.4., 1.5., 1.6. using largest available sample (not adjusting for prior strategy use)
# Outcome: Prioritize yellow-only strategy

v_formula_1_1 <- as.formula (original_vic_strat_yellow ~
                               tradeoff +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_1 <- cauchy(location = c(MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 4), 2.5, 2.5))
v_model_1_1 <- hlm_func(formula = v_formula_1_1, data = games, family="binomial", priors = priors1_1)

# Outcome: Prioritize Sequential strategy

v_formula_1_2 <- as.formula (original_vic_strat_seq ~
                               tradeoff +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_2 <- cauchy(location = c(MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 4), 2.5, 2.5))
v_model_1_2 <- hlm_func(formula= v_formula_1_2, data = games, family="binomial", priors = priors1_2)

# Testing 1.5. &  1.6.: adjusting for prior strategy use 
# Outcome: Prioritize Yellow-only strategy

v_formula_1_3 <- as.formula (original_vic_strat_yellow ~
                               tradeoff +
                               vic_strat_yel_prev_most_time +
                               vic_strat_yel_prev_most_points +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_3 <- cauchy(location = c(MDES_l, MDES_l, MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 6), 2.5, 2.5))
v_model_1_3 <- hlm_func(formula = v_formula_1_3, data = games, family="binomial", priors = priors1_3)

# Outcome: Prioritize sequential strategy

v_formula_1_4 <- as.formula (original_vic_strat_seq ~
                             tradeoff +
                             vic_strat_seq_prev_most_time +
                             vic_strat_seq_prev_most_points +
                             sat_tendency_std2 +
                             spatial_ability_std +
                             videogame_experience_std +
                             complexity +
                            (1 | member_id))
priors1_4 <- cauchy(location = c(MDES_l, MDES_l, MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 6), 2.5, 2.5))
v_model_1_4 <- hlm_func(formula= v_formula_1_4, data = games, family="binomial", priors = priors1_4)

#' ##2. "Execute strategy" predictions
# 2.1. Participants will be more likely to implement strategies mentioned in the pre-trial survey than other strategies. 
exp_func (DV="victim_strategy_data.Yellow.First.time_spent", IV="original_vic_strat_yellow", data=games)
exp_func (DV="most_time_vic_strat_yellow", IV="original_vic_strat_yellow", data=games)

# Outcome: Yellow-only strategy

v_formula_2_1 <- as.formula (most_time_vic_strat_yellow ~ 
                               original_vic_strat_yellow + 
                               training +
                               complexity +
                               (1 | member_id))
priors2_1 <- cauchy(location = c(MDES_l, 0, 0, 0, 0, 0), 
                                 scale = c(MDES_l/2, rep(2.5, 5)))
v_model_2_1 <- hlm_func(formula= v_formula_2_1, data = games, family="binomial", priors = priors2_1)

# Outcome: Sequential strategy

exp_func (DV="victim_strategy_data.Sequential.time_spent", IV="original_vic_strat_seq", data=games)
exp_func (DV="most_time_vic_strat_seq", IV="original_vic_strat_seq", data=games)

v_formula_2_2 <- as.formula (most_time_vic_strat_seq ~ 
                               original_vic_strat_seq + 
                               training +
                               complexity +
                               (1 | member_id))
priors2_2 <- cauchy(location = c(MDES_l, 0, 0, 0, 0, 0), 
                    scale = c(MDES_l/2, rep(2.5, 5)))
v_model_2_2 <- hlm_func(formula= v_formula_2_2, data = games, family="binomial", priors = priors2_1)

#' ##3. "Workload" predictions
# 3.1. Participants are more likely to experience high workload under higher mission complexity than lower mission complexity. 

exp_func (DV="workload", IV="complexity", data=games)

priors3_1 <- cauchy(location = c(MDES_b, MDES_b, 0, 0, 0), 
                    scale = c(MDES_b/2, MDES_b/2, rep(2.5, 3)))
v_formula_3_1 <- as.formula (workload ~ 
                             complexity + 
                             training + (1 | member_id))
v_model_3_1 <- hlm_func(formula= v_formula_3_1, data = games, family="gaussian", priors = priors3_1)

#' ##4. "Current Utility" predictions
# 4.1. Participants using a "yellow-only" or "mixed" strategy where Py = 1 will have a higher score than participants using a strategy where Py < 1. 
exp_func (DV="final_score_std", IV="left_behind_yellow_cat", data=games)
# 4.2. Participants with higher competency scores will have a higher score than participants with lower competency scores.
exp_func (DV="final_score_std", IV="competency_score_std", data=games)
# 4.3. Participants with higher spatial ability will have a higher score than participants with lower spatial ability. 
exp_func (DV="final_score_std", IV="spatial_ability_std", data=games)

v_formula_4_1 <- as.formula (final_score_std ~ 
                             left_behind_yellow_max_std +
                             competency_score_std +
                             spatial_ability_std +
                             complexity +
                             training +
                             (1 | member_id))
priors4_1 <- cauchy(location = c(rep(MDES_b, 3), rep(0, 5)), 
                    scale = c(rep(MDES_b/2, 3), rep(2.5, 5)))
v_model_4_1 <- hlm_func(formula= v_formula_4_1, data = games, family="gaussian", priors = priors4_1)

#' ##5. "Update Strategy" predictions
# 5.1 The probability of "yellow-only" victim strategy will decrease as average search times for victims decreases. 
exp_func (DV="vic_strat_yellow", IV="yellow_search_time_std", data=victims_first_half)
exp_func (DV="vic_strat_yellow", IV="green_search_time_std", data=victims_first_half)
# 5.2 The probability of "yellow-only" victim strategy will increase as the time remaining for the 5-minute mark approaches the product of the number of remaining yellow victims times the sum of their average search time and time to be rescued. 
exp_func (DV="vic_strat_yellow", IV="spare_time_yellows_std", data=victims_first_half)

v_formula_5_1 <- as.formula (vic_strat_yellow ~ 
                               yellow_search_time_std +
                               green_search_time_std +
                               spare_time_yellows_std + 
                               complexity +
                               training +
                               (1 | member_id))
priors5_1 <- cauchy(location = c(rep(MDES_l, 3), rep(0, 5)),
                    scale = c(rep(MDES_l/2, 3), rep(2.5, 5)))
v_model_5_1 <- hlm_func(formula= v_formula_5_1, data = victims_first_half, family="binomial", priors = priors5_1)

# 5.3 The probability of a victim strategy update will be greater for participants with lower current utility, as measured by the sum of their yellow rate, their green rate, and their expected green rate after 5 minutes. 
# 5.4 The probability of a victim strategy update among participants with lower current utility will increase as uncertainty about current utility decreases through learning.
# 5.5 Victim strategy updates will be more likely for participants high in optimizing tendency.
# 5.6 Victim strategy updates will be more likely after a participant has rescued all yellow victims or after the 5-minute mark (yellow victims decease).
exp_func (DV="vic_strat_yellow", IV="all_yellow_rescued", data=victims_first_half)

# Note that expected_green_rate_std is redundant due to perfect colinearity with green_per_minute_std, and so it is excluded

v_formula_5_2 <- as.formula (victim_strategy_update ~ 
                             yellow_per_minute_std +
                             green_per_minute_std +
                             seconds_remaining_std +
                             sat_tendency_std2 +
                             all_yellow_rescued +
                             five_minutes +
                             complexity +
                             training +
                             (1 | member_id))
priors5_2 <- cauchy(location = c(rep(MDES_l, 6), rep(0, 5)),
                    scale = c(rep(MDES_l/2, 6), rep(2.5, 5)))
v_model_5_2 <- hlm_func(formula= v_formula_5_2, data = victims_first_half, family="binomial", priors = priors5_2)

#' #Hypothesis testing - Navigation Strategies
#--------------------------------------------------------------------------
# Hypothesis testing - Navigation Strategies
#--------------------------------------------------------------------------

#' ##1. "Prioritized navigation strategy" predictions
table(games$original_nav_strategy)
# 1.1.	Participants in the "trade-off + device" training condition will be more likely to mention "avoid empty rooms" and/or "prioritize rooms with yellow victims in them" as their building navigation strategy in the pre-trial survey.
exp_func (DV="original_nav_strat_yelempt", IV="device", data=games)
# 1.2.	The amount of time a navigation strategy has been used in the past will increase the likelihood that participants will mention that strategy in the pre-trial survey. 
exp_func (DV="original_nav_strat_yellow", IV="nav_strat_yel_prev_most_time", data=games)
exp_func (DV="original_nav_strat_seq", IV="nav_strat_seq_prev_most_time", data=games)
# 1.3.	The average past benefit rate of a navigation strategy will increase the likelihood that participants will mention that strategy in the pre-trial survey. 
exp_func (DV="original_nav_strat_yellow", IV="nav_strat_yel_prev_most_points", data=games)
exp_func (DV="original_nav_strat_seq", IV="nav_strat_seq_prev_most_points", data=games)
# 1.4. Participants with a greater number of prior device uses, as evidenced by participants avoiding empty rooms (no beeps) or rooms inconsistent with a player's ongoing strategy (e.g. green only rooms when a player's strategy is yellow only), will be more likely to mention "avoid empty rooms" and/or "prioritize rooms with yellow victims in them" as their building navigation strategy in the pre-trial survey.
exp_func (DV="original_nav_strat_yelempt", IV="prior_use_consistent_std", data=games)
# 1.5. Participants high in satisficing tendency will be less likely to mention "avoid empty rooms" and/or "prioritize rooms with yellow victims in them" as their building navigation strategy in the pre-trial survey. 
exp_func (DV="original_nav_strat_yelempt", IV="sat_tendency_std2", data=games)
# 1.6. Participants with lower levels of spatial ability will be more likely to mention sequential search as their navigation strategy in the pre-trial survey. 
exp_func (DV="original_nav_strat_seq", IV="spatial_ability_std", data=games)
# 1.7. Participants with lower levels of videogaming experience will be more likely to mention sequential search as their navigation strategy in the pre-trial survey. 
exp_func (DV="original_nav_strat_seq", IV="videogame_experience_std", data=games)

# Equation for hyp. 1.1. (keep largest sample by excluding prior use of strategy variables)

# Outcome: Prioritize yellow first or avoid empty

n_formula_1_1 <- as.formula (original_nav_strat_yelempt ~
                             device +
                             sat_tendency_std2 +
                             spatial_ability_std +
                             videogame_experience_std +
                             complexity +
                             (1 | member_id))
priors1_1 <- cauchy(location = c(MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 4), 2.5, 2.5))
n_model_1_1 <- hlm_func(formula= n_formula_1_1, data = games, family="binomial", priors = priors1_1)

# Equation for hyp. 1.6. & 1.7 .(keep largest sample by excluding prior use of strategy variables)
# Outcome: Prioritize sequential

n_formula_1_2 <- as.formula (original_nav_strat_seq ~
                               device +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_2 <- cauchy(location = c(MDES_l, MDES_l, -MDES_l, -MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 4), 2.5, 2.5))
n_model_1_2 <- hlm_func(formula= n_formula_1_2, data = games, family="binomial", priors = priors1_2)

# Equations for hyps 1.2., 1.3(test on "yellow only" and "sequential" strategies, as the two most common)

n_formula_1_3 <- as.formula (original_nav_strat_yellow ~
                               device +
                               nav_strat_yel_prev_most_time +
                               nav_strat_yel_prev_most_points +
                               prior_use_consistent_std +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_3 <- normal(location = c(MDES_l, MDES_l, MDES_l, MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 7), 2.5, 2.5)) # Changed to normal to avoid convergence issues
n_model_1_3 <- hlm_func(formula= n_formula_1_3, data = games, family="binomial", priors = priors1_3)

n_formula_1_4 <- as.formula (original_nav_strat_seq ~
                             device +
                             nav_strat_seq_prev_most_time +
                             nav_strat_seq_prev_most_points +
                             prior_use_consistent_std +
                             sat_tendency_std2 +
                             spatial_ability_std +
                             videogame_experience_std +
                             complexity +
                             (1 | member_id))
priors1_4 <- normal(location = c(MDES_l, MDES_l, MDES_l, MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 7), 2.5, 2.5)) # Changed to normal to avoid convergence issues
n_model_1_4 <- hlm_func(formula= n_formula_1_4, data = games, family="binomial", priors = priors1_4)

# Equations for hyps 1.4., 1.5 (test on "yellow only + sequential" strategies)

n_formula_1_5 <- as.formula (original_nav_strat_yelempt ~
                               device +
                               nav_strat_seq_prev_most_time +
                               nav_strat_seq_prev_most_points +
                               prior_use_consistent_std +
                               sat_tendency_std2 +
                               spatial_ability_std +
                               videogame_experience_std +
                               complexity +
                               (1 | member_id))
priors1_5 <- normal(location = c(MDES_l, MDES_l, MDES_l, MDES_l, -MDES_l, MDES_l, MDES_l, 0, 0), 
                    scale = c(rep(MDES_l/2, 7), 2.5, 2.5)) # Changed to normal to avoid convergence issues
n_model_1_5 <- hlm_func(formula= n_formula_1_5, data = games, family="binomial", priors = priors1_5)

#' ##2. "Executed navigation strategy" predictions

# Outcome: Yellow-Only

n_formula_2_1 <- as.formula (most_time_nav_strat_yel ~ 
                               original_nav_strat_yellow + 
                               training +
                               complexity +
                               (1 | member_id))
priors2_1 <- normal(location = c(MDES_l, 0, 0, 0, 0, 0), 
                    scale = c(MDES_l/2, rep(2.5, 5))) # USed normal to fix convergence issues
n_model_2_1 <- hlm_func(formula= n_formula_2_1, data = games, family="binomial", priors=priors2_1)


# Outcome: Sequential

n_formula_2_2 <- as.formula (most_time_nav_strat_seq ~ 
                               original_nav_strat_seq +
                               training +
                               complexity +
                               (1 | member_id))
priors2_2 <- cauchy(location = c(MDES_l, 0, 0, 0, 0, 0), 
                    scale = c(MDES_l/2, rep(2.5, 5)))
n_model_2_2 <- hlm_func(formula= n_formula_2_2, data = games, family="binomial", priors=priors2_2)

#' ##3. "Device Use" predictions
# 3.1. Exposure to positive and negative incentives following device beeps will increase the probability of learning the device (per post-strategy survey).  


games_no_device <- subset (games, device == "NoDevice")
exp_func (DV="q239_cat", IV="rooms_entered_empty_std", data=games_no_device)
exp_func (DV="q239_cat", IV="rooms_entered_not_empty_std", data=games_no_device)

v_formula_3_1 <- as.formula (q239_cat ~ 
                               empty_max_trial_std + 
                               not_empty_max_trial_std +
                               training +
                               complexity +
                               (1 | member_id))
priors3_1 <- cauchy(location = c(MDES_l, MDES_l, rep(0, 3)), 
                    scale = c(MDES_l/2, MDES_l/2, rep(2.5, 3)))
v_model_3_1 <- hlm_func(formula= v_formula_3_1, data = games_no_device, family="binomial", priors=priors3_1)

# Since q239 is underpowered, consider plan to use device-relevant strategy in next trial (i.e. "yellow only" & "avoid empty").

exp_func (DV="next_nav_strat_yelempt", IV="rooms_entered_not_empty_std", data=games_no_device)
exp_func (DV="next_nav_strat_yelempt", IV="rooms_entered_empty_std", data=games_no_device)
exp_func (DV="next_nav_strat_yelempt", IV="empty_max_trial_std", data=games_no_device)

v_formula_3_2 <- as.formula (original_nav_strat_yelempt ~ 
                               empty_max_trial_prev_std +
                               not_empty_max_trial_prev_std + 
                               training +
                               complexity +
                               (1 | member_id))
priors3_2 <- cauchy(location = c(MDES_l, MDES_l, rep(0, 3)), 
                    scale = c(MDES_l/2, MDES_l/2, rep(2.5, 3)))
v_model_3_2 <- hlm_func(formula=v_formula_3_2, data = games_no_device, family="binomial", priors=priors3_2)

#' ##4. "Navigation strategy update" predictions
#4.1. Navigation strategy updates will be more likely after participants observe a perturbation.
#4.2. The probability of a navigation strategy update will increase with exposure to positive incentives following device beeps (rooms with victims).
#4.3. The probability of a navigation strategy update will increase with exposure to negative incentives following device beeps (empty rooms).
exp_func (DV="nav_strategy_update", IV="openings_seen", data=rooms_first_half)

n_formula_4_1 <- as.formula (nav_strategy_update ~  
                               openings_seen + 
                               rooms_entered_empty_std + 
                               rooms_entered_not_empty_std + 
                               complexity +
                               training +
                               (1 | member_id))
priors4_1 <- cauchy(location = c(MDES_l, MDES_l, MDES_l, rep(0, 5)), 
                    scale = c(rep(MDES_l/2, 3), rep(2.5, 5)))
n_model_4_1 <- hlm_func(formula= n_formula_4_1, data = rooms_first_half, family="binomial", priors=priors4_1)

#--------------------------------------------------------------------------
## Render into notebook (run code below in separate script to test this one)
#--------------------------------------------------------------------------

# setwd ("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Analytics/Phase_1") # Local execution
# rmarkdown::render("hyp_test.R")
