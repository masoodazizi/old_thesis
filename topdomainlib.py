import dns.resolver
from dns.resolver import Resolver, NXDOMAIN, NoNameservers, Timeout, NoAnswer

# NoNameservers: No non-broken nameservers are available to answer the query.
# NoAnswer: The response did not contain an answer to the question.
# NXDOMAIN: The query name does not exist (non-existent (invalid) Internet or Intranet domain name)
# Timeout: happens when the DNS system cannot translate a domain name into an IP address (due to heavy traffic or broken DNS server)

def AAAAQuery(domain, domainList, mainctr):		
	while True:
		try:
			answer=dns.resolver.query(domain, "AAAA")

			domainList[mainctr].append(1)
			#AAAActr += 1
			AAAABool = True
			break
		except (NoAnswer):
			domainList[mainctr].append(0)
			AAAABool = False
			break
		except (NoNameservers, NXDOMAIN, Timeout):
			domainList[mainctr].append(-1)
			AAAABool = False
			break

	return AAAABool


def AAAAHostQuery(domain, domainList, mainctr):
	while True:
		try:
			answer=dns.resolver.query("www." + domain, "AAAA")
			domainList[mainctr].append(1)
			AAAAHostBool = True
			break
		except (NoAnswer):
			domainList[mainctr].append(0)
			AAAAHostBool = False
			break	
		except (NoNameservers, NXDOMAIN, Timeout):
			domainList[mainctr].append(-1)
			AAAAHostBool = False
			break			
	return AAAAHostBool


def MXQuery(domain):
	mxObjRecords = []
	mxRecords = []

	while True:
		try:
			for item in dns.resolver.query(domain, 'MX'):
				mxObjRecords.append(item)
			break
		except (NoAnswer, Timeout, NXDOMAIN, NoNameservers):
			break;
	
	for record in mxObjRecords:
		spacePos = str(record).find(' ')
		mxRecords.append(str(record)[spacePos+1:])

	return mxRecords


def AAAAMXQuery(mxRecords, domainList, mainctr):
	MXctr = 0
	for domain in mxRecords:
		while True:
			try:
				answer=dns.resolver.query(domain, "AAAA")
				MXctr += 1
				break
			except (NoNameservers, NoAnswer, NXDOMAIN, Timeout):
				break

	if (MXctr == 0):
		domainList[mainctr].append(0)
		AAAAMXBool = False
	elif (MXctr > 0):
		domainList[mainctr].append(1)
		AAAAMXBool = True

	return AAAAMXBool


def NSQuery(domain):
	nsObjRecords = []
	nsRecords = []
	
	while True:
		try:
			for item in dns.resolver.query(domain, 'NS'):
				nsObjRecords.append(item)
			break	
		except (NoAnswer, Timeout, NXDOMAIN, NoNameservers):
			break

	for record in nsObjRecords:
		spacePos = str(record).find(' ')
		nsRecords.append(str(record)[spacePos+1:])

	return nsRecords


def AAAANSQuery(nsRecords, domainList, mainctr):
	NSctr = 0
	for domain in nsRecords:
		while True:
			try:
				answer=dns.resolver.query(domain, "AAAA")
				NSctr += 1
				break
			except (NoNameservers, NoAnswer, NXDOMAIN, Timeout):
				break

	if (NSctr == 0):
		domainList[mainctr].append(0)
		AAAANSBool = False
	elif (NSctr > 0):
		domainList[mainctr].append(1)
		AAAANSBool = True

	return AAAANSBool


def domainTimeout()

	timeListFileName = "timeList.csv"
	timeListFile = open(timeListFileName,"r")
	timeList = timeListFile.readlines()
	timeListFile.close()

	timeListFinal = []
	ctr = 0
	for item in timeList:
		timeListFinal.append([])
		commaPos1 = item.find(',')
		timeListFinal[ctr].append(item[:commaPos1])
		record = item[commaPos1+1:]
		commaPos2 = record.find(',')
		timeListFinal[ctr].append(record[:commaPos2])
		record = record[commaPos2+1:]
		commaPos3 = record.find(',')
		timeListFinal[ctr].append(record[:commaPos3])
		record = record[commaPos3+1:]
		commaPos4 = record.find(',')
		timeListFinal[ctr].append(record[:commaPos4])
		record = record[commaPos4+1:]
		commaPos5 = record.find(',')
		timeListFinal[ctr].append(record[:commaPos5])
		timeListFinal[ctr].append(record[commaPos5+1:-1])
		ctr += 1


	return timeListFinal



