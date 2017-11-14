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

def publish_deployment_conf():
    """
    This function publish new configuration deployment
    in kibana dashboard
    """
    return True

def smash_run():
    print '\033[94m' + "(3) Running smashbox in" +  str(socket.gethostname()) + '\033[0m'
    current_path = os.path.dirname(os.path.abspath(__file__))
    os.system(sys.executable + " " + current_path + "/smashbox/bin/smash --keep-going -a " + current_path + "/smashbox/lib/")

def install_oc_client(version):
    import wget

    if platform.system() == "linux" or platform.system() == "linux2":  # linux
        print '\033[94m' + "(1) Installing cernbox client " + version + " for linux" + '\033[0m'
        wget.download("http://cernbox.cern.ch/cernbox/doc/Linux/" + cbox_v[version][0] +".repo")
        os.rename("./" + cbox_v[version][0] +".repo", "./tmp/" + cbox_v[version][0] +".repo")
        os.system("cp ./tmp/" + cbox_v[version][0] +".repo /etc/yum.repos.d/cernbox.repo")
        os.system("yum update")
        os.system("yum install cernbox-client")

    elif platform.system() == "darwin":  # MacOSX
        print '\033[94m' + "(1) Installing cernbox client " + version + " for MAC OSX" + '\033[0m'
        wget.download("https://cernbox.cern.ch/cernbox/doc/MacOSX/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("cp ./cernbox-" + cbox_v[version][1] +"-signed.pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg")
        os.system("installer -pkg ./tmp/cernbox-" + cbox_v[version][1] +"-signed.pkg -target /")


    elif platform.system() == "Windows":  # Windows
        print '\033[94m' + "(1) Installing cernbox client " + version + " for Windows" + '\033[0m'
        wget.download("https://cernbox.cern.ch/cernbox/doc/Windows/cernbox-" + cbox_v[version][2] +"-setup.exe")
        #os.rename(os.path.join(os.getcwd(),"cernbox-" + cbox_v[version][2] +"-setup.exe"), os.path.join(os.getcwd(),"/tmp/cernbox-" + cbox_v[version][2] +"-setup.exe"))
        os.system("cernbox-" + cbox_v[version][2] +"-setup.exe /S")
        os.remove("cernbox-" + cbox_v[version][2] +"-setup.exe")

def configure_smashbox(oc_account_name,oc_account_password,oc_server,ssl_enabled):
    print '\033[94m' + "(2) Installing smashbox" + '\033[0m'
    new_smash_conf = os.path.join(os.getcwd(),"smashbox","etc","smashbox.conf")
    shutil.copyfile("auto-smashbox.conf",new_smash_conf)
    f = open(new_smash_conf, 'a')

    f.write('oc_account_name =' + '"{}"'.format(oc_account_name) + '\n')
    f.write('oc_account_password =' + '"{}"'.format(oc_account_password) + '\n')
    f.write('oc_server =' + '"{}"'.format(oc_server + "/cernbox/desktop") + '\n')

    if ssl_enabled:
        f.write('oc_ssl_enabled =' + "True" + '\n')
    else:
        f.write('oc_ssl_enabled =' + "False" + '\n')

    if platform.system() == "linux" or platform.system() == "linux2":  # linux
        location = os.popen("whereis cernboxcmd").read()
        path = "/" + location.split("cernboxcmd")[1].split(": /")[1] + "cernboxcmd --trust"
    elif platform.system() == "darwin":
        path = "/Applications/cernbox.app/Contents/MacOS/cernboxcmd --trust"
    elif platform.system() == "Windows":
        path =  "['C:\Program Files (x86)\cernbox\cernboxcmd.exe','--trust']"

    if platform.system() != "Windows":
        f.write("oc_sync_cmd =" + '"{}"'.format(path))
    else:
        f.write("oc_sync_cmd =" + path)

    f.close()


def backup_results():
    return True


def get_repo_name(repo_url):
    if (repo_url[0:len("https://github.com/")]=="https://github.com/"): #git repo
        repo_name = repo_url.split("https://github.com/")[1][:-4]
    elif (repo_url[0:len("https://gitlab.cern.ch/")] == "https://gitlab.cern.ch/"): #gitlab private repo
        repo_name = repo_url.split("https://gitlab.cern.ch/")[1][:-4]
    else:
        print "incorrect repo url or git service not supported"
        exit(0)
    return repo_name

def get_private_repo(git_url,username,token):
    import urllib2
    import base64
    import requests
    try:
        wget.download
    except:
        print 'Failed to get api request from %s' % git_url

def is_private(repo_url):
    if (repo_url[0:len("https://gitlab.cern.ch/")] == "https://gitlab.cern.ch/"):
        return True
    else:
        return False

def download_repository(repo_url,is_update):
    """ This function is a workaround for Windows
    lack of git on cmd
    """
    repo_name = get_repo_name(repo_url)

    if platform.system() == "Windows":
        if is_update:
            shutil.rmtree(repo_name)
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


def setup_python():
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



def setup_config(deployment_config, accounts_info, is_update):
    current_config = dict()
    for row in deployment_config:
        if(row["hostname"]==socket.gethostname()):
            current_config = row

    if not current_config:
        print "this host has been removed from the configuration files; please manually delete this vm"
        exit(0)
    else:
        if not is_update:
            setup_python()
            download_repository("https://github.com/cernbox/smashbox.git",is_update)
            import pip
            pip.main(['install', 'pyocclient'])

        # check owncloud client version installation
        version = os.popen("cernboxcmd --version").read()
        if(current_config["oc_client"]!=version):
            install_oc_client(current_config["oc_client"])# update version

        # configurate smashbox
        configure_smashbox(accounts_info["oc_account_name"], accounts_info["oc_account_password"], current_config["oc_server"],current_config["ssl_enabled"])
    return current_config


def load_config_file(deploy_file,auth_file):
    deploy_configuration = dict()
    accounts_info = dict()

    try:
        authfile = open(auth_file, 'rb')
    except IOError:
        print "Could not read file:", auth_file

    for line in authfile:
        if line[0:len("oc_account_name = ")] == "oc_account_name = ":
            accounts_info["oc_account_name"] = line[len("oc_account_name = ")::].split("   ")[0][:-2]
        if line[0:len("oc_account_password = ")] == "oc_account_password = ":
            accounts_info["oc_account_password"] = line[len("oc_account_password = ")::].split("   ")[0][:-2]

    if deploy_file[-3:] == "csv":
        try:
            csvfile = open(deploy_file, 'rb')
            deploy_configuration = csv.DictReader(csvfile)
        except IOError:
            print "Could not read file:", deploy_file
    else:
        print "Wrong file format:", deploy_file
        exit(0)

    return deploy_configuration, accounts_info


def parse_cmdline_args():
    parser = argparse.ArgumentParser(description='''Smashbox - This is a framework for end-to-end testing the core storage functionality of owncloud-based service installation ''')
    parser.add_argument("--repo",
                        help='git repository with the configuration file and accounts info file')
    parser.add_argument("--config",
                        help='deployment configuration file',
                        default="deployment_architecture.csv")
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

    if not (args.config and args.auth) and not (args.repo and args.auth):
        print "Missing the configurations files or git repository with them"
        parser.print_help()
        exit(0)

    elif args.repo: # In this mode it will automatically apply the deployment changes from deployment_architecture.csv
        repo_name = get_repo_name(args.repo)
        repo_folder = repo_name.split("/")[1]
        if os.path.exists(os.path.join(os.getcwd(), repo_folder)): is_update = True # it's already configurated, only apply config changes
        download_repository(args.repo,is_update)  # get new deployment config files
        config_files = [f for f in listdir(repo_folder) if isfile(join(repo_folder, f)) and f=='deployment_architecture.csv' ]
        if(len(config_files)<1):
            print "Missing configuration files: 'deployment_architecture.csv'"
            exit(0)
        else:
            deployment_config, accounts_info = load_config_file(config_files[0],args.auth)

    current_config = dict()
    if os.path.exists(os.path.join(os.getcwd(), "smashbox")) != True:
        if args.config and args.auth: # In this mode it will simply set up the machine with the deployment architecture defined in deployment_architecture.csv
            deployment_config, accounts_info = load_config_file(args.config, args.auth)

        current_config = setup_config(deployment_config, accounts_info, is_update)
        smash_run()
        if not is_update:
            # install cron job
            print '\033[94m' + "(3) Installing cron job" + '\033[0m'

            if platform.system() != "Windows":
                try:
                    from crontab import CronTab
                except ImportError:
                    print("CronTab not present. Installing crontab...")
                    os.system(sys.executable + " -m easy_install python-crontab")
                    from crontab import CronTab

                user = os.popen("echo $USER").read().split("\n")[0]
                my_cron = CronTab(user)
                current_path = os.path.dirname(os.path.abspath(__file__))
                job = my_cron.new(command=sys.executable + os.path.join(os.getcwd(), "smash-setup.py"))
                runtime = current_config['runtime'].split(":")
                job.setall(runtime[1] + runtime[0] + ' * * *')
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
    else:
        smash_run()





