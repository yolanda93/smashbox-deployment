#!/usr/bin/python
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

# linux, macosx windows
cbox_v = {
    "2.3.3": ["centos7-cernbox","2.3.3.1807","2.3.3.1110"],
    "2.2.4": ["centos7-cernbox","2.2.4.1495","2.2.4.830"],
    "2.1.1": ["centos7-cernbox","2.1.1.1144","2.2.2.570"],
    "2.0.2": ["centos7-cernbox","2.0.2.782","2.0.2.236"],
    "1.6.4": ["centos7-cernbox","1.6.4.1197","1.6.4.4043"],
    "2.0.1": ["centos7-cernbox","2.0.1.747","2.0.1.203"],
    "1.7.1": ["centos7-cernbox","1.7.1.1810","1.7.1.4505"],
    "1.7.2": ["centos7-cernbox","1.7.2.2331","1.7.2.5046"],
    "1.8.3": ["centos7-cernbox","1.8.3.510","1.8.3.499"],
}

####### monitoring utilities to publish deployment state in kibana ############################################################

def get_monitoring_host():
    """
    Get kibana parameters defined in smashbox.conf
    """
    smashbox_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)),"smashbox","etc","smashbox.conf")

    conf_file = open(smashbox_conf, 'r')

    for line in conf_file:
        if line[0:len("kibana_monitoring_host = ")] == "kibana_monitoring_host = ":
            monitoring_host = line[len("kibana_monitoring_host = ")::].rsplit('\n')[0].replace('"', '')
        if line[0:len("kibana_monitoring_port = ")] == "kibana_monitoring_port = ":
            monitoring_port = line[len("kibana_monitoring_port = ")::].rsplit('\n')[0].replace('"', '')

    return monitoring_host,monitoring_port


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
    repo_name=""

    for line in git_config:
        if line[0:len("	url = ")] == "	url = " :
            return line[len("	url = ")::].split('\n')[0]

this_repo = this_repo_name()
print this_repo

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

    if platform.system() == "Windows":
        import wget
        wget.download("http://github.com/" + repo_name + "/archive/master.zip")
        import zipfile
        zip_ref = zipfile.ZipFile(os.path.join(os.getcwd(),repo_name.split("/")[1] + "-master.zip"), 'r')
        zip_ref.extractall(".")
        zip_ref.close()
        os.rename(repo_name.split("/")[1] +"-master", repo_name.split("/")[1])
        os.remove(repo_name.split("/")[1] +"-master.zip")

    else: # use git
        if is_update:
            os.system("git pull " + os.path.join(os.getcwd(),repo_name.split("/")[1]))
        else:
            os.system("git clone " + "http://github.com/" + repo_name + ".git")


####### utilities for this installation script #################################################################################

def smash_run():
    print '\033[94m' + "Running smashbox in " +  str(socket.gethostname()) + '\033[0m'
    current_path = os.path.dirname(os.path.abspath(__file__))
    cmd = sys.executable + " " + current_path + "/smashbox/bin/smash " + current_path + "/smashbox/lib/test_nplusone.py"
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        print "Smashbox installation failed: Non-zero exit code after running smashbox"

    os.system(sys.executable + " " + current_path + "/smashbox/bin/smash --keep-going " + current_path + "/smashbox/lib/") # run smashbox normally


