kpack_linux
-----------

[![IRC #Komlog](https://img.shields.io/badge/irc.freenode.net-%23komlog-blue.svg)]()

kpack_linux is a [komlogd](<https://github.com/komlog-io/komlogd>) package
for monitoring and visualizing linux servers metrics.

## 1. Install

To add *kpack_linux* package to komlogd, just edit your komlogd configuration file (*komlogd.yaml*)
and add a *package block* like this one:

```
- package:
    install: https://github.com/komlog-io/kpack_linux/archive/master.zip
    enabled: yes
    venv: default
```

Then, reboot your komlogd agent.

## 2. Package Functionality

kpack_linux will upload the following info to your Komlog account:

- CPU usage information obtained from *top* command:

![cpu_info](./img/cpu_info.png)

- Memory usage information obtained from */proc/meminfo* file:

![mem_info](./img/mem_info.png)

- Disk usage information obtaind from *df* command:

![disk_info](./img/disk_info.png)


## 3. Package customization

You can modify the base uri or the commands execution schedule in
[settings.py file](/kpack_linux/settings.py). Feel free to fork this repo
and adjust them to your needs.


# Contributing and Help

Feel free to fork this repo and make your pull requests. **Thank you** for your contributions.
If you need help, please visit our IRC Channel #Komlog (Freenode) or our
[mailing lists](https://groups.google.com/forum/#!forum/komlog).

