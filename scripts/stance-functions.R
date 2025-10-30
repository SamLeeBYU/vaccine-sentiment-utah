# X: n x 4 matrix with columns A,B,C,D
get.stance <- function(X) {
  stopifnot(ncol(X) == 4)
  A <- X[, 1]
  B <- X[, 2]
  C <- X[, 3]
  D <- X[, 4]

  # row max and ties at the max
  m <- do.call(pmax, as.list(as.data.frame(X)))
  tA <- A == m
  tB <- B == m
  tC <- C == m
  tD <- D == m
  k <- tA + tB + tC + tD # number of max ties per row

  S <- X # adjusted scores (for tie-breaks only)

  ## Rule 1: C and D tied, plus at least one more tied -> choose D
  r1 <- tC & tD & (k >= 3)
  S[r1, 4] <- S[r1, 4] + 1L

  ## Rule 2: A and B tied -> choose C
  r2 <- tA & tB
  S[r2, 3] <- S[r2, 3] + 1L

  ## Rule 3: A/B tied with C -> choose C
  r3 <- (tA & tC) | (tB & tC)
  S[r3, 3] <- S[r3, 3] + 1L

  ## Rule 4: A/B tied with D
  # If the extra one is the other of A/B, choose C; otherwise choose D
  r4a <- tA & tD
  r4a_chooseC <- r4a & tB # extra tie is B
  S[r4a_chooseC, 3] <- S[r4a_chooseC, 3] + 1L
  S[r4a & !r4a_chooseC, 4] <- S[r4a & !r4a_chooseC, 4] + 1L

  r4b <- tB & tD
  r4b_chooseC <- r4b & tA # extra tie is A
  S[r4b_chooseC, 3] <- S[r4b_chooseC, 3] + 1L
  S[r4b & !r4b_chooseC, 4] <- S[r4b & !r4b_chooseC, 4] + 1L

  # final stance by argmax after adjustments
  idx <- max.col(S, ties.method = "first")
  c("A", "B", "C", "D")[idx]
}