def install_oc_client(version):
    import wget

    if platform.system() == "linux" or platform.system() == "linux2":  # linux
        print '\033[94m' + "Installing cernbox client " + version + " for linux" + '\033[0m'
        wget.download("http://cernbox.cern.ch/cernbox/doc/Linux/" + cbox_v[version][0] +".repo")
        os.rename("./" + cbox_v[version][0] +".repo", "./tmp/" + cbox_v[version][0] +".repo")
        os.system("cp ./tmp/" + cbox_v[version][0] +".repo /etc/yum.repos.d/cernbox.repo")
        os.system("yum update")
        os.system("yum install cernbox-client")

    elif platform.system() == "darwin":  # MacOSX
        print '\033[94m' + "Installing cernbox client " + version + " for MAC OSX" + '\033[0m'
        wget.download("https://cernbox.cern.ch/cernbox/doc/MacOSX/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("cp ./cernbox-" + cbox_v[version][1] +"-signed.pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("installer -pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg -target /")


    elif platform.system() == "Windows":  # Windows
        print '\033[94m' + "Installing cernbox client " + version + " for Windows" + '\033[0m'
        wget.download("https://cernbox.cern.ch/cernbox/doc/Windows/cernbox-" + cbox_v[version][2] +"-setup.exe")
        #os.rename(os.path.join(os.getcwd(),"cernbox-" + cbox_v[version][2] +"-setup.exe"), os.path.join(os.getcwd(),"/tmp/cernbox-" + cbox_v[version][2] +"-setup.exe"))
        os.system("cernbox-" + cbox_v[version][2] +"-setup.exe /S")
        os.remove("cernbox-" + cbox_v[version][2] +"-setup.exe")

def config_smashbox(oc_account_name, oc_account_password, oc_server, ssl_enabled, kibana_activity):
    print '\033[94m' + "Installing/updating smashbox" + '\033[0m'
    new_smash_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)),"smashbox","etc","smashbox.conf")
    shutil.copyfile("auto-smashbox.conf",new_smash_conf)
    f = open(new_smash_conf, 'a')

    f.write('oc_account_name =' + '"{}"'.format(oc_account_name) + '\n')
    f.write('oc_account_password =' + '"{}"'.format(oc_account_password) + '\n')
    f.write('oc_server =' + '"{}"'.format(oc_server + "/cernbox/desktop") + '\n')

    if ssl_enabled:
        f.write('oc_ssl_enabled =' + "True" + '\n')
    else:
        f.write('oc_ssl_enabled =' + "False" + '\n')

    oc_sync_path = get_oc_sync_cmd_path()
    f.write("oc_sync_cmd =" + str(oc_sync_path) + '\n')

    f.write('kibana_activity =' + '"{}"'.format(kibana_activity) + '\n')

    f.close()


def get_oc_sync_cmd_path():
    if platform.system() == "Windows":
        path = ['C:\Program Files (x86)\cernbox\cernboxcmd.exe', '--trust']
    elif platform.system() == "Linux":
        location = os.popen("whereis cernboxcmd").read()
        path = "/" + location.split("cernboxcmd")[1].split(": /")[1] + "cernboxcmd --trust"
    elif platform.system() == "Darwin":
        path = "/Applications/cernbox.app/Contents/MacOS/cernboxcmd --trust"

    return path

def backup_results():
    return True


def setup_python():
    """ Setup some needed python packages for the execution of this script
    """
    try:
        import wget
    except ImportError:
        print("wget not present. Installing wget...")
        os.system(sys.executable + " -m easy_install pycurl")
        import wget

    try:
        import urllib2
    except ImportError:
        print("wget not present. Installing urllib2...")
        os.system(sys.executable + " -m easy_install urllib2")
        import wget

    try:
        import pip
    except ImportError:
        print("pip not present. Installing pip...")
        os.system(sys.executable + " -m easy_install pip")
        import pip

    if platform.system() == "Windows":
        try:
            import pycurl
        except ImportError:
            print("Pycurl not present. Installing pycurl...")
            os.system(sys.executable + " -m easy_install pycurl")
            import pycurl


