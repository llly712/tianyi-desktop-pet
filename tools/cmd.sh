CONTAINER=astrbot_mhcm-astrbot_MHCM-1
echo "=== recent pet_bridge ==="
docker logs --tail 300 $CONTAINER 2>&1 | grep -i 'pet_bridge\|PetBridge' | tail -25
echo "=== recent errors ==="
docker logs --tail 300 $CONTAINER 2>&1 | grep -iE 'Traceback|Error|Exception' | tail -25
