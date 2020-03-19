FROM jrnold/rstan

RUN mkdir /app
WORKDIR /app

ADD . /app

CMD Rscript --vanilla run.R