library(readr)
library(dplyr)
sf <- read_csv("data/sampling_frame.csv")

# We want to measure the differences in phat from strata before and after COVID and strata during COVID
sf = stratify(sf)

# 1) Set true stratum probabilities (group B = notcovid; group A = covid)
set_probs <- function(sf, covid_idx, p_B = 0.30, delta = 0.10) {
  str <- sf$strata
  p_h <- ifelse(str %in% covid_idx, p_B + delta, p_B) # two-sample diff = delta
  p_h <- pmin(pmax(p_h, 1e-6), 1 - 1e-6)
  p_h[match(str, str)] # vector aligned to rows
}

# 2) Simulate the finite population outcomes once per replicate
simulate_frame <- function(sf, covid_idx, p_B = 0.30, delta = 0.10) {
  p_i <- set_probs(sf, covid_idx, p_B, delta)
  sf$y <- rbinom(nrow(sf), 1, p_i)
  sf
}

# 3) Estimator and variance (as before)
estimate_group_p <- function(samp, N_h, group_strata) {
  tab <- samp |>
    dplyr::filter(strata %in% group_strata) |>
    dplyr::group_by(strata) |>
    dplyr::summarise(n_h = dplyr::n(), p_h = mean(y), .groups = "drop")
  W <- N_h[group_strata] / sum(N_h[group_strata])
  W_h <- W[match(tab$strata, names(W))]
  var_h <- (1 - tab$n_h / N_h[as.character(tab$strata)]) *
    tab$p_h *
    (1 - tab$p_h) /
    pmax(tab$n_h, 1)
  list(p_hat = sum(W_h * tab$p_h), var_hat = sum((W_h^2) * var_h))
}

# 4) Power simulation
power_strat_diff <- function(
  sf,
  n,
  B = 1000,
  alpha = 0.05,
  covid_idx,
  notcovid_idx,
  alloc_fn = prop.sample,
  var.plan = NULL,
  p_B = 0.20,
  delta = 0.10,
  two_sided = TRUE
) {
  N_h <- table(sf$strata)
  rej <- replicate(B, {
    sf_pop <- simulate_frame(sf, covid_idx, p_B, delta) # <-- y~Bern here
    samp <- alloc_fn(sf_pop, n = n, var.h = var.plan, seed = NULL)
    A <- estimate_group_p(samp, N_h, covid_idx)
    B <- estimate_group_p(samp, N_h, notcovid_idx)
    z <- (A$p_hat - B$p_hat) / sqrt(A$var_hat + B$var_hat)
    if (two_sided) abs(z) > qnorm(1 - alpha / 2) else z > qnorm(1 - alpha)
  })
  #Return lower bound on rejection rate
  rr = mean(rej)
  rr - qnorm(0.975) * sqrt(rr * (1 - rr) / B)
}

# Search n to hit target power
find_n_strat <- function(
  sf,
  target_power = 0.8,
  alpha = 0.05,
  covid_idx,
  notcovid_idx,
  var.plan = NULL,
  B = 5000,
  lo = 50,
  hi = 5000
) {
  f <- function(n) {
    power_strat_diff(
      sf,
      n,
      B,
      alpha,
      covid_idx,
      notcovid_idx,
      alloc_fn = prop.sample,
      var.plan = var.plan
    )
  }
  plo <- f(lo)
  phi <- f(hi)
  while (phi < target_power) {
    lo <- hi
    hi <- hi * 2
    phi <- f(hi)
  }
  while (lo + 1 < hi) {
    mid <- floor((lo + hi) / 2)
    if (f(mid) >= target_power) hi <- mid else lo <- mid
  }
  list(n_total = hi, power = f(hi))
}

# Example usage
notcovid.idx <- c(1:3, 12:16, 25:26)
covid.idx <- setdiff(sort(unique(sf$strata)), notcovid.idx)

# Find n for 80% power, two-sided alpha=0.05
res <- find_n_strat(
  sf,
  target_power = 0.80,
  alpha = 0.05,
  covid_idx = covid.idx,
  notcovid_idx = notcovid.idx,
  var.plan = var.plan,
  B = 1000
)
