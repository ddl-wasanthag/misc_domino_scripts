# Install R packages from a file
fileName <- "r-packages.txt"
conn <- file(fileName,open="r")
linn <-readLines(conn)
for (i in 1:length(linn)){
        install.packages(linn[i])
   }

# Install archived or packages unavailable at CRAN
devtools::install_version("fitdc", "0.0.1")
remotes::install_github("ropensci/tabulizer")

# install packages from source
install.packages("/translations", repos = NULL, type="source")

# Check if all packages were installed.
a<-installed.packages()
packages<-a[,1] 

for (i in 1:length(linn)){
   if(!(linn[i] %in% packages)) {
           cat(linn[i], " is NOT installed", "\n")
   }
}
close(conn)

