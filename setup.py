#!\Python27\python
import argparse
import sys
import os
from os import listdir
from os.path import isfile, join
import csv
import socket
import shutil
import subprocess
import platform

deployment_config_link = "https://cernbox.cern.ch/index.php/s/65BChf3cbz7OoDe/download"

# linux, macosx windows
cbox_v = {
    "2.3.3": ["centos7-cernbox.repo","2.3.3.1807","2.3.3.1110"],
    "2.2.4": ["cernbox-2.2.4.968-linux/CentOS_7/ownbrander:cernbox","2.2.4.1495","2.2.4.830"],
    "2.1.1": ["cernbox-2.1.1.697-linux/CentOS_7/ownbrander:cernbox","2.1.1.1144","2.2.2.570"],
    "2.0.2": ["cernbox-2.0.2.445-linux/CentOS_7/ownbrander:cernbox","2.0.2.782","2.0.2.236"],
    "1.6.4": ["cernbox-1.6.4/CentOS_7/ownbrander:cernbox","1.6.4.1197","1.6.4.4043"],
    "2.0.1": ["cernboxtest-2.0.1/CentOS_7/ownbrander:cernbox","2.0.1.747","2.0.1.203"],
    "1.7.1": ["cernbox-1.7.1/CentOS_7/ownbrander:cernbox","1.7.1.1810","1.7.1.4505"],
    "1.7.2": ["cernbox-1.7.2/CentOS_7/ownbrander:cernbox","1.7.2.2331","1.7.2.5046"],
    "1.8.3": ["cernbox-1.8.3/CentOS_7/ownbrander:cernbox","1.8.3.510","1.8.3.499"],
}


required_packages = ['urllib2','wget','pyoclient']

if platform.system() == "Windows":
    required_packages.append('pycurl')
    required_packages.append('pip') # windows don't have a pip in path as default
else:
    required_packages.append('python-crontab')
    required_packages.append('pyoclient')

def install_and_import(pkg):
    """ Setup some needed python packages for the execution of this script
    """
    import site
    import importlib

    try:
        importlib.import_module(pkg)
    except ImportError:
        print(pkg + " not present. Installing " + pkg + " ...")
        try:
            import pip
            pip.main(['install', pkg])
        except:
           print("pip not present. Installing pip ...")
           os.system(sys.executable + " -m easy_install pip")
           reload(site)

        import pip # retry
        if pkg == "pyoclient":
            pip.main(['install', "git+https://github.com/owncloud/pyocclient.git@master#egg=pyocclient"])
        else:
            pip.main(['install', pkg])
            reload(site) # Most of the stuff is set up in Python's site.py which is automatically imported when starting the interpreter

        if pkg != "python-crontab" and  pkg != "pyoclient": # import python-crontab later
            importlib.import_module(pkg)
            globals()[pkg] = importlib.import_module(pkg) # make sure that the pkg is in global namespace

for pkg in required_packages:
    install_and_import(pkg)

####### monitoring utilities to publish deployment state in kibana ############################################################

def get_monitoring_host():
    """
    Get kibana parameters defined in smashbox.conf
    """
    smashbox_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)),"smashbox","etc","smashbox-cernbox.conf")
    try:
        conf_file = open(smashbox_conf, 'r')

        for line in conf_file:
            if line[0:len("kibana_monitoring_host = ")] == "kibana_monitoring_host = ":
                monitoring_host = line[len("kibana_monitoring_host = ")::].rsplit('\n')[0].replace('"', '')
            if line[0:len("kibana_monitoring_port = ")] == "kibana_monitoring_port = ":
                monitoring_port = line[len("kibana_monitoring_port = ")::].rsplit('\n')[0].replace('"', '')

        return monitoring_host,monitoring_port
    except:
        return "","" # Only info if the host machine is tested against production also (TODO:consider also allow add small tests)

def publish_deployment_state(deployment_config):
    """
    This function publish new configuration deployment
    in the kibana dashboard
    """
    import time

    monitoring_host, monitoring_port = get_monitoring_host()
    json_result = [{'producer': "cernbox", 'type': "ops", 'hostname': socket.gethostname(),
                    'timestamp': int(round(time.time() * 1000)),'deployment':deployment_config}]

    send_and_check(json_result,monitoring_host,monitoring_port)
    return True

