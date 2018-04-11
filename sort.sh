#!//bin/bash
# by: @jartigag
# thanks to @shellkr@mstdn.io
echo 'sorting' $(ls -1 | wc -l) 'files by' $1 ; awk -F'.*:' /$1/'{print  $2 , substr(FILENAME,8) }' $2 | sort -n | column
