### UNIT - Next Generation Analytical Pipeline

# Environment

options(digits = 2)
if (!require("pacman")) install.packages("pacman")
library ("pacman")
pacman::p_load(ggplot2, arm, rstan, httr, dplyr, knitr, RCurl, formatR, DT, bayesplot, data.table, foreach, doParallel)

options(mc.cores = parallel::detectCores())
rstan_options(auto_write = TRUE)
Sys.setenv(LOCAL_CPPFLAGS = '-march=native')
set.seed(123456)
start_time <- Sys.time()

# Functions

print_file <- function(file) {
  cat(paste(readLines(file), "\n", sep=""), sep="")
}

extract_one_draw <- function(stanfit, chain = 1, iter = 1) {
  x <- get_inits(stanfit, iter = iter)
  x[[chain]]
}

par_ggplot <- function (data = par_fit, parameter = "a", true, coloring="red") {
  data_sub <- data[parameter]
  d <- ggplot(data_sub, aes(x=data_sub[,1])) + 
    geom_density(aes(colour="Estimated density"), fill=coloring, alpha=0.3) + 
    geom_vline(aes(xintercept=true, linetype = "True Parameter"), colour=coloring) +     
    ggtitle("True parameter and estimated density") + 
    scale_linetype_manual(name = "", values = c(2, 3),
                          guide = guide_legend(override.aes = list(color = coloring))) + 
    labs(x = parameter, colour = "") 
  print (d)
}

# This function is a modified version of `lm.power()` above, enabling parallel
# processing of the for loop, disabling parallel processing for the `stan()` 
# calls and suppressing console output from `stan()`.

lm.power <- function (N, beta, n.sims=1000){
  signif <- rep (NA, n.sims)
  for (s in 1:n.sims){
    sim_data <- list(N=N, a=rnorm(1, 0, 1), b=rnorm(1, beta, 1), sigma=abs(rnorm(1, 0, 10)), x=runif(N, 0, 10))
    sim_out <- stan("models/fake-data.stan", chains=1, iter=1, algorithm="Fixed_param", data=sim_data)
    sim_data$y <- extract_one_draw(sim_out)$y
    fit <- stan("models/simplest-regression.stan", data=sim_data, chains=3, iter=1000, cores = 1, refresh=0)
    par_fit <- extract(fit, pars = "b")[[1]]
    signif[s] <- ifelse (quantile(par_fit, probs = c(0.025)) > 0, 1, 0)
  }
  power <- mean (signif)
  return (power)
}

source ("R/stan_utility.R")

# 1. Print Models 

print_file("models/simplest-regression.stan")
print_file("models/fake-data.stan")

# 2. Simulate Data

N <- 1000
sim_data <- list(N=N, a=10, b=4, sigma=5, x=runif(N, 0, 10))
sim_out <- stan("models/fake-data.stan", chains=1, iter=1, algorithm="Fixed_param", data=sim_data)
sim_data$y <- extract_one_draw(sim_out)$y
hist(sim_data$y, breaks = "fd")
hist(sim_data$x, breaks = "fd")

### 3. Fit simulated data

fit <- stan("models/simplest-regression.stan", data=sim_data)
print(fit)

par_fit <- as.data.frame(sapply(c("a", "b", "sigma"), function(x) extract(fit, pars = x)[[1]]))
par_ggplot (data = par_fit, parameter = "a", true=10, coloring="red")
par_ggplot (data = par_fit, parameter = "b", true=4, coloring="blue")
par_ggplot (data = par_fit, parameter = "sigma", true=5, coloring="green")
check_all_diagnostics(fit)
rstan::traceplot(fit)

# If our model is a good fit then we should be able to use it to generate data that looks a lot like the data we observed.

fit2 <- stan("models/regression.stan", data=sim_data, chains = 3)
y_rep <- as.matrix(fit2, pars = "y_rep")
ppc_dens_overlay(sim_data$y, y_rep[1:1000, ])
ppc_stat(y = sim_data$y, yrep = y_rep, stat = "mean")
ppc_scatter_avg(y = sim_data$y, yrep = y_rep)

# We confirm a good fit of the posterior predictive distribution and observed data. 

### 4. Use Generative Model for Power Analysis

N.values <- 50
beta.values <- 1
power.values <- array (NA, c(length(N.values),length(beta.values)))
for (i1 in 1:length(N.values)){
  for (i2 in 1:length(beta.values)){
    cat ("computing power calculation for N =", N.values[i1], ", beta =", beta.values[i2], "\n")
    power.values[i1,i2] <- lm.power (N=N.values[i1], beta=beta.values[i2], n.sims=10000)
    cat ("power =", power.values[i1,i2], "\n")
  }
}

power.values
write.csv (power.values, "power_values.csv")

# plot all the curves

plot (c(0,max(N.values)), c(0,1), xaxs="i", yaxs="i", xlab="number of participants", ylab="power", type="n")
for (i2 in 1:length(beta.values)){
  lines (c(0,N.values), c(.025,power.values[,i2]))
}

# Hard-coded simulation
N.values <- seq(10, 100, 10)
beta.values <- c(0.5, 1, 2)
power.values2 <- array (NA, c(length(N.values),length(beta.values)))
for (i1 in 1:length(N.values)){
  for (i2 in 1:length(beta.values)){
    power.values2[i1,i2] <- log10(N.values[i1])*(beta.values[i2])/4
    cat ("power =", power.values2[i1,i2], "\n")
  }
}

power.values2 <- as.data.frame(power.values2)
power.values2$Sample.Size <- N.values
colnames(power.values2) <- c("beta=0.5", "beta=1.0", "beta=2.0", "Sample.Size")
long <- melt(setDT(power.values2), id.vars = c("Sample.Size"), variable.name = "Beta")

ggplot(data=long, aes(x=Sample.Size, y=value, group=Beta)) +
  geom_line(aes(color=Beta), size = 1)+
  theme_grey() +
  scale_color_brewer(palette ="Set2") +
  scale_y_continuous(breaks=c(0,0.20, 0.40, 0.60, 0.80, 1)) +
  ggtitle("Bayesian Power by Sample Size and Beta") +
  geom_hline(yintercept=0.8, linetype="dashed", color="darkgray")

# Total Runtime

end_time <- Sys.time()
end_time - start_time