def send(document,monitoring_host,monitoring_port):
    import requests
    import json

    return requests.post(monitoring_host + ":" + monitoring_port + "/", data=json.dumps(document),
           headers={"Content-Type": "application/json; charset=UTF-8"})

def send_and_check(document, monitoring_host,monitoring_port, should_fail=False):
    response = send(document, monitoring_host, monitoring_port)
    assert (
    (response.status_code in [200]) != should_fail), 'With document: {0}. Status code: {1}. Message: {2}'.format(
        document, response.status_code, response.text)


####### git repo utilities without using git commands (Windows lack of git on cmd) #############################################

def this_repo_name():
    current_path = os.path.dirname(os.path.abspath(__file__))
    git_config = open(os.path.join(current_path,".git","config"), 'rb')

    for line in git_config:
        if line[0:len("	url = ")] == "	url = " :
            return line[len("	url = ")::].split('\n')[0]

this_repo =  this_repo_name()

def get_repo_name(repo_url):
    """ This function is a workaround for Windows
    lack of git on cmd
    """
    if (repo_url[0:len("https://github.com/")]=="https://github.com/"): #git repo
        repo_name = repo_url.split("https://github.com/")[1][:-4]
    else:
        print "incorrect repo url or git service not supported"
        exit(0)
    return repo_name


def download_repository(repo_url):
    """ This function is a workaround for Windows
    lack of git on cmd
    """
    repo_name = get_repo_name(repo_url)
    print repo_name

    try:
        this_filepath = os.path.dirname(os.path.abspath(__file__))
        import wget
        wget.download("http://github.com/" + repo_name + "/archive/master.zip")
        shutil.move(os.path.join(os.getcwd(),repo_name.split("/")[1] + "-master.zip"),os.path.join(os.path.dirname(os.path.abspath(__file__)),repo_name.split("/")[1] + "-master.zip"))
        import zipfile
        print repo_name
        zip_ref = zipfile.ZipFile(os.path.join(os.path.dirname(os.path.abspath(__file__)),repo_name.split("/")[1] + "-master.zip"), 'r')
        zip_ref.extractall(this_filepath)
        zip_ref.close()
        os.rename(os.path.join(this_filepath,repo_name.split("/")[1] +"-master"), os.path.join(this_filepath,repo_name.split("/")[1]))
        os.remove(os.path.join(this_filepath,repo_name.split("/")[1] +"-master.zip"))
    except:
        "git service is not accessible"

def remove_old_folders():
    tmp_folder1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), get_repo_name(this_repo).split("/")[1])
    if os.path.exists(tmp_folder1) :  # if windows removed the "smashbox-deploymnet" folder (this folder is incorrectly leaved after updates)
        shutil.rmtree(tmp_folder1)

    tmp_folder2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smashbox")
    if os.path.exists(tmp_folder2) :  # if windows removed the "smashbox" folder (this folder is incorrectly leaved after updates)
        shutil.rmtree(tmp_folder2)

####### utilities for this installation script #################################################################################

def smash_check():

    current_path = os.path.dirname(os.path.abspath(__file__))

    test_endpoints = [f for f in listdir(os.path.join(current_path,"smashbox","etc")) if f[0:len('smashbox-')] == 'smashbox-'] # test endpoint

    for endpoint in test_endpoints:
        print '\033[94m' + "Testing smashbox installation in " + str(socket.gethostname()) + " with " + endpoint + '\033[0m'
        cmd = sys.executable + " " + current_path + "/smashbox/bin/smash " + current_path + "/smashbox/lib/test_nplusone.py  -c " + current_path +"/smashbox/etc/" + endpoint
        try:
             os.system(cmd)
        except Exception as e:
            print "Smashbox installation failed: Non-zero exit code after running smashbox with " + endpoint
            print e
            exit(0)
        print "Smashbox installation success! with " +  endpoint

