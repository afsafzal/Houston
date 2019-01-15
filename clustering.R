library("dtwclust")
library("optparse")

option_list = list(
  make_option("--data_dir", type="character", default=NULL, 
              help="path to the data directory"),
  make_option(c("-c", "--command"), type="character", default=NULL, 
              help="desired command"),
  make_option("--output_dir", type="character", default="", 
              help="path to the output directory"),
  make_option(c("-k", "--clusters"), type="integer", default=3, 
              help="number of clusters (k)"),
  make_option("--fuzzy", action="store_true", default=FALSE, 
              help="desired command")
); 

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

if(is.null(opt$data_dir) || is.null(opt$command)) {
  print_help(opt_parser)
  stop("Required arguments missing!")
}

files <- list.files(path=opt$data_dir, pattern=paste("factory.", opt$command, ".+.csv", sep=""), full.names=TRUE, recursive=FALSE)

myData <- list()
i <- 1
for (f in files) {
  m <- read.csv(f, header=TRUE)[,1]
  m <- as.matrix(m)
  myData[[i]] <- m
  i <- i+1
}

write(files, file=paste(opt$output_dir, "files.txt", sep=""))

#myData2 <- zscore(myData)
#m <- read.csv(files[1], header=TRUE)

if (!opt$fuzzy) {
mvc <- tsclust(myData, k = opt$clusters, distance = "dtw", seed = 390L)
plot(mvc)
} else {
mvc <- tsclust(myData, k = opt$clusters, type = "fuzzy", seed = 390L)
plot(mvc)
}
write(paste("Int64", toString(mvc@cluster), sep = "\n"), file=paste(opt$output_dir, "labels.txt", sep=""))
save.image(file=paste(opt$output_dir, opt$command, ".RData", sep=""))


