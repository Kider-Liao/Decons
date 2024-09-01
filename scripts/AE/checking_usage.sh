count=$(ps -aux | grep wrk| wc -l)
if ((count > 1)); then echo "Cluster is busy now!"; else echo "Cluster is idle now!"; fi
