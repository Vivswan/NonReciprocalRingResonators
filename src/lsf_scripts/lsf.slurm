#!/bin/bash
#SBATCH --job-name=@name@
#SBATCH --output=slurm_%x_%A.log
#SBATCH --mail-user=vis77@pitt.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --cluster=smp
#SBATCH --partition=smp
#SBATCH --time=1-00:00:00
#SBATCH --chdir="/ihome/nyoungblood/vis77"
#SBATCH --requeue

source "${HOME}/.bashrc";
module load intel intel-mpi lumerical;

OutFileLocation="${HOME}/slurm_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.log";
RunDirectoryLocation="@RunDirectoryLocation@";
DataDirectoryLocation="@DataDirectoryLocation@";
echo "SLURM_JOB_NAME: ${SLURM_JOB_NAME}";
echo "SLURM_JOB_ID: ${SLURM_JOB_ID}";
echo "OutFileLocation: ${OutFileLocation}";
echo "RunDirectoryLocation: ${RunDirectoryLocation}";
echo "DataDirectoryLocation: ${DataDirectoryLocation}";
mkdir -p $DataDirectoryLocation;
EXIT_CODE=1;

run_on_exit() {
  echo "";
  echo "####################################### Billing #######################################";
  echo "";
  sacct -M "$SLURM_CLUSTER_NAME" -j "$SLURM_JOBID" --format=AllocTRES%50,elapsed;
  echo "";

  echo "";
  echo "####################################### crc-job-stats.py #######################################";
  echo "";
  crc-job-stats;
  echo "";
  echo "!!!!!! Completed !!!!!!!";
  echo "";
  
  if [ $EXIT_CODE -eq 0 ]; then
    echo "####################################### Main Program: Success #######################################";
  else
    echo "####################################### Main Program: Failure #######################################";
  fi
}
trap run_on_exit EXIT;

echo "####################################### Main Program: Starting #######################################";

cd $RunDirectoryLocation || exit 1;

EXIT_CODE=1;
LAST_MODIFIED_TIME=$(date +%s);
for (( i = 1; i < 4; i++ )); do
  echo "${i}th attempt";
  srun interconnect-batch -logall -trust-script "@name@.sbatch.lsf" >> "${OutFileLocation}" 2>&1 &
  process_id=$!

  while ps -p $process_id > /dev/null; do
    if [ -f "$SLURM_JOB_ID.completed.txt" ]; then
      EXIT_CODE=0;
      rm "$SLURM_JOB_ID.completed.txt";
      echo "Completed Successfully";
      kill -15 $process_id;
      kill -9 $process_id;
      break;
    fi

    if [ -f "$SLURM_JOB_ID.run.txt" ]; then
      LAST_MODIFIED_TIME=$(stat -c %Y "$SLURM_JOB_ID.run.txt");
      cat "$SLURM_JOB_ID.run.txt";
      rm "$SLURM_JOB_ID.run.txt";
    fi

    current_time=$(date +%s);
    time_difference=$((current_time - LAST_MODIFIED_TIME));
    if [ $time_difference -gt 600 ]; then
      echo "No progress in the 10 minutes. Killing the process";
      kill -15 $process_id;
      kill -9 $process_id;
      break;
    fi
    
    sleep 10;
  done

  if [ $EXIT_CODE -eq 0 ]; then
    break;
  fi

  sleep 5;
done

all_files=$(ls ./*."${SLURM_JOB_ID}".running.lsf);
for file in $all_files; do
  file_without_num=$file;
  file_without_num=${file_without_num%.*};
  file_without_num=${file_without_num%.*};
  file_without_num=${file_without_num%.*};
  new_file=${file_without_num}.run.lsf;
  echo "$file -> $new_file";
  mv "$file" "$new_file";
done

exit $EXIT_CODE;