def smash_run(endpoint):
    print '\033[94m' + "Running smashbox in " +  str(socket.gethostname()) + '\033[0m' + '\n'
    current_path = os.path.dirname(os.path.abspath(__file__))
    try:
        os.system(sys.executable + " " + current_path + "/smashbox/bin/smash --keep-going " + current_path + "/smashbox/lib/ -c " + current_path +"/smashbox/etc/smashbox-" + endpoint + ".conf") # run smashbox normally
    except:
        print "Smashbox failed: Non-zero exit code after running smashbox with " + endpoint
       # continue with next endpoint

def install_oc_client(version):
    import wget

    if platform.system() == "linux" or platform.system() == "linux2":  # linux
        print '\033[94m' + "Installing cernbox client " + version + " for linux" + '\033[0m' + '\n'
        wget.download("http://cernbox.cern.ch/cernbox/doc/Linux/" + cbox_v[version][0])
        shutil.copyfile(cbox_v[version][0] + ".repo", "/etc/yum-puppet.repos.d/cernbox.repo")
        os.system("yum update")
        os.system("yum install cernbox-client")
        os.remove(cbox_v[version][0] + ".repo")

    elif platform.system() == "darwin":  # MacOSX
        print '\033[94m' + "Installing cernbox client " + version + " for MAC OSX" + '\033[0m' + '\n'
        wget.download("https://cernbox.cern.ch/cernbox/doc/MacOSX/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("cp ./cernbox-" + cbox_v[version][1] +"-signed.pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("installer -pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg -target /")


    elif platform.system() == "Windows":  # Windows
        print '\033[94m' + "Installing cernbox client " + version + " for Windows" + '\033[0m' + '\n'
        wget.download("https://cernbox.cern.ch/cernbox/doc/Windows/cernbox-" + cbox_v[version][2] +"-setup.exe")
        #os.rename(os.path.join(os.getcwd(),"cernbox-" + cbox_v[version][2] +"-setup.exe"), os.path.join(os.getcwd(),"/tmp/cernbox-" + cbox_v[version][2] +"-setup.exe"))
        os.system("cernbox-" + cbox_v[version][2] +"-setup.exe /S")
        os.remove("cernbox-" + cbox_v[version][2] +"-setup.exe")

def generate_config_smashbox(oc_account_name, oc_account_password, endpoint, ssl_enabled, kibana_activity):
    print '\033[94m' + "Installing/updating smashbox for: " + endpoint + '\033[0m' + '\n'
    # TODO: Solve this bug in smashbox. Smashbox always requires a file with the name "smashbox.conf" even if it is not used ( -c smashbox option)
    shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto-smashbox.conf"), os.path.join(os.path.dirname(os.path.abspath(__file__)),"smashbox","etc","smashbox.conf" ))

    new_smash_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)),"smashbox","etc","smashbox-" + endpoint + ".conf" )
    shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),"auto-smashbox.conf"),new_smash_conf)
    f = open(new_smash_conf, 'a')

    f.write('oc_account_name = ' + '"{}"'.format(oc_account_name) + '\n')
    f.write('oc_account_password = ' + '"{}"'.format(oc_account_password) + '\n')
    f.write('oc_server = ' + '"{}"'.format(endpoint + ".cern.ch" + "/cernbox/desktop") + '\n')

    f.write('oc_ssl_enabled = ' + ssl_enabled + '\n')

    oc_sync_path = get_oc_sync_cmd_path()
    f.write('oc_sync_cmd = ' + '"{}"'.format(oc_sync_path) + '\n')

    f.write('kibana_activity =' + '"{}"'.format(kibana_activity) + '\n')

    f.close()


def get_oc_sync_cmd_path():
    if platform.system() == "Windows":
        path = ['C:\Program Files (x86)\cernbox\cernboxcmd.exe', '--trust']
    elif platform.system() == "Linux":
        location = os.popen("whereis cernboxcmd").read()
        if len(location)>0:
            path = "/" + location.split("cernboxcmd")[1].split(": /")[1] + "cernboxcmd --trust"
        else: # no cernbox installed
            path = ""
    elif platform.system() == "Darwin":
        path = "/Applications/cernbox.app/Contents/MacOS/cernboxcmd --trust"

    return path

def backup_results(): # TODO: add the option to backup the test results
    return True