def ocsync_version(oc_sync_cmd):
    """ Return the version reported by oc_sync_cmd.
     :return a tuple (major,minor,bugfix). For example: (1,7,2) or (2,1,1)
    """
    # strip possible options from config.oc_sync_cmd
    cmd = [oc_sync_cmd[0]] + ["--version"]
    try:
        process = subprocess.Popen(cmd, shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = process.communicate()
    except WindowsError:
        return ""

    sver = stdout.strip().split()[2]  # the version is the third argument

    return tuple([int(x) for x in sver.split(".")])

def check_oc_client_installation(config):
    """ It checks owncloud client installation and it installs a new
    version (if required)
    """
    version_tuple = ocsync_version(get_oc_sync_cmd_path())
    installed_version = str(version_tuple)[1:-1].replace(", ", ".")

    if (config["oc_client"] != installed_version): # TODO: check if it is needed to unistall first previous version
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
        print "this host has been removed from the configuration files; please manually delete this vm"
        exit(0)
    else:
        if not is_update:
            setup_python()
            download_repository("https://github.com/cernbox/smashbox.git")
            import pip
            pip.main(['install', 'pyocclient'])

        check_oc_client_installation(this_host_config)

        # configurate smashbox
        config_smashbox(accounts_info["oc_account_name"], accounts_info["oc_account_password"], this_host_config["oc_server"], this_host_config["ssl_enabled"],this_host_config["kibana_activity"])

    return this_host_config


def load_config_files(auth_file="auth.conf", is_update=False):
    """ This method loads the config file "auth.conf" passed to
    the script as argument and the "deployment_architecture.csv"
    :return deploy_configuration with the architecture as a dict
    and account_info as a dict with oc_account_name and oc_account_password
    """
    deploy_configuration = dict()
    accounts_info = dict()
    deploy_file = None

    if is_update: # update repo to get the new "deployment_architecture.csv"
        if platform.system() == "Windows":
            download_repository(this_repo)
            deploy_file = os.path.join(os.getcwd(), "smashbox-deployment", "deployment_architecture.csv")
        else:
            os.system("git pull " + os.getcwd())

    if not deploy_file: # get the deployment file from the current project
        deploy_file = [f for f in listdir(os.getcwd()) if isfile(join(os.getcwd(), f)) and f=='deployment_architecture.csv' ][0]
        if deploy_file == "":
            print "Missing deployment configuration file: 'deployment_architecture.csv'"
            exit(0)

    try:
        authfile = open(auth_file, 'rb')
    except IOError:
        print "Could not read file:", auth_file

    for line in authfile:
        if line[0:len("oc_account_name = ")] == "oc_account_name = ":
            accounts_info["oc_account_name"] = line[len("oc_account_name = ")::].split('\n')[0]
        if line[0:len("oc_account_password = ")] == "oc_account_password = ":
            accounts_info["oc_account_password"] = line[len("oc_account_password = ")::].rsplit('\n')[0]

    if deploy_file[-3:] == "csv":
        try:
            csvfile = open(deploy_file, 'rb')
            deploy_configuration = csv.DictReader(csvfile)
        except IOError:
            print "Could not read file: ", deploy_file
    else:
        print "Wrong file format: ", deploy_file
        exit(0)

    return deploy_configuration, accounts_info

def parse_cmdline_args():
    parser = argparse.ArgumentParser(description='''Smashbox - This is a framework for end-to-end testing the core storage functionality of owncloud-based service installation ''')
    parser.add_argument("--auth",
                        help='accounts info config file',
                        default="auth.conf")
    return parser

if __name__== '__main__':
    try:
        parser = parse_cmdline_args()
        args = parser.parse_args()
    except Exception as e:
        sys.stdout.write("Check command line arguments (%s)" % e.strerror)

    is_update = False
    current_config = dict()

    if os.path.exists(os.path.join(os.getcwd(), "smashbox")): # check if the current script execution is update? or now setup? (no smashbox folder in new setups)
        is_update = True

    if platform.system() == "Windows":  # if windows removed the "smashbox-deploymnet" folder (this folder is incorrectly leaved after updates)
        shutil.rmtree(get_repo_name(this_repo).split("/")[1])

    # 1) Load the configutation files ( get updated deployment_architecture if is_update)
    deployment_config, accounts_info = load_config_files(args.auth, is_update)
    # 2) Setup smashbox and oc_client with the new/updated "deployment_architecture" and "auth" configuration
    current_config = setup_config(deployment_config, accounts_info, is_update)
    # 3) Run smashbox
    smash_run()
    # 4) Publish new deployment architecture info into kibana dashboard
    publish_deployment_state(current_config)



    if not is_update:
        # install cron job

        if platform.system() != "Windows":
            try:
                from crontab import CronTab
            except ImportError:
                print("CronTab not present. Installing crontab...")
                os.system(sys.executable + " -m easy_install python-crontab")
                from crontab import CronTab

            #user = os.popen("echo $USER").read().split("\n")[0]
            my_cron = CronTab("root")
            current_path = os.path.dirname(os.path.abspath(__file__))
            job = my_cron.new(command=sys.executable + os.path.join(os.getcwd(), "smash-setup.py"))
            runtime = current_config['runtime'].split(":")
            job_time = runtime[1] + " " + runtime[0] + " * * *"
            job.setall(str(job_time))
            print '\033[94m' + "Installing cron job at: " + job_time + '\033[0m'
            my_cron.write()

        else:
            import sys

            cmd = "schtasks /Create /SC DAILY /TN Smashbox /ST " + current_config[
                'runtime'] + " /TR " + sys.executable + os.path.join(os.getcwd(),
                                                                     "smash-setup.py")  # --repo https://gitlab.cern.ch/ydelahoz/smashbox-deployment-config")
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if (len(stderr) > 0):
                print "The task cannot be created on Windows - ", stderr
            else:
                print "The task has been successfully installed"






