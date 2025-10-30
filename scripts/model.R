library(nimble)
library(lubridate)

#return Z given time vector
stratify.time <- function(t.norm, site = "Deseret News") {
  #t is a vector of lubridate date objects
  y = year(t.norm)
  q = quarter(t.norm)
  h <- dplyr::case_when(
    y == 2017 ~ 1,
    y == 2018 ~ 2,
    y == 2019 ~ 3,
    y == 2020 & q == 1 ~ 4,
    y == 2020 & q == 2 ~ 5,
    y == 2020 & q == 3 ~ 6,
    y == 2020 & q == 4 ~ 7,
    y == 2021 & q == 1 ~ 8,
    y == 2021 & q == 2 ~ 9,
    y == 2021 & q == 3 ~ 10,
    y == 2021 & q == 4 ~ 11,
    y == 2022 ~ 12,
    y == 2023 ~ 13,
  )
  if (site != "Deseret News") {
    h = h + 13
  }
  Z = model.matrix(~ -1 + factor(h, levels = 1:26))
  Z
}

#dat is something like prelim
format.data <- function(
  dat,
  response = "B",
  t.0 = lubridate::date("2020-01-20")
) {
  y <- as.integer(dat$stance == response)
  x1 <- as.integer(dat$site == "Deseret News")
  x2 <- as.integer(dat$site == "ksl.com")
  # map strata to 1:H
  hfac <- factor(dat$strata)
  h <- as.integer(hfac)

  t <- as.numeric(lubridate::date(dat$date) - t.0)
  sd.t <- sd(t)
  t <- t / sd.t
  t2 <- t^2
  pre <- as.integer(t < 0)
  post <- 1L - pre

  list(
    scale = list(
      t.0 = t.0,
      sd.t = sd.t
    ),
    data = list(
      y = y,
      x1 = x1,
      x2 = x2,
      pre = pre,
      post = post,
      t = t,
      t2 = t2
    ),
    const = list(
      N = nrow(dat),
      H = nlevels(hfac),

      h = h,

      sigma2beta = 10^2,
      sigma2gamma = 10^2,
      Valpha = 10^2 * diag(2),
      Mualpha = c(0, 0),
      a = 2,
      b = 1
    ),
    inits = list(
      gamma = 0,
      betaDN = -1.3,
      betaKSL = -1.3,
      alpha1 = c(0, 0), # baseline trend coefs
      alpha2 = c(0, 0), # post-period slope changes
      mu = rep(0, nlevels(hfac)),
      sigma2mu = 4
    )
  )
}

model.code <- nimbleCode({
  # Priors
  betaDN ~ dnorm(0, sd = sqrt(sigma2beta))
  betaKSL ~ dnorm(0, sd = sqrt(sigma2beta))

  alpha1[1:2] ~ dmnorm(mean = Mualpha[1:2], cov = Valpha[1:2, 1:2]) # baseline slopes
  alpha2[1:2] ~ dmnorm(mean = Mualpha[1:2], cov = Valpha[1:2, 1:2]) # post slope changes

  sigma2mu ~ dinvgamma(shape = a, scale = b)
  for (s in 1:H) {
    mu[s] ~ dnorm(0, sd = sqrt(sigma2mu))
  }

  gamma ~ dnorm(0, sd = sqrt(sigma2gamma)) # post level change

  # Likelihood
  for (i in 1:N) {
    eta[i] <- betaDN *
      x1[i] +
      betaKSL * x2[i] +
      mu[h[i]] +
      pre[i] * (alpha1[1] * t[i] + alpha1[2] * t2[i]) + # baseline trend
      post[i] * (gamma + alpha2[1] * t[i] + alpha2[2] * t2[i]) # post changes
    probit(p[i]) <- eta[i] # p[i] = phi(eta[i])
    y[i] ~ dbern(p[i])
  }
})

nimble.dat = format.data(prelim)

#Vaccine sentiment model
vsm <- nimbleModel(
  code = model.code,
  name = "vsm",
  constants = nimble.dat$const,
  data = nimble.dat$data,
  inits = nimble.dat$inits,
)
Cvsm <- compileNimble(vsm)

vsm.conf <- configureMCMC(
  vsm,
  monitors = c("alpha1", "alpha2", "betaDN", "betaKSL", "gamma", "mu")
)
vsm.mcmc <- buildMCMC(vsm.conf)
vsm.compiled.mcmc <- compileNimble(vsm.mcmc, project = vsm)

vsm.out <- runMCMC(
  vsm.compiled.mcmc,
  niter = 100000,
  nburnin = 1000,
  thin = 100,
  nchains = 4,
  samplesAsCodaMCMC = TRUE,
  summary = T
)
coda::traceplot(vsm.out$samples)
samples <- as.matrix(vsm.out$samples)

#Parameters
betaDN = samples[, "betaDN"]
betaKSL = samples[, "betaKSL"]
mu = samples[, grep("^mu\\[", colnames(samples))]
gamma = samples[, "gamma"]
alpha1 = samples[, grep("^alpha1\\[", colnames(samples))]
alpha2 = samples[, grep("^alpha2\\[", colnames(samples))]

#Data
iters = 1000
t = seq(min(nimble.dat$data$t), max(nimble.dat$data$t), length.out = iters)
t2 = t^2
t.norm = nimble.dat$scale$t.0 + t * nimble.dat$scale$sd.t
Z.DN = stratify.time(t.norm)
Z.KSL = stratify.time(t.norm, site = "KSL")
pre = 1 * (t < 0)
post = 1 * (t >= 0)

