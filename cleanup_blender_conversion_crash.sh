#!/bin/bash
export MODEXPORTER_OUTPUTROOT=$HOME
export MODEXPORTER_OUTPUTDIR=${MODEXPORTER_OUTPUTROOT}/oblivion.output/jobs

rm ${MODEXPORTER_OUTPUTDIR}/*.lock
echo "----------------------------------------------"
echo "Cleanup completed."
echo "----------------------------------------------"
exit

echo ""
echo "----------------------------------------------"
echo ""
echo "Cleanup completed. Press any key to close window."
echo ""
echo "----------------------------------------------"
echo ""
exit

echo ""
echo "----------------------------------------------"
echo "Total jobs found = " $count
echo "No locks found, no cleanup necessary."
echo ""
echo "Press any key to close window."
echo "----------------------------------------------"
echo ""
exit
