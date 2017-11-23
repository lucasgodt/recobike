#
#fields = ['id','latitude','longitude','track_id','time']
import csv   

def addLine(list fields,str filename):

    with open('r'+filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
