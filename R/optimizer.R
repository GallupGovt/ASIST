#' ---
#' title: "ASIST - Gallup Experiment 1 - Optimization"
#' author: "Pablo Diego-Rosell, PhD"
#' date: "November 27, 2020"
#' output:
#'    html_document:
#'      toc: true
#' theme: united
#' ---

#' #Setup

rm(list=ls(all=t))
if (!require("pacman")) install.packages("pacman")
library ("pacman")
pacman::p_load(reshape2, plotly)
setwd ("C:/Users/C_Pablo_Diego-Rosell/Desktop/Projects/ASIST/Analytics/Phase_1")

#' Generate matrix for simulations in Visual Basic (Excel macro)

x <- seq(10, 80, 1) # Range of search times (min 10, max 80, per experiment 1 data)
y <- seq(0, 1, 1/10) # Probabilities as a function of victims rescued over total N (10 yellow victims, per final design)
matrix <- expand.grid(x,x,y) 
write.csv (matrix, "matrix.csv")

#' Run optimizations in Visual Basic and read back in

#' #Optimized probability of green at different probabilities of yellow

optim <- read.csv("optim_green.csv")
for (i in unique(optim$py)) {
  optim1 <- optim[which(optim$py==i), ]
  print(summary(optim1))
  z <- acast(optim1, search_y~search_g1, value.var="optim_pg1")
  persp(seq(1, 80, 1), seq(1, 80, 1), z, phi = 30, theta = 60,
        xlab = "Search time yellow", ylab = "Search time green", zlab = "Probability of green",  
        zlim=c(0,1),
        main=paste("Total Points by Search Times (Py = ", paste(i*10, "/10)"), sep=""), 
        ticktype="detailed")
}

#' #Optimal Probability of Yellow (Full game, optimizing probability of green for total points)

optim <- read.csv("optim_yellow.csv")
zlim1 <- c(0,540)
for (i in unique(optim$py)) {
  optim1 <- optim[which(optim$py==i), ]
  z <- acast(optim1, search_y~search_g1, value.var="points")
  persp(seq(1, 80, 1), seq(1, 80, 1), z, phi = 30, theta = 60,
        xlab = "Search time yellow", ylab = "Search time green", zlab = "Total points", 
        main = paste("Total Points by Search Times (Py = ", paste(i*10, "/10)"), sep=""), 
        ticktype="detailed", zlim =zlim1)
}

# Create interactive plotly visualization with all 10 levels of Py

p <- plot_ly()
for (i in unique(optim$py)) {
  optim1 <- optim[which(optim$py==i), ]
  p <- add_mesh (p, data = optim1,
                 x=optim1$search_y, 
                 y=optim1$search_g1, 
                 z=optim1$points, 
                 type="mesh3d")
}
p <- layout(p, title = "Final score by search times and probability of yellow (optimized for green)", 
            scene = list(
              xaxis = list(title = "Mean Yellow Search Time"),
              yaxis = list(title = "Mean Green Search Time"),
              zaxis = list(title = "Final Score")
            ))
p <- layout(p,
            updatemenus = list(
              list(
                type = "buttons",
                y = 1,
                buttons = list(
                  list(method = "restyle",
                       args = list("visible", c(T,F,F,F,F,F,F,F,F,F,F)),
                       label = "Py = 0.0"),
                  list(method = "restyle",
                       args = list("visible", c(F,T,F,F,F,F,F,F,F,F,F)),
                       label = "Py = 0.1"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,T,F,F,F,F,F,F,F,F)),
                       label = "Py = 0.2"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,T,F,F,F,F,F,F,F)),
                       label = "Py = 0.3"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,T,F,F,F,F,F,F)),
                       label = "Py = 0.4"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,T,F,F,F,F,F)),
                       label = "Py = 0.5"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,F,T,F,F,F,F)),
                       label = "Py = 0.6"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,F,F,T,F,F,F)),
                       label = "Py = 0.7"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,F,F,F,T,F,F)),
                       label = "Py = 0.8"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,F,F,F,F,T,F)),
                       label = "Py = 0.9"),
                  list(method = "restyle",
                       args = list("visible", c(F,F,F,F,F,F,F,F,F,F,T)),
                       label = "Py = 1.0"),
                  list(method = "restyle",
                       args = list("visible", c(T,T,T,T,T,T,T,T,T,T,T)),
                       label = "All")))
            ))
p

htmlwidgets::saveWidget(p, "probs_yellow.html")
