FROM debian:8

MAINTAINER Yolanda de la Hoz Simon <ydelahoz@cern.ch>

# ----- python configuration ----- #

RUN apt-get update && \
    apt-get install -y wget && \
    apt-get install -y python2.7 && \
    apt-get install -y python2.7-dev && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python2.7 get-pip.py && \
    pip install wget && \
    pip install python-crontab 
    

# ----- Install smashbox ----- #

RUN apt-get install -y git && \
    git clone https://github.com/cernbox/smashbox.git /smashbox && \
    cd /smashbox && \
    pip install -r requirements.txt && \
    apt-get install -y curl 	


# ----- Install cernbox client ----- #

RUN apt-get install -y apt-transport-https && \
    wget -q -O- https://cernbox.cern.ch/cernbox/doc/Linux/repo/Debian_8.0/Release.key | apt-key add - && \	
    sh -c "echo 'deb https://cernbox.cern.ch/cernbox/doc/Linux/repo/Debian_8.0/ /' > /etc/apt/sources.list.d/cernbox-client.list" && \
    apt-get update && \
    apt-get install -y cernbox-client && \ 
    apt-get install -y cron
	
# ----- Copy setup monitoring scripts ----- #

COPY setup.d /setup.d

# ----- Copy setup  ----- #

CMD ["/usr/bin/python2.7", "./setup.d/setup-smashbox.py"]
