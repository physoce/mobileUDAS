import serial, time, csv
from DateTime import DateTime
from datetime import datetime as dt



#Helper Functions
def getTime():
    #This will give us the time in unix, UTC, and local
    unix = time.time() #returns unix in utc
    utc = DateTime(unix,'UTC')
    local = DateTime(unix,'US/Pacific')
    utc_iso = utc.ISO8601()
    
    return (unix,local,utc_iso)
    
    
def parseSCUFA(raw):
    try:
        parsed = raw.split(' ')
        #print parsed
        rawFL = float(parsed[2])
        correctedFL = float(parsed[3])
        turb = float(parsed[4])
        temp = float(parsed[5][:-3])
        
        return (rawFL,correctedFL,turb,temp)
    except:
        print('ERROR: Invalid SCUFA Data: ',raw)
        return ('NaN','NaN','NaN','NaN')
        
def parseTSG(raw):
    try:     
        parsed = raw.split(',')
        temp = float(parsed[0])
        cond = float(parsed[1])
        sal = float(parsed[2])
    
        return (temp,cond,sal)
        
    except:
        print('ERROR: Invalid TSG data: ',raw)
        return ('NaN','NaN','NaN')
    
def parseTrans(raw):
    try:
        parsed = raw.split('\t')
        ba = float(parsed[4])
        
    
        return ba
        
    except:
        print('ERROR: Invalid Trans data: ',raw)
        return 'NaN'

#Connect to each sensor via the com port its connected to..
#If you switch around the plugs, you're going to have to..
#.. update the 'COMX' value accordingly

#scufa = serial.Serial('COM7',9600,timeout=10)
#tsg   = serial.Serial('COM9',38400,timeout=10)
#trans = serial.Serial('COM8',19200,timeout=10)

parse_scufa = False
parse_tsg = True
parse_trans = True

scufa_port = ''
tsg_port = '/dev/ttyUSB0'
trans_port = '/dev/ttyUSB1'

scufa_baud = 9600
tsg_baud = 38400
trans_baud = 19200

if parse_scufa:
    scufa = serial.Serial(scufa_port,scufa_baud,timeout=10)
if parse_tsg:
    tsg   = serial.Serial(tsg_port,tsg_baud,timeout=10)
if parse_trans:
    trans = serial.Serial(trans_port,trans_baud,timeout=10)

t = getTime()[1]
dateString = t.strftime('%Y%m%d-%H%M')
filename = '/home/pi/Desktop/mobileUDAS_data/'+dateString+'_UDAS.csv'
print(filename)
f= open(filename,'wt')
writer = csv.writer(f,delimiter = ',')
writer.writerow(['unix_time: seconds from 1970-01-01 GMT'])
writer.writerow(['local_time: our local time in PDT'])
writer.writerow(['utc_time: time in GMT/UTC'])
writer.writerow(['Temperatures in degrees Celcius'])
writer.writerow(['Conductivity in Siemems per meter (S/m)'])
writer.writerow(['Salinity in Practical Salinity Units (PSU)'])
writer.writerow(['RF: raw fluorescence in micrograms per Liter'])
writer.writerow(['CF: temperature corrected in micrograms per Liter'])
writer.writerow(['turb: turbidity in NTU'])
writer.writerow(['ba: beam attenuation in 1/m'])

header = ['unix_time','local_time','utc_time','sbe_temp','sbe_cond',
          'sbe_sal','scufa_RF','scufa_CF','scufa_turb','scufa_temp','ba']
writer.writerow(header)


#Loop runs until user stops it
while True:
    try:
        t = getTime()
        
        try:
            scufa_data_raw = scufa.readline().decode()
        except:
            try:
                scufa_data_raw = scufa.readline()
            except:
                scufa_data_raw = ''
            
        try:
            tsg_data_raw = tsg.readline().decode()
        except:
            try:
                tsg_data_raw = scufa.readline()
            except:
                tsg_data_raw = ''    
        try:
            trans_data_raw = trans.readline().decode()
        except:
            try:
                trans_data_raw = scufa.readline()
            except:
                trans_data_raw = ''
       
        print('Time: ',t)
        print('SCUFA_raw: ',scufa_data_raw)
        print('TSG_raw: ',tsg_data_raw)
        print('Trans_raw: ',trans_data_raw)
        
        scufa_data_parsed = parseSCUFA(scufa_data_raw)
        tsg_data_parsed = parseTSG(tsg_data_raw)
        trans_data_parsed = parseTrans(trans_data_raw)
        
        print('Time: ',t)
        print('SCUFA_parsed: ',scufa_data_parsed)
        print('TSG_parsed: ',tsg_data_parsed)
        print('Trans_parsed: ',trans_data_parsed)
        writer.writerow([t[0],t[1],t[2],
                    tsg_data_parsed[0],tsg_data_parsed[1],tsg_data_parsed[2],
                    scufa_data_parsed[0],scufa_data_parsed[1],scufa_data_parsed[2],scufa_data_parsed[3],
                         trans_data_parsed])
       
       
    except KeyboardInterrupt:

        try:
            scufa.close()
        except:
            pass
        try:
            tsg.close()
        except:
            pass
        try:
            trans.close()
        except:
            pass
        
        f.close()
        
        
    
    
    
