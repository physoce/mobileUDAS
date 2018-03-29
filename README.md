# mobileUDAS
## mobile Underway Data Acquisition System

Data acquisition script for MLML mobile UDAS.

### Requirements

* [DateTime](https://pypi.python.org/pypi/DateTime/) module, to install with pip run ```pip install DateTime```
* [pynmea2](https://github.com/Knio/pynmea2) module, to install with pip run ```pip install pynmea2```

### Running on startup (Raspberry Pi)

Edit the crontab with the following command:

```
crontab -e
```

Add the following line (editing the path to the mobileUDAS directory if necessary):

```
@reboot python3 -u /home/pi/mobileUDAS/mobileUDAS.py > /home/pi/mobileUDAS/log.txt
```

This runs the script and also creates a log file of the output. The `python -u` command runs in unbuffered mode so that the log file is written continuously.

To send the log file output to a terminal (such as one on an external display), add an additional line:

```
@reboot /bin/sleep 20; tail -f  /home/pi/mobileUDAS/log.txt > /dev/tty1
```
This sends the output to the terminal represented by `/dev/tty1`. This terminal is the default for the PiTFT 2.2" display. 
