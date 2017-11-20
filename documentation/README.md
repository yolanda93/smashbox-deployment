# Smashbox deployment

This README describes the procedure to manually configurate a machine with smashbox for continuos testing and visualize test results with kibana.

### Step 1 - Install the CERNBox/ OwnCloud client
  - Documentation on how to install CERNBox client is available at: https://cernbox.cern.ch/cernbox/doc/clients.html
  - OwnCloud client installation docs are available at:  https://doc.owncloud.org/desktop/1.8/installing.html
### Step 2 - Smashbox Installation
```
git clone https://github.com/cernbox/smashbox.git
cd smashbox
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install requirements.txt
pip install pycurl # This step is for windows only
```
### Step 4 - Smashbox Configuration
```
 cp etc/smashbox.conf.template etc/smashbox.conf
```
 Edit the smashbox.conf file to add the following mandatory parameters:
  - **oc_account, oc_password**. CERNBox/OwnCloud testing account and password
  - **oc_server**. OwnCloud endpoint   
  - **oc_sync_cmd**. The location path of the sync client. On windows the path may be configured like this: oc_sync_cmd = ['C:\Program Files (x86)\cernbox\cernboxcmd.exe',"--trust"]

In order to visualize the results test results in kibana; it is needed also to provide the following parameters:

  - **kibana_monitoring_host**. This is the host machine where you have running kibana. *For example: kibana_monitoring_host = "http://monit-metrics"*
  - **kibana_monitoring_port**. This is the port to communicate with ELK. *For example:  kibana_monitoring_port = "10012"*
  - **kibana_activity**. This is an additional parameter to be able to identify the data that you are sending to ELK. *For example: kibana_activity = "smashbox-regression"*

**Note: We use "smashbox-regression" for the deployed testing infraestracture, if you want to run and visualize internal tests; please specify another value. For example: kibana_activity = "smashbox-user1"

You can also modify additional parameters for advance configurations. These parameters are described in smashbox.conf.

### Step 4 - Setup the cronjob to run smashbox daily and report results to kibana
This step may differ depending on the platform. On windows you can use the Tasks Manager tool and on linux it is recommended the crontab tool.
