import serial, time, csv
from DateTime import DateTime
from datetime import datetime as dt

#Helper Functions
def getTime():
    '''This will give us the time in unix, UTC, and local'''
    unix = time.time() #returns unix in utc
    utc = DateTime(unix,'UTC')
    local = DateTime(unix,'US/Pacific')
    utc_iso = utc.ISO8601()
    return (unix,local,utc_iso)

def getRaw(sensor):
    ''' Sequence of steps to try reading serial data from a sensor'''
    try:
        data_raw = sensor.readline().decode() # Python 3
    except:
        try:
            data_raw = sensor.readline() #Python 2
        except:
            data_raw = ''
    return data_raw
    
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

parse_scufa = False
parse_tsg = True
parse_trans = True

#Connect to each sensor via the com port its connected to..
#If you switch around the plugs, you're going to have to..
#.. update the 'ttyUSBx' value accordingly
# to find ports on Raspberry Pi: dmesg | grep tty
# need to figure out how to make these consistent
scufa_port = ''
tsg_port = '/dev/ttyUSB2'
trans_port = '/dev/ttyUSB0'

scufa_baud = 9600
tsg_baud = 38400
trans_baud = 19200

t = getTime()[1]
dateString = t.strftime('%Y%m%d-%H%M')
filename = '/home/pi/Desktop/mobileUDAS_data/'+dateString+'_UDAS.csv'
print(filename)
with open(filename,'wt') as f:
    writer = csv.writer(f,delimiter = ',')
    
    writer.writerow(['unix_time: seconds from 1970-01-01 GMT'])
    writer.writerow(['local_time: our local time in PDT'])
    writer.writerow(['utc_time: time in GMT/UTC'])
    header = ['unix_time','local_time','utc_time']
    
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

            if parse_tsg:
                try:
                    with serial.Serial(tsg_port,tsg_baud,timeout=5) as tsg:
                        tsg_data_raw = getRaw(tsg)
                        tsg_data_parsed = parseTSG(tsg_data_raw)
                        print('TSG_raw: ',tsg_data_raw)
                        print('TSG_parsed: ',tsg_data_parsed)
                except:
                    tsg_data_parsed = ['NaN','NaN','NaN','NaN']
                rowdata = rowdata+tsg_data_parsed
            
            if parse_scufa:
                try:
                    with serial.Serial(scufa_port,scufa_baud,timeout=5) as scufa:
                        scufa_data_raw = getRaw(scufa)
                        scufa_data_parsed = parseSCUFA(scufa_data_raw)
                        print('SCUFA_raw: ',scufa_data_raw)
                        print('SCUFA_parsed: ',scufa_data_parsed)
                except:
                    scufa_data_parsed = ['NaN','NaN','NaN','NaN']
                rowdata = rowdata+scufa_data_parsed
                
            if parse_trans:
                try:
                    with serial.Serial(trans_port,trans_baud,timeout=5) as trans:
                        trans_data_raw = getRaw(trans)
                        trans_data_parsed = parseTrans(trans_data_raw)
                        print('Trans_raw: ',trans_data_raw)
                        print('Trans_parsed: ',trans_data_parsed)
                except:
                    trans_data_parsed = ['NaN']
                rowdata = rowdata+trans_data_parsed
            
            writer.writerow(rowdata)
                  
    except KeyboardInterrupt:
        readloop = False
