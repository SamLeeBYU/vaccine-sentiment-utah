library(readr)
library(stringr)
library(lubridate)
library(dplyr)

library(ggplot2)
library(scales)

source("scripts/stance-functions.R")

prelim <- read_csv("data/sentiment_classification_prelim.csv")
sf <- read_csv("data/sampling_frame.csv")

#Stratification Design
# Strata, 2017, 2018, 2019, 2020Q1, 2020Q2, 2020Q3, 2020Q4, 2021Q1, 2021Q2, 2021Q3, 2021Q4, 2022, 2023
stratify <- function(sf.copy) {
  sf.copy$year = lubridate::year(sf.copy$date)
  sf.copy$quarter = lubridate::quarter(sf.copy$date)
  sf.copy$strata = case_when(
    sf.copy$site == "Deseret News" & sf.copy$year <= 2017 ~ 1,
    sf.copy$site == "Deseret News" & sf.copy$year <= 2018 ~ 2,
    sf.copy$site == "Deseret News" & sf.copy$year <= 2019 ~ 3,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 1 ~ 4,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 2 ~ 5,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 3 ~ 6,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 4 ~ 7,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 1 ~ 8,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 2 ~ 9,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 3 ~ 10,
    sf.copy$site == "Deseret News" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 4 ~ 11,
    sf.copy$site == "Deseret News" & sf.copy$year <= 2022 ~ 12,
    sf.copy$site == "Deseret News" & sf.copy$year <= 2023 ~ 13,

    sf.copy$site == "ksl.com" & sf.copy$year <= 2017 ~ 14,
    sf.copy$site == "ksl.com" & sf.copy$year <= 2018 ~ 15,
    sf.copy$site == "ksl.com" & sf.copy$year <= 2019 ~ 16,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 1 ~ 17,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 2 ~ 18,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 3 ~ 19,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2020 &
      sf.copy$quarter <= 4 ~ 20,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 1 ~ 21,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 2 ~ 22,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 3 ~ 23,
    sf.copy$site == "ksl.com" &
      sf.copy$year <= 2021 &
      sf.copy$quarter <= 4 ~ 24,
    sf.copy$site == "ksl.com" & sf.copy$year <= 2022 ~ 25,
    sf.copy$site == "ksl.com" & sf.copy$year <= 2023 ~ 26
  ) |>
    as.factor()
  sf.copy
}
sf = stratify(sf)

sf.summary = sf %>%
  group_by(strata) %>%
  summarize(
    site = first(site),
    year = first(year),
    quarter = first(quarter),
    N.h = n()
  ) %>%
  ungroup() %>%
  mutate(
    p = N.h / sum(N.h)
  )

# Assumptions (Neyman Allocation)
# 1. It costs the same to obtain a sentiment analysis for each article
# 2. The population variance in each strata is the same within each respective group: COVID and non-COVID years
prop.sample <- function(sf.copy, n, seed = 234, var.h = NULL) {
  set.seed(seed)

  # stratum sizes
  N.h <- as.integer(table(sf.copy$strata))
  strata <- names(table(sf.copy$strata))
  H <- length(N.h)

  # variances per stratum (aligned by name)
  if (is.null(var.h)) {
    var.h <- rep(1, H)
  }
  if (is.null(names(var.h))) {
    names(var.h) <- strata
  }
  var.h <- var.h[strata]
  S.h <- sqrt(pmax(var.h, 0))

  # Neyman allocation
  w <- N.h * S.h
  raw <- n * w / sum(w)

  # largest-remainder rounding to hit sum = n
  plan <- floor(raw)
  rem <- raw - plan
  k <- n - sum(plan)
  if (k > 0) {
    idx <- order(rem, decreasing = TRUE)[seq_len(k)]
    plan[idx] <- plan[idx] + 1
  }

  Ncs <- cumsum(N.h)
  start <- c(0L, head(Ncs, -1L)) + 1L
  ends <- Ncs
  obs_ranges <- Map(seq.int, start, ends)
  sample.idx <- unlist(Map(sample, obs_ranges, plan), use.names = FALSE)
  sf.copy[sample.idx, ]
}
prelim.samp = prop.sample(sf, 2 * 234)
write_csv(prelim.samp, "data/prelim.csv")

stances = as.matrix(prelim[, str_c("stance", LETTERS[1:4])])
prelim$stance = get.stance(stances)