def create_cron_job():
    """ This is the method to create the cron jobs
    """
    if platform.system() != "Windows":

        runtime = current_config['runtime'].split(":")
        job_time = runtime[1] + " " + runtime[0] + " * * *"
        print '\033[94m' + "Installing cron job at: " + job_time + '\033[0m'  + '\n'
        #user = os.popen("echo $USER").read().split("\n")[0]

        import sys
        from crontab import CronTab
        my_cron = CronTab("root") # This installation script needs to be run as root

        job_is_updated = False
        for job in my_cron:
            if job.comment == 'smashbox-' + current_config['runtime']:
                job_is_updated = True

        if not job_is_updated: # Install cron job
            current_path = os.path.dirname(os.path.abspath(__file__))
            job = my_cron.new(command=sys.executable + " " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup.py"), comment='smashbox-' + current_config['runtime'])
            job.setall(str(job_time))
            my_cron.write()

    else:
        import sys

        print '\033[94m' + "Installing cron job at: " + str(current_config['runtime']) + '\033[0m'  + '\n'
        this_exec_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)),"setup.py" + "'")

        cmd = "schtasks /Create /SC DAILY /TN Smashbox /ST " + current_config['runtime'] + " /TR " + this_exec_path + " /F" # /F is to force the overwrite of the existing scheduled task
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if (len(stderr) > 0):
            print "The task cannot be created on Windows - ", stderr
        else:
            print "The task has been successfully installed"


def ocsync_version(oc_sync_cmd):
    """ Return the version reported by oc_sync_cmd.
     :return a tuple (major,minor,bugfix). For example: (1,7,2) or (2,1,1)
     Note: Same method as cernbox/smashbox project
    """
    # strip possible options from config.oc_sync_cmd
    cmd = [oc_sync_cmd[0]] + ["--version"]
    try:
        process = subprocess.Popen(cmd, shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = process.communicate()
    except:
        return ""

    sver = stdout.strip().split()[2]  # the version is the third argument

    return tuple([int(x) for x in sver.split(".")])

def check_oc_client_installation(config):
    """ It checks owncloud client installation and it installs a new
    version (if required)
    """
    version_tuple = ocsync_version(get_oc_sync_cmd_path())
    installed_version = str(version_tuple)[1:-1].replace(", ", ".")

    if (config["oc_client"] != installed_version): # TODO: check if it is needed to unistall previous version
        install_oc_client(config["oc_client"])  # update version

def setup_config(deployment_config, accounts_info,is_update):
    """ This method installs oc_client and smashbox with the current host and
     the parameters (oc_client_version, oc_server, accounts_info).
    These parameters are defined in deployment_config (deployment_architecture.csv)
    :return this_host_config with the corresponding deployment
    configuration for this host
    """
    this_host_config = dict()
    for row in deployment_config:
        if(row["hostname"]==socket.gethostname()):
            this_host_config = row
            row["state"] = "Active"

    if not this_host_config:
        this_host_config["state"] = "Deleted"
        print "this host has been removed from the configuration files; please manually delete this vm"  + '\n'
        exit(0)
    else:
        download_repository("https://github.com/cernbox/smashbox.git")

        check_oc_client_installation(this_host_config)

        endpoints_list =  this_host_config["oc_endpoints"].split(",")
        ssl_enabled_list =  this_host_config["ssl_enabled"].split(",")

        # configurate smashbox
        for endpoint, ssl_enabled in zip(endpoints_list,ssl_enabled_list):
            if endpoint in accounts_info.keys():
                generate_config_smashbox(accounts_info[endpoint]["oc_account_name"],
                                         accounts_info[endpoint]["oc_account_password"],endpoint,
                                         ssl_enabled,this_host_config["kibana_activity"])
            else:
                if "default" not in accounts_info.keys():
                    print "ERROR auth-default.conf : At least one valid auth-default.conf file with default owncloud client username and password is required"
                    exit(0)
                else:
                    generate_config_smashbox(accounts_info["default"]["oc_account_name"],
                                             accounts_info["default"]["oc_account_password"], endpoint,
                                             ssl_enabled, this_host_config["kibana_activity"])

    return this_host_config


def get_occ_credentials(auth_files):
    """ This method loads the config file "auth_files"
    passed to the script as argument
    :return  account_info as a list of dict with oc_account_name and oc_account_password
    """
    authfile = None
    accounts_info = dict()
    auth_file_list = [f for f in listdir(os.path.dirname(os.path.abspath(__file__))) if isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), f)) and f in auth_files ]
    if len(auth_file_list)<0:
        print "Missing authentication configuration files: 'auth-default.conf'"
        exit(0)

    for file in auth_file_list:
        try:
            authfile = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), file), 'rb')
        except IOError:
            print "Could not read file:", auth_files

        endpoint = file.split("auth-")[1].rsplit(".")[0]

        accounts_info[endpoint] = {"oc_account_name": "", "oc_account_password": ""}
        for line in authfile:
            if line[0:len("oc_account_name = ")] == "oc_account_name = ":
                if platform.system() == "Windows":
                    accounts_info[endpoint]["oc_account_name"] = line[len("oc_account_name = ")::].rsplit('\r')[0]
                else:
                    accounts_info[endpoint]["oc_account_name"] = line[len("oc_account_name = ")::].rsplit('\n')[0]
            if line[0:len("oc_account_password = ")] == "oc_account_password = ":
                accounts_info[endpoint]["oc_account_password"] = line[len("oc_account_password = ")::].rsplit('\n')[0]

    return accounts_info

