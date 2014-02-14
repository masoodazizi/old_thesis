from string import *

AAAAListFileName = "AAAAList.csv"

AAAAListFile = open(AAAAListFileName,"r")
AAAAList = AAAAListFile.readlines()
AAAAListFile.close()

#AAAAListTemp  = []
AAAAListFinal = []

ctr = 0
for item in AAAAList:
	
	commaPos1 = item.find(',')
	recordTemp = item[commaPos1+1:]
	commaPos2 = recordTemp.find(',')
	AAAAListFinal.append([])
	AAAAListFinal[ctr].append(recordTemp[:commaPos2])
	recordTemp = recordTemp[commaPos2+1:]
	commaPos3 = recordTemp.find(',')
	AAAAListFinal[ctr].append(recordTemp[:commaPos3])
	AAAAListFinal[ctr].append(recordTemp[commaPos3+1:-1])	
	ctr += 1


inputDomain = raw_input ("Enter domain name to check IPv6 status: ")
domainInList = 0
for item in AAAAListFinal:
	if (item[0] == inputDomain):
		if (item[1] == str(1) and item[2] == str(1)):
			print " (++) Domain and host of \"" + item[0] + "\" are both IPv6 reachable."
		elif (item[1] == str(1)):
			print " (+) Domain \"" + item[0] + "\" is IPv6 reachable."
		elif (item[2] == str(1)):
			print " (+) Host of domain \"" + item[0] + "\" is IPv6 reachable."
		else:
			print " (-) Domain \"" + item[0] + "\" is IPv6 UNreachable."
		domainInList = 1
if (domainInList == 0):
	print " (x) Domain \"" + inputDomain + "\" is NOT in the list!"



