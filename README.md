smashbox-deployment
========

This repository contains the scripts and documentation to easily deploy CERNBox client-testing configurations with smashbox framework. Analysis and visualization of test results can be monitor with kibana using the kibana-plugin in `smashbox/python/monitoring/kibana_monitoring.py`.

We deploy smashbox with the following purposes:
   * Regression-testing
   * Behaviour comparison of the sync client with different configurations: platforms, cernbox client versions and endpoints
   * Test the sync client installation on different platforms (e.g., Windows, CentOS, MacOSX)

Currently, it is possible to deploy smashbox in your current machine, a cluster of VMs in OpenStack or within a set of containers using Docker. Finally, this document also describes how to visualize and analyse the test results with kibana (instructions)

project tree   
=================

This repository is organised in the following way:

<pre>
   smashbox-deployment
   ├── documentation/       : procedures to manually set up a machine for continuos testing and monitoring
   ├── docker/              : scripts, docker files and configuration used to automatically deploy and continuosly run smashbox tests in a set of containers
   │   └── Dockerfiles/     : dockerfiles used to build different images for each platform
   │   └── setup.d          : these are the main scripts used to deploy the specified architecture
   ├── kibana/              : this folder contains json files that stores kibana dashboards configurations
   ├── setup.py             : this is the script used to set up automatically the machine
   └── README               : this file

</pre>

Instructions
=================
  - [Deploy and set up a testing cluster of VMs (Openstack)](#Openstack)
  - [Deploy and set up a testing cluster of containers (Docker)](#Docker)
  - [Manually set up a machine for continuos testing and monitoring](#Setting-up-a-machine)
  - [Monitoring and Analysis with kibana](#Monitoring)

<h3 id="Openstack"> Deploy and set up a testing cluster of VMs (Openstack)</h3>

If you want to set up a machine for continuos testing and monitoring with smashbox, you can execute the script `setup.py`. This script is developed to automatically and dinamically install the OwnCloud client, configure smashbox and install the cron job. The steps to use this script are the followings:

###### (1) Manually create a set of VMs in OpenStack. These VMs should follow the naming convention:

smash-"platform"-"oc_client_version". For example: `smash-win10-233`

###### (2) Indicate the configuration of each of these machines in `./deployment_architecture.csv` 

The `./deployment_architecture.csv` file should be stored in the root path of this repository and it contains the following parameters:


|    hostname    |  platform | oc_client |      oc_enpoints                |     runtime     |  ssl_enabled        |  kibana_activity   |
|:--------------:|:---------:|:---------:|:-------------------------------:|:---------------:|---------------------:|-------------------:|
| osx-buildnode  |   MacOSX  |   2.3.3   |   "oc_endpoint1, oc_endpoint2"  |      20:00      |    "True, False"     |   smashbox-deploy  |



Once the machine has been set up, the machine will be configured to read periodically from this configuration file to apply changes (if neccesary).

###### (3) Enter in each VM and execute this installation script `setup.py` as follows:

```
python setup.py --auth auth.conf auth-endpointName.conf
```

The auth.conf is a file required by the application with the following confidential information (owncloud login username and password):
```
oc_account_name = user1  
oc_account_password = password1
```
You need to define at least one `auth-default.conf` with occ username and password and another with the naming convenction: `auth-endpointName.conf`; where endpointName is the name of the endpoint that must use this username and password.  

Note: Alternatively, you can manually set up the machine with the documentation available in `documentation`.

<h3 id="Docker">Deploy and set up a testing cluster of containers (Docker)</h3>

If you want to set up the cluster with containers. You should run the following commands:
```
docker build -t debian-smashbox
docker run -it -e SMASHBOX_OC_ACCOUNT_NAME="XXXX" -e  SMASHBOX_OC_ACCOUNT_PASSWORD="YYYYYY" -e SMASHBOX_OC_SERVER="cernbox.cern.ch" debian-smashbox:latest bash
```

The `docker build` should make reference to the dockerfile with the image desired to set up. Then, it is also neccesary to define the following environment variables:

```
  SMASHBOX_OS
  SMASHBOX_CLIENT_VERSION
  SMASHBOX_OC_SERVER
  SMASHBOX_OC_ACCOUNT_NAME
  SMASHBOX_OC_ACCOUNT_PASSWORD
  SMASHBOX_TESTDIR
  SMASHBOX_SSL_ENABLED
```

<h3 id="Setting-up-a-machine">Manually set up a machine for continuos testing and monitoring</h3>

The documentation and steps to manually setup a machine are in: `./documentation`

<h3 id="Monitoring">Monitoring and Analysis with kibana</h3>

The goal of this section is to provide a convenient monitoring tool for the deployed smashbox testing architecture. For this purpose it has been choosen kibana for visualization and elasticsearch to store tests results.

In order to visualize the test results in kibana; first it is needed to provide the following parameters in `smashbox/etc/smashbox.conf`

  - **kibana_monitoring_host**. This is the host machine where you have running kibana. *For example: kibana_monitoring_host = "http://monit-metrics"*
  - **kibana_monitoring_port**. This is the port to communicate with ELK. *For example:  kibana_monitoring_port = "10012"*
  - **kibana_activity**. This is an additional parameter to be able to identify the data that you are sending to ELK. *For example: kibana_activity = "smashbox-regression"*

The kibana web interface is accessible in https://monit-kibana.cern.ch.

If you don't have yet the dashboard configured. You can download the json file `kibana\cernbox-smashbox.json`; then you need to go to the tab "management" in kibana and import this json file as a saved of object.

![Alt text](/documentation/img/import-kibana-dashboard.png?raw=true "import-kibana-dashboard")

The dashboard has been designed to monitor the failed tests running smashbox with different OwnCloud client versions and different platforms. For regression testing, tests are executed periodically according to the csv file provided in the deployment and the  schedule specified there.

![Alt text](/documentation/img/smashbox-dashboard.png?raw=true "smashbox-dashboard")

** Note: This section is based on the current deployed ELK architecture at CERN. In order to easily deploy an ELK architecture there is a document describing the procedure `kibana/elk-docker.pdf`.
