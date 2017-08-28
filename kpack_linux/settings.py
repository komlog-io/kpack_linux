# default package settings. You are free to fork this repo to set yours.
import socket
from komlogd.api.model.schedules import CronSchedule

# Where your data will appear in your data model
BASE_URI = '.'.join(('hosts.linux',socket.gethostname()))

# how often we upload cpu info. CronSchedule() defaults to '* * * * *' in cron format.
CPU_SCHED = CronSchedule()

# how often we upload mem info. CronSchedule() defaults to '* * * * *' in cron format.
MEM_SCHED = CronSchedule()

# how often we upload disk info. every five minutes.
DISK_SCHED = CronSchedule(minute='*/5')

