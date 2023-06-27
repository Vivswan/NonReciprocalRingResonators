#!/bin/bash
#SBATCH --job-name=@name@
#SBATCH --output=slurm_%x_%A.log
#SBATCH --mail-user=vis77@pitt.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --cluster=smp
#SBATCH --partition=smp
#SBATCH --time=1-00:00:00
#SBATCH --chdir="/ihome/nyoungblood/vis77"
#SBATCH --requeue

source ~/.bashrc;
module load intel intel-mpi lumerical;

OutFileLocation="${HOME}/slurm_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.log";
RunDirectoryLocation="@RunDirectoryLocation@";
DataDirectoryLocation="@DataDirectoryLocation@";
echo "OutFileLocation: ${OutFileLocation}";
echo "RunDirectoryLocation: ${RunDirectoryLocation}";
echo "DataDirectoryLocation: ${DataDirectoryLocation}";
mkdir -p $DataDirectoryLocation;
EXIT_CODE=1;

run_on_exit() {
  echo "";
  echo "####################################### Billing #######################################";
  echo "";
  sacct -M smp -j "$SLURM_JOBID" --format=AllocTRES%50,elapsed;
  echo "";

  echo "";
  echo "####################################### crc-job-stats.py #######################################";
  echo "";
  crc-job-stats;
  echo "";
  echo "!!!!!! Completed !!!!!!!";
  echo "";
  
  if [ $EXIT_CODE -eq 0 ]; then
    echo "####################################### Main Program: Success ${RunScript} #######################################";
  else
    echo "####################################### Main Program: Failure ${RunScript} #######################################";
  fi
}
trap run_on_exit EXIT;

echo "####################################### Main Program: Starting #######################################";

cd $RunDirectoryLocation || exit 1;

EXIT_CODE=1;
for (( i = 1; i < 4; i++ )); do
  echo "${i}th attempt";
  srun interconnect-batch -logall -trust-script "@name@.sbatch.lsf" >> $OutFileLocation 2>&1 &
  process_id=$!

  while ps -p $process_id > /dev/null; do
    if [ -f "$SLURM_JOB_ID.completed.txt" ]; then
      EXIT_CODE=0;
      echo "Completed Successfully";
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

exit $EXIT_CODE;