#!/usr/bin/env bash

SOURCE=${BASH_SOURCE[0]}
# resolve $SOURCE until the file is no longer a symlink
while [ -L "$SOURCE" ]; do
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

echo "DIR: $DIR"
all_folders=$(ls -d $DIR/*/)

for folder in $all_folders
do
    echo "folder: $folder"
    all_files=$(ls $folder)
    for file in $all_files
    do
        if [[ $file == *.running.lsf ]]
        then
            echo "$file is running"
            file_without_num=${file%%.*}
            new_file=${file_without_num}.run.lsf
            mv $folder/$file $folder/$new_file
        fi
    done
done

echo "Done"