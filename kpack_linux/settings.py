# default package settings. You are free to fork this repo to set yours.
import socket
from komlogd.api.model.schedules import CronSchedule

# Where your data will appear in your data model
BASE_URI = '.'.join(('pkg.kpack_linux',socket.gethostname()))

# how often we update info. CronSchedule() defaults to '* * * * *' in cron format.
SCHED = CronSchedule()

