#!/bin/sh
#$ -S /bin/sh
#$ -N FRET-BENCHMARK 
#$ -o /netapp/sali/mbonomi/working/FRET_BENCHMARK/OUT_ERR 
#$ -e /netapp/sali/mbonomi/working/FRET_BENCHMARK/OUT_ERR 
#$ -r n
#$ -j n
#$ -l netapp=5G
#$ -l h_rt=24:00:00
#$ -l mem_free=4G
#$ -q lab.q
#$ -l arch=linux-x64 
#$ -l hostname="iq10[2-9]|iq1[1-9][0-9]|ih*|io*"
#$ -R yes
#$ -V
#$ -cwd
#$ -t 1-1280

# Root directory
export ROOT=`cd ../../../ && pwd`

# Directory where tests are executed and results are stored
export RESULTDIR=${ROOT}/RESULTS_LINKER
# Data directory (with useful stuff)
export DATADIR=${ROOT}/DATA
# Gaussian Mixture Models for model of linker flexibility
export GMMDIR=${DATADIR}/GMM
# PDB location
export PDBDIR=${DATADIR}/PDBs
# SCRIPTs needed by the benchmark
export SCRIPTDIR=${DATADIR}/SCRIPTS/BENCHMARK_LINKER

# JOB ID
ID=$SGE_TASK_ID

# create working dir
mkdir ${RESULTDIR}/testdir${ID}

# create command lines for test #ID from global list
sed -n ${ID}p GENERATE_COMMAND_LIST > ${RESULTDIR}/testdir${ID}/go.sh
sed -n ${ID}p SAMPLE_COMMAND_LIST  >> ${RESULTDIR}/testdir${ID}/go.sh                                   

# go into directory
cd ${RESULTDIR}/testdir${ID}

# run 
SCRIPTDIR=$SCRIPTDIR PDBDIR=$PDBDIR GMMDIR=$GMMDIR bash go.sh
