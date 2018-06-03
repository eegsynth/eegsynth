This is the patch used for the Wayob installation at Galleri Fagerstedt.
See this [link](http://www.perhuttner.com/wayob/) for details.

The technical implementation of EEGsynth consisted of a Raspberry Pi that was configured to start all modules upon boot. To allow remote monitoring and reconfiguration, TeamViewer was installed. Furthermore, a regular cron job was running to keep ngrok running and to pull and execute optional commands from a bash script hosted on a remote web server.

The crontab looks like this
```
@reboot            ~/bin/startup.sh   > ~/bin/startup.log   2>&1
0,15,30,45 * * * * ~/bin/regularly.sh > ~/bin/regularly.log 2>&1
```

Note that at the time we were not yet using the patches directory. This patch and documentation have been reconstructed to match the setup used back then.
