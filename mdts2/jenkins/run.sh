#!/bin/bash -x

MIDONET_TARGET_VERSION=$1

if [ "$MIDONET_TARGET_VERSION" == "midonet1" ] ; then
    PLUGIN_SETTING="http://github.com/tomoe/networking-midonet.git midonet1"
else
    PLUGIN_SETTING="http://github.com/stackforge/networking-midonet.git"
fi


sudo pip install nose

git clone http://github.com/openstack-dev/devstack
cd devstack

export MIDONET_ENABLE_Q_SVC_ONLY=True
export LOG_COLOR=False
export SCREEN_LOGDIR=$WORKSPACE/logs

cat > local.conf <<EOF
#!/usr/bin/env bash

[[local|localrc]]

# Load the devstack plugin for midonet
enable_plugin networking-midonet $PLUGIN_SETTING

EOF

./stack.sh


cd $WORKSPACE/mdts/mdts2/tests/functional_tests/


PYTHONPATH=../../../ nosetests -vv --with-xunit --xunit-file=$WORKSPACE/logs/nosetests.xml
EXIT_CODE=$?

# copy log file to archive
mkdir -p $WORKSPACE/artifacts
cp -rL $WORKSPACE/logs/ $WORKSPACE/artifacts

exit $EXIT_CODE

