#!//bin/bash
# by: @jartigag
# thanks to @shellkr@mstdn.io
if [ $# -eq 0 ]
	then
		echo "usage example: ./sort.sh 'tweets' '*'"
	exit 1
else
	echo 'sorting' $(ls -1 | wc -l) 'files by' $1 ; awk -F'.*:' /$1/'{print  $2 , substr(FILENAME,8) }' $2 | sort -n | column
fi