prelim$strata.alloc <- case_when(
  prelim$strata %in% c(1:3, 14:16) ~ "BeforeCOVID",
  prelim$strata %in% c(4:11, 17:24) ~ "DuringCOVID",
  TRUE ~ "AfterCOVID"
)
prelim %>%
  group_by(strata.alloc) %>%
  summarize(
    p.hatA = mean(stance == "A"),
    p.hatB = mean(stance == "B"),
    p.hatC = mean(stance == "C"),
    se.hatA = sqrt(mean(stance == "A") * (1 - mean(stance == "A"))),
    se.hatB = sqrt(mean(stance == "B") * (1 - mean(stance == "B"))),
    se.hatC = sqrt(mean(stance == "C") * (1 - mean(stance == "C")))
  ) %>%
  ungroup()
# => 0.03 for non-COVID years and 0.115 for COVID years

var.plan = numeric(26)
var.plan[c(1:3, 14:16)] = 0.2
var.plan[c(4:11, 17:24)] = 0.3
var.plan[c(12:13, 25:26)] = 0.1

#Determine best sample size given Neyman allocation
source("scripts/sample-size.R")
n.star = res$n

main.sample = prop.sample(sf.copy, 1000, var.h = var.plan, seed = 234)
write_csv(main.sample, "data/main_sample.csv")

#sampled n.h
n.h <- main.sample %>%
  group_by(strata) %>%
  summarize(
    n.h = n(),
    Date = first(date),
    Site = first(site)
  ) %>%
  ungroup() %>%
  mutate(
    Period = ifelse(
      strata %in% c(1:3, 14:16),
      "Before COVID",
      ifelse(strata %in% c(4:11, 17:24), "During Covid", "After COVID")
    )
  )

#### Plots ####
period_bounds <- n.h %>%
  group_by(Period) %>%
  summarize(xmin = min(Date), xmax = max(Date), .groups = "drop") %>%
  arrange(xmin) %>%
  mutate(
    xmax = coalesce(lead(xmin), xmax) # ensures continuous shading
  )

monthly_counts <- sf %>%
  mutate(month_date = floor_date(date, "month")) %>%
  group_by(month_date, site) %>%
  summarize(n = n(), .groups = "drop")

#### Plot of vaccine articles over time ####
ggplot(monthly_counts, aes(x = month_date, y = n, color = site)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.2) +
  scale_color_manual(
    values = c("Deseret News" = "#2B65EC", "ksl.com" = "#E69F00")
  ) +
  scale_x_datetime(
    date_breaks = "3 months",
    date_labels = "%Y-%m"
  ) +
  labs(
    title = "Monthly Count of Vaccine Articles by Site",
    x = "Month",
    y = "Number of Vaccine Articles",
    color = "Site",
    fill = "COVID Period"
  ) +
  theme_minimal(base_size = 24) +
  theme(
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(size = 11, color = "gray30"),
    axis.text.x = element_text(angle = 60, hjust = 1),
    legend.position = "top",
    legend.box = "horizontal",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

#### Plot of n.h ####
ggplot(n.h, aes(x = Date, y = n.h, color = Site)) +
  geom_rect(
    data = period_bounds,
    inherit.aes = FALSE,
    aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf, fill = Period),
    alpha = 0.2,
    color = NA
  ) +
  geom_line(linewidth = 0.7, linetype = "dashed") +
  geom_point(size = 2.5) +
  scale_color_manual(
    values = c(
      "Deseret News" = "#2B65EC",
      "ksl.com" = "#E69F00"
    )
  ) +
  scale_fill_manual(
    values = c(
      "Before COVID" = "#B0C4DE",
      "During Covid" = "#FFE4B5",
      "After COVID" = "#D3D3D3"
    )
  ) +
  scale_x_datetime(
    date_breaks = "6 months",
    date_labels = "%Y-%m"
  ) +
  labs(
    title = "Sample Sizes by Stratum and Site",
    subtitle = "Shaded regions denote COVID-related study periods",
    x = "Date of First Article in Stratum",
    y = "Sample Size per Stratum",
    color = "Site",
    fill = "Period"
  ) +
  theme_minimal(base_size = 24) +
  theme(
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(size = 11, color = "gray30"),
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top",
    legend.box = "horizontal",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

main.dat <- read_csv("data/sentiment_classification_main.csv")
main.dat$stance <- get.stance(as.matrix(main.dat[, str_c(
  "stance",
  LETTERS[1:4]
)]))
main.dat$obs <- 1:nrow(main.dat)

#Display sample for paper
rbind(head(main.dat, 10), tail(main.dat, 10)) %>%
  dplyr::select(
    obs,
    title,
    site,
    date,
    strata,
    stanceA,
    stanceB,
    stanceC,
    stanceD,
    stance
  ) %>%
  View()