#For DN
eta0DN <- betaDN + mu[, 3]
p.preDN <- pnorm(eta0DN)
p.postDN <- pnorm(eta0DN + (mu[, 4] - mu[, 3]) + gamma)
DeltaDN <- p.postDN - p.preDN

#For KSL
eta0KSL <- betaKSL + mu[, 16]
p.preKSL <- pnorm(eta0KSL)
p.postKSL <- pnorm(eta0KSL + (mu[, 17] - mu[, 16]) + gamma)
DeltaKSL <- p.postKSL - p.preKSL

##### RESULTS #####
#Pr(Delta > 0)
mean(DeltaDN > 0)
mean(DeltaDN)
median(DeltaDN)
quantile(DeltaDN, c(0.025, 0.975))

mean(DeltaKSL > 0)
mean(DeltaKSL)
median(DeltaKSL)
quantile(DeltaKSL, c(0.025, 0.975))

#Overall
Delta <- c(DeltaDN, DeltaKSL)
mean(Delta > 0)
mean(Delta)
median(Delta)
quantile(Delta, c(0.025, 0.975))

library(tidyr)
dens_dn <- density(DeltaDN, n = 2048)
dens_ksl <- density(DeltaKSL, n = 2048)

# 95% CrIs
q_dn <- quantile(DeltaDN, c(.025, .975))
q_ksl <- quantile(DeltaKSL, c(.025, .975))

df_dn <- tibble(
  x = dens_dn$x,
  y = dens_dn$y,
  site = "Deseret News",
  lwr = q_dn[1],
  upr = q_dn[2]
) %>%
  mutate(in_ci = x >= lwr & x <= upr)

df_ksl <- tibble(
  x = dens_ksl$x,
  y = dens_ksl$y,
  site = "KSL",
  lwr = q_ksl[1],
  upr = q_ksl[2]
) %>%
  mutate(in_ci = x >= lwr & x <= upr)

df_plot <- bind_rows(df_dn, df_ksl)

col_map <- c("Deseret News" = "#2B65EC", "KSL" = "#E69F00")

ggplot(df_plot, aes(x = x, y = y, color = site, fill = site)) +
  geom_area(data = subset(df_plot, in_ci), alpha = 0.25, linewidth = 0) +
  geom_vline(xintercept = 0) +
  scale_color_manual(values = col_map, name = "Site") +
  scale_fill_manual(values = col_map, name = "Site") +
  labs(
    title = "Posterior of probability jump at the COVID shock",
    subtitle = "Shaded area is the 95% credible interval",
    x = "Change in Probability at t=0",
    y = "Density",
    color = "Site",
    fill = "Site"
  ) +
  facet_wrap(~site, nrow = 1, scales = "free_y") +
  theme_minimal(base_size = 24) +
  theme(
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(size = 16, color = "gray30"),
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top",
    legend.box = "horizontal",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

eta.simsDN <- matrix(nrow = nrow(samples), ncol = iters)
for (i in 1:nrow(eta.sims)) {
  eta.simsDN[i, ] = betaDN[i] +
    mu[i, 4] + #Because the jump occurs in strata 4 #Use Z.DN %*% t(mu[i, , drop = F]) + for generic predictions
    pre * (alpha1[i, 1] * t + alpha1[i, 2] * t2) +
    post * (gamma[i] + alpha2[i, 1] * t + alpha2[i, 2] * t2)
}

eta.simsKSL <- matrix(nrow = nrow(samples), ncol = iters)
for (i in 1:nrow(eta.sims)) {
  eta.simsKSL[i, ] = betaKSL[i] +
    mu[i, 17] + #Because the jump occurs in strata 17 #Use Z.KSL %*% t(mu[i, , drop = F]) + for generic predictions
    pre * (alpha1[i, 1] * t + alpha1[i, 2] * t2) +
    post * (gamma[i] + alpha2[i, 1] * t + alpha2[i, 2] * t2)
}

# plot(t.norm, pnorm(colMeans(eta.simsDN)))
# plot(t.norm, pnorm(colMeans(eta.simsKSL)))

# In ggplot
summarize_eta <- function(eta_mat, time_vec) {
  p_mat <- pnorm(eta_mat)
  tibble(
    date = time_vec,
    mean = colMeans(p_mat),
    lwr = apply(p_mat, 2, quantile, 0.025),
    upr = apply(p_mat, 2, quantile, 0.975)
  )
}

df_DN <- summarize_eta(eta.simsDN, t.norm) %>% mutate(site = "Deseret News")
df_KSL <- summarize_eta(eta.simsKSL, t.norm) %>% mutate(site = "KSL")

df_plot <- bind_rows(df_DN, df_KSL)

t0 <- nimble.dat$scale$t.0

col_map <- c("Deseret News" = "#2B65EC", "KSL" = "#E69F00")
fill_map <- col_map
t0 <- as.Date(nimble.dat$scale$t.0)

ggplot(df_plot, aes(x = date, y = mean, color = site, fill = site)) +
  geom_ribbon(aes(ymin = lwr, ymax = upr), alpha = 0.15, linewidth = 0) +
  geom_line(linewidth = 0.7) +
  geom_vline(xintercept = as.numeric(t0), linetype = "dashed") +
  scale_color_manual(values = col_map, name = "Site") +
  scale_fill_manual(values = col_map, name = "Site") +
  scale_x_date(date_breaks = "6 months", date_labels = "%Y-%m") +
  labs(
    title = "Predicted probability of 'B' by site",
    subtitle = "Dashed vertical line marks the COVID shock date",
    x = "Date",
    y = "Pr(Stance = 'B')"
  ) +
  theme_minimal(base_size = 24) +
  theme(
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(size = 16, color = "gray30"),
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top",
    legend.box = "horizontal",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )
