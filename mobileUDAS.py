import serial, time, csv
from DateTime import DateTime
from datetime import datetime as dt
import signal
import pynmea2
import os.path
from retrieve_SUNA import getSUNA

#Helper Functions
def getTime():
    '''This will give us the time in unix, UTC, and local'''
    unix = time.time() #returns unix in utc
    utc = DateTime(unix,'UTC')
    local = DateTime(unix,'US/Pacific')
    utc_iso = utc.ISO8601()
    return (unix,local,utc_iso)

def timeout(func, args=(), timeout_duration=1, default=None):
    '''
    Call a function and wait a certain amount of time before killing it.
    
    This is needed because the serial timeout is not working on Raspberry Pi.

    Modified from function by user "Alex" at:
    https://stackoverflow.com/questions/492519/timeout-on-a-function-call
    https://stackoverflow.com/users/1581090/alex
    '''

    class TimeoutError(Exception):
        pass

    def handler(signum, frame):
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler) 
    signal.alarm(timeout_duration)
    try:
        result = func(args)
    except TimeoutError as exc:
        result = default
    finally:
        signal.alarm(0)

    return result

def getRaw(sensor):
    ''' Sequence of steps to try reading serial data from a sensor'''

    # get data 
    try:
        data_raw = sensor.readline().decode() # Python 3
    except:
        try:
            data_raw = sensor.readline() #Python 2
        except:
            data_raw = ''
    return data_raw

def readData(parsefun,baud,current_port=None):
    '''
    Get raw data and parse. Scan ports if necessary.

    parsefun is a function defined below (e.g. parseTSG)
    '''
    port_prefix = '/dev/ttyUSB'

    try:
        with serial.Serial(current_port,baud,timeout=5) as sensor:
            data_raw = timeout(getRaw,sensor,timeout_duration=5)
            data_parsed = parsefun(data_raw)
        port = current_port

# Ideally the code would automatically scan for ports, but timeouts are not yet working             
# If the port is wrong, serial.readline() runs forever

##        if 'NaN' in data_parsed:
##            raise Exception('invalid data')
##
##    except Exception:
##        print('scanning ports')
##        for port_num in range(4):
##            print('port',port_num)
##            port = port_prefix+str(port_num)
##            try:
##                with serial.Serial(port,baud,timeout=5) as sensor:
##                    data_raw = timeout(getRaw,sensor,timeout_duration=5)
##                data_parsed = parsefun(data_raw)
##                break
##            except Exception:
##                pass
    except Exception:
        pass

    return data_raw,data_parsed,port
        
def parseSCUFA(raw):
    try:
        parsed = raw.split(' ')
        #print parsed
        rawFL = float(parsed[2])
        correctedFL = float(parsed[3])
        turb = float(parsed[4])
        temp = float(parsed[5][:-3])
        return [rawFL,correctedFL,turb,temp]
    except:
        print('ERROR: Invalid SCUFA Data: ',raw)
        return ['NaN','NaN','NaN','NaN']
        
def parseTSG(raw):
    try:
        parsed = raw.split(',')
        temp = float(parsed[0])
        cond = float(parsed[1])
        sal = float(parsed[2])
        return [temp,cond,sal]
    except:
        print('ERROR: Invalid TSG data: ',raw)
        return ['NaN','NaN','NaN']
    
def parseTrans(raw):
    try:
        parsed = raw.split('\t')
        ba = float(parsed[4])
        return [ba]
    except:
        print('ERROR: Invalid Trans data: ',raw)
        return ['NaN']

def readGPS(gps_port,gps_baud):
    gps_parsed = ['NaN','NaN','NaN','NaN','NaN']
    with serial.Serial(gps_port, gps_baud, timeout=1) as ser:
        for i in range(7):
            try:
                nmea_raw = ser.readline().decode() # python 3
            except:
                nmea_raw = ser.readline() # python 2
            if nmea_raw[3:6] == 'GGA':
                print(nmea_raw)
                timestr = nmea_raw[7:13]
                gps_hour = timestr[0:2]
                gps_min = timestr[2:4]
                gps_sec = timestr[4:]
                gps_time = str(gps_hour)+':'+str(gps_min)+':'+str(gps_sec)
                gps_parsed[0] = gps_time
                try:
                    nmea_parsed = pynmea2.parse(nmea_raw)
                    latdeg = int((float(nmea_parsed.lat)-float(nmea_parsed.lat)%100)/100)
                    latmin = float(nmea_parsed.lat)%100
                    londeg = int((float(nmea_parsed.lon)-float(nmea_parsed.lon)%100)/100)
                    lonmin = float(nmea_parsed.lon)%100
                    gps_parsed = [gps_time,
                                  str(latdeg),
                                  str(latmin)[0:10],
                                  str(londeg),
                                  str(lonmin)[0:10]]
                except:
                    pass

    return gps_parsed

collect_data = True

parse_scufa = False
parse_tsg = True
parse_trans = True
parse_suna = True

