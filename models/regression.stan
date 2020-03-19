
data {
  int<lower=0> N;
  vector[N] x;
  vector[N] y;
}
parameters {
  real a;
  real b;
  real<lower=0> sigma;
}
model {
  y ~ normal(a + b * x, sigma);
}

generated quantities {
 real y_rep[N];

 for (n in 1:N) {
 y_rep[n] = normal_rng(x[n] * b + a, sigma);
 }
}
