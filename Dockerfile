FROM jrnold/rstan

LABEL maintainer="Pablo Diego-Rosell c_Pablo_Diego-Rosell@gallup.co.uk"

RUN mkdir /app
WORKDIR /app

ADD . /app

RUN R -e "install.packages('pacman', repos='http://cran.us.r-project.org')"

CMD Rscript --vanilla run.R