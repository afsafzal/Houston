library("clustMixType")
n <-100
prb <- 0.9
muk <- 1.5
clusid <- rep(1:4, each = n)
x1 <- sample(c(1,2), 2*n, replace = TRUE, prob = c(prb, 1-prb))
x1 <- c(x1, sample(c(1,2), 2*n, replace = TRUE, prob = c(1-prb, prb)))
x1 <- as.factor(x1)
x2 <- sample(c("A","B"), 2*n, replace = TRUE, prob = c(prb, 1-prb))
x2 <- c(x2, sample(c("A","B"), 2*n, replace = TRUE, prob = c(1-prb, prb)))
x2 <- as.factor(x2)
x3 <- c(rnorm(n, mean = -muk), rnorm(n, mean = muk), rnorm(n, mean = -muk), rnorm(n, mean = muk))
x4 <- c(rnorm(n, mean = -muk), rnorm(n, mean = muk), rnorm(n, mean = -muk), rnorm(n, mean = muk))

x <- data.frame(x1,x2,x3,x4)
# apply k-prototyps
kpres <- kproto(x, 4)
clprofiles(kpres, x)
# in real world clusters are often not as clear cut
# by variation of lambda the emphasize is shifted towards factor / numeric variables
kpres <- kproto(x, 2)
clprofiles(kpres, x)
kpres <- kproto(x, 2, lambda = 0.1)
clprofiles(kpres, x)
kpres <- kproto(x, 2, lambda = 25)
clprofiles(kpres, x)



mydata <- read.table("/Users/afsoona/Documents/workspace/Houston-forked/factory.MAV_CMD_NAV_TAKEOFF.data", header=TRUE)
kpres <- kproto(mydata, 3)
clprofiles(kpres, mydata)