#Connect to each sensor via the com port its connected to..
#If you switch around the plugs, you're going to have to..
#.. update the 'ttyUSBx' value accordingly
# to find ports on Raspberry Pi: dmesg | grep tty
# need to figure out how to make these consistent


gps_port = '/dev/ttyUSB2'
scufa_port = ''
tsg_port = '/dev/ttyUSB3'
trans_port = '/dev/ttyUSB0'
suna_port = '/dev/ttyUSB1'

gps_baud = 4800
scufa_baud = 9600
tsg_baud = 38400
trans_baud = 19200
suna_baud = 57600


if collect_data is True:
    # open new output file and write header
    t = getTime()[1]
    dateString = t.strftime('%Y%m%d-%H%M')
    filename = '/home/pi/Desktop/mobileUDAS_data/'+dateString+'_UDAS.csv'
    # avoid overwriting file of same name
    for i in range(100):
        if os.path.isfile(filename):
            filename = '/home/pi/Desktop/mobileUDAS_data/'+dateString+'_UDAS-'+str(i)+'.csv'
        else:
            break
    print(filename)
    with open(filename,'wt') as f:
        writer = csv.writer(f,delimiter = ',')
        
        writer.writerow(['unix_time: seconds from 1970-01-01 GMT'])
        writer.writerow(['local_time: our local time in PDT'])
        writer.writerow(['utc_time: time in GMT/UTC'])
        writer.writerow(['gps_time: GPS time in GMT/UTC'])
        writer.writerow(['lat_deg: GPS latitude degrees'])
        writer.writerow(['lat_min: GPS latitude minutes'])
        writer.writerow(['lon_deg: GPS longitude degrees'])
        writer.writerow(['lon_min: GPS longitude minutes'])
        header = ['unix_time','local_time','utc_time',
                  'gps_time','lat_deg','lat_min','lon_deg','lon_min']
        
        if parse_tsg:
            writer.writerow(['Temperatures in degrees Celcius'])
            writer.writerow(['Conductivity in Siemems per meter (S/m)'])
            writer.writerow(['Salinity in Practical Salinity Units (PSU)'])
            header = header+['sbe_temp','sbe_cond','sbe_sal']
        if parse_scufa:
            writer.writerow(['RF: raw fluorescence in micrograms per Liter'])
            writer.writerow(['CF: temperature corrected in micrograms per Liter'])
            writer.writerow(['turb: turbidity in NTU'])
            header = header+['scufa_RF','scufa_CF','scufa_turb','scufa_temp']
        if parse_trans:
            writer.writerow(['ba: beam attenuation in 1/m'])
            header = header+['ba']
        if parse_suna:
            writer.writerow(['no3: nitrate in uM'])
            header = header+['no3']
            
            
        writer.writerow(header)

    #Loop runs until user stops it
    readloop = True
    while readloop is True:
        try:
            with open(filename,'at') as f:
                writer = csv.writer(f,delimiter = ',')
                
                t = getTime()
                print('Time: ',t)
                rowdata = [t[0],t[1],t[2]]

                gps_parsed = readGPS(gps_port,gps_baud)
                print('GPS_parsed: ',gps_parsed)
                rowdata = rowdata+gps_parsed

                if parse_tsg:
                    try:
                        tsg_data = readData(parseTSG,tsg_baud,tsg_port)
                        tsg_data_raw,tsg_data_parsed,tsg_port = tsg_data
                        print('TSG_raw: ',tsg_data_raw)
                        print('TSG_parsed: ',tsg_data_parsed)
                    except:
                        tsg_data_parsed = ['NaN','NaN','NaN','NaN']
                    rowdata = rowdata+tsg_data_parsed
                
                if parse_scufa:
                    try:
                        scufa_data = readData(parseSCUFA,scufa_baud,scufa_port)
                        scufa_data_raw,scufa_data_parsed,scufa_port = scufa_data
                        print('SCUFA_raw: ',scufa_data_raw)
                        print('SCUFA_parsed: ',scufa_data_parsed)
                    except:
                        scufa_data_parsed = ['NaN','NaN','NaN','NaN']
                    rowdata = rowdata+scufa_data_parsed
                    
                if parse_trans:
                    try:
                        trans_data = readData(parseTrans,trans_baud,trans_port)
                        trans_data_raw,trans_data_parsed,trans_port = trans_data
                        print('Trans_raw: ',trans_data_raw)
                        print('Trans_parsed: ',trans_data_parsed)
                    except:
                        trans_data_parsed = ['NaN']
                    rowdata = rowdata+trans_data_parsed
                    
                if parse_suna:
#                    try:
                    sensor = serial.Serial(suna_port,suna_baud,timeout=10)
                    nsample = 5
                    nitrate_uM,nitrogen = getSUNA(sensor,nsample)
                    suna_parsed = [nitrate_uM]
                    sensor.close()
                    print('SUNA_parsed: ',suna_parsed)
##                    except:
##                        suna_parsed = ['NaN']
                    rowdata = rowdata+suna_parsed
                
                writer.writerow(rowdata)
                      
        except KeyboardInterrupt:
            readloop = False
