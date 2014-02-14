from string import *
import sys
import time
from topdomainlib import *

startTime = time.time()
topListFileName = "top-1m.csv"  #"top-10.txt"
AAAAListFileName = "AAAAList.csv"
timeListFileName = "timeList.csv"
AAAActr = 0
AAAABool = False
mainctr = 0
AAAAHostctr = 0
AAAAMXctr = 0
AAAANSctr = 0
AAAAHostBool = False
www_Domainctr = 0
MX_Domainctr = 0
www_MXctr = 0
www_MX_Domainctr = 0
MX_NSctr = 0
www_MX_NS_Domainctr = 0
domainList = []
timeList = []


defaultNumCount = 10
argvNum = len(sys.argv)
if (argvNum > 1 ):
	numItr = int(sys.argv[1])
else:
	numItr = defaultNumCount


topListFile = open(topListFileName,"r")
topList = topListFile.readlines()
topListFile.close()

topListFinal = []

ctr = 0
for item in topList:
	if (ctr >= numItr):
		break
	commaPos = item.find(',')
	topListFinal.append(item[commaPos+1:-1])
	ctr += 1


ctr = 0
for domain in topListFinal:

	print mainctr , domain
	if (ctr >= numItr):
		break
 
	domainList.append([])
	domainList[mainctr].append(domain)	
	timeList.append([])
	timeList[mainctr].append(domain)
	
	looptime = time.time()	
	AAAABool = AAAAQuery(domain, domainList, mainctr)
	domain_interval = time.time() - looptime 

	looptime = time.time()
	AAAAHostBool = AAAAHostQuery(domain, domainList, mainctr)
	host_interval = time.time() - looptime	

	looptime = time.time()
	mxRecords = MXQuery(domain)
	AAAAMXBool = AAAAMXQuery(mxRecords, domainList, mainctr)
	mx_interval = time.time() - looptime

	looptime = time.time()
	nsRecords = NSQuery(domain)
	AAAANSBool = AAAANSQuery(nsRecords, domainList, mainctr)
	ns_interval = time.time() - looptime

	if (AAAABool and AAAAHostBool and AAAAMXBool and AAAANSBool):
		www_MX_NS_Domainctr += 1
	if (AAAABool and AAAAHostBool and AAAAMXBool):
		www_MX_Domainctr += 1
	if (AAAABool and AAAAMXBool):
		MX_Domainctr += 1	
	if (AAAAMXBool and AAAAHostBool):
		www_MXctr += 1
	if (AAAABool and AAAAHostBool):
		www_Domainctr += 1
	if (AAAANSBool and AAAAMXBool):
		MX_NSctr += 1
	if (AAAABool):
		AAAActr +=1
	if (AAAAHostBool):
		AAAAHostctr +=1
	if (AAAAMXBool):
		AAAAMXctr += 1
	if (AAAANSBool):
		AAAANSctr += 1		
	
	timeList[mainctr].extend([round(domain_interval, 3), round(host_interval, 3), 
							 round(mx_interval, 3), round(ns_interval, 3)])

	mainctr += 1
	ctr += 1
	time.sleep(.1)
 
#for i in timeList:
#	print i
endTime = time.time()

### Writing the list of top domain with availability of IPv6 on domain, host, mail exchnager and name server into a file
AAAAListFile = open(AAAAListFileName,"w")
AAAAListFile.writelines("#,DomainName,DomainIPv6,WWWhostIPv6,MXIPv6,NSIPv6\n")
ctr = 1
for item in domainList:
	AAAAListFile.writelines(str(ctr) + ',' + item[0] + ',' + str(item[1]) + ',' + 
							str(item[2]) + ',' + str(item[3]) + ',' + str(item[4]) + '\n')
	ctr += 1
AAAAListFile.close()

### Writing the time interval of each operation in name resloving o domain, host, mx and ns
timeListFile = open(timeListFileName,"w")
timeListFile.writelines("#,DomainName,DomainInterval,HostInterval,MXInterval,NSInterval\n")
ctr = 1
for item in timeList:
	timeListFile.writelines(str(ctr) + ',' + item[0] + ',' + str(item[1]) + ',' + 
							str(item[2]) + ',' + str(item[3]) + ',' + str(item[4]) + '\n')
	ctr += 1
timeListFile.close()


print "The number of whole domains: " + str(mainctr) 
print "The number of IPv6-enabled for:"
print "<<domains>>: " + str(AAAActr) + ' (' + str(float(AAAActr)/float(mainctr)*100) + '%)'
print "<<www-hosts>>: " + str(AAAAHostctr) + ' (' + str(float(AAAAHostctr)/float(mainctr)*100) + '%)'
print "<<mail-exchangers>>: " + str(AAAAMXctr) + ' (' + str(float(AAAAMXctr)/float(mainctr)*100) + '%)'
print "<<DNS-servers>>: " + str(AAAANSctr) + ' (' + str(float(AAAANSctr)/float(mainctr)*100) + '%)'
print "<<domains>> and <<www-hosts>> : " + str(www_Domainctr) + ' (' + str(float(www_Domainctr)/float(mainctr)*100) + '%)'
# print "<<www-hosts>> and <<mail-exchangers>>: " + str(www_MXctr) + ' (' + str(float(www_MXctr)/float(mainctr)*100) + '%)'
print "<<domains>> and <<mail-exchangers>>: " + str(MX_Domainctr) + ' (' + str(float(MX_Domainctr)/float(mainctr)*100) + '%)'
print "<<mail-exchangers>> and <<DNS-servers>>: " + str(MX_NSctr) + ' (' + str(float(MX_NSctr)/float(mainctr)*100) + '%)'
print "<<domains>> , <<www-hosts>> and <<mail-exchangers>>: " + str(www_MX_Domainctr) + ' (' + str(float(www_MX_Domainctr)/float(mainctr)*100) + '%)'
print "<<domains>> , <<www-hosts>> , <<mail-exchangers>> and <<DNS-servers>>: " + \
		str(www_MX_NS_Domainctr) + ' (' + str(float(www_MX_NS_Domainctr)/float(mainctr)*100) + '%)'
print "Resolving duration of the program is " + str(endTime - startTime) + " seconds."


# Result for 1000 records
''' 
The number of whole domains: 1000
The number of IPv6-enabled domains: 113 (11.3%)
The number of IPv6-enabled www-hosts of domains: 126 (12.6%)
The number of IPv6-enabled both www-hosts and domains: 110 (11.0%)
Resolving duration of the program is 413.887099028 seconds.
'''
