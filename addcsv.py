#
#fields = ['id','latitude','longitude','track_id','time']
import csv   

def addLine(fields,filename):

    with open('tmp'+filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