def get_deploy_configuration():
    """ This method loads the config file "deployment_architecture.csv"
    passed to the script as argument
    :return deploy_configuration with the architecture as a dict
    """
    deploy_configuration= dict()
    if os.path.exists("deployment_architecture.csv"): # update repo to get the new "deployment_architecture.csv"
        os.remove("deployment_architecture.csv")
    import wget
    wget.download(deployment_config_link)# get the deployment file

    deploy_file = [f for f in listdir(os.path.dirname(os.path.abspath(__file__))) if isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), f)) and f=='deployment_architecture.csv' ][0]
    if deploy_file == "":
        print "Missing deployment configuration file: 'deployment_architecture.csv'"
        exit(0)

    if deploy_file[-3:] == "csv":
        try:
            csvfile = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), deploy_file), 'rb')
            deploy_configuration = csv.DictReader(csvfile)
        except IOError:
            print "Could not read file: ", deploy_file
    else:
        print "Wrong file format: ", deploy_file
        exit(0)

    return deploy_configuration

def load_config_files(auth_files=["auth-default.conf"], is_update=False):
    """ This method loads the config file "auth-default.conf" passed to
    the script as argument and the "deployment_architecture.csv"
    :return deploy_configuration with the architecture as a dict
    and account_info as a dict with oc_account_name and oc_account_password
    """

    deploy_configuration = get_deploy_configuration()

    accounts_info = get_occ_credentials(auth_files)

    return deploy_configuration, accounts_info

def parse_cmdline_args():
    parser = argparse.ArgumentParser(description='''Smashbox - This is a framework for end-to-end testing the core storage functionality of owncloud-based service installation ''')
    parser.add_argument("--auth",
                        nargs='+',
                        help='accounts info config file',
                        default=["auth-default.conf"])
    return parser

if __name__== '__main__':
    try:
        parser = parse_cmdline_args()
        args = parser.parse_args()
    except Exception as e:
        sys.stdout.write("Check command line arguments (%s)" % e.strerror)

    is_update = False
    current_config = dict()

    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smashbox")): # check if the current script execution is update? or now setup? (no smashbox folder in new setups)
        is_update = True

    remove_old_folders()

    # 1) Load the configutation files ( get updated deployment_architecture if is_update)
    deployment_config, accounts_info = load_config_files(args.auth, is_update)
    # 2) Setup smashbox and oc_client with the new/updated "deployment_architecture" and "auth" configuration
    current_config = setup_config(deployment_config, accounts_info, is_update)
    # 3) Check smashbox installation
    smash_check()
    # 4) Publish new deployment architecture info into kibana dashboard
    publish_deployment_state(current_config)
    # 5) install cron job
    create_cron_job()
    # 6) Run smashbox
    endpoints_list = current_config["oc_endpoints"].split(",")
    # run all tests per endpoint
    for endpoint in endpoints_list:
        smash_run(endpoint)







