try:
    from dns import query
    from dns import message
    from dns import rdatatype
    from dns import rdataclass
    from dns import resolver
    from dns.resolver import Timeout
    from dns.resolver import NXDOMAIN
except (NameError, ImportError), e:
    print "dnspython is required, please install. " \
          "dns module disabled"
else:

    import sys
    import re
    import socket
    from random import random
    from select import select
#    from mhelper.system import time
    import time

    if sys.platform == 'win32':
        if sys.version_info.major == 2:
            import _winreg
        if sys.version_info.major == 3:
            import winreg
    elif sys.platform == 'cygwin':
        import cygwinreg as winreg
        from cygwinreg import w32api

#    from mhelper.system import time
#    from mhelper.util.statistics import identity
#    from util.statistics import identity

    def get_nameservers(force_update=False):
        if force_update:
            resolver.default_resolver = resolver.Resolver()
        return resolver.get_default_resolver().nameservers

    # dummy resolver object for name resolution
    _resolver = resolver.Resolver(configure=False)
    _resolver.reset()
    def resolve(qname, where=get_nameservers, timeout=5.0, retries=3,
                rdtype=rdatatype.A, rdclass=rdataclass.IN, tcp=False,
                source=None, raise_on_no_answer=True, source_port=0):
        global _resolver
        rc = 'FAIL'
        answer = None
        nameserver = None
        for nameserver in where:
            _resolver.timeout = timeout
            answer = None
            try:
                _resolver.nameservers = [nameserver]*retries
                answer = _resolver.query(qname, rdtype, rdclass, tcp, source,
                                         raise_on_no_answer, source_port)
                rc = 'OK'
                break
            except NXDOMAIN, e:
                print >>sys.stderr, type(e), e
                # carry NXDOMAIN info along (overwritten when correct answer is
                # found)
                rc = 'NXDOMAIN'
            except Timeout:
                print >>sys.stderr, type(e), e
                # only carry TIMEOUT info along if rc is FAIL
                if rc == 'FAIL':
                    rc = 'TIMEOUT'
            except Exception, e:
                print >>sys.stderr, type(e), e
        return (answer, nameserver), rc


    def udp_timing(qname, where, rdtype=rdatatype.A,
                   rdclass=rdataclass.IN, timeout=5.0, port=53, af=None,
                   source=None, source_port=0, ignore_unexpected=False,
                   one_rr_per_rrset=False):
        rc = 'FAIL'
        q = message.make_query(qname, rdtype, rdclass)
        wire = q.to_wire()
        (af, destination, source) = query._destination_and_source(af, where,
                                                                  port, source,
                                                                  source_port)
        s = socket.socket(af, socket.SOCK_DGRAM, 0)
        try:
            expiration = query._compute_expiration(timeout)
            s.setblocking(0)
            if source is not None:
                s.bind(source)
            query._wait_for_writable(s, expiration)
            t1 = time()
            s.sendto(wire, destination)
            while 1:
                query._wait_for_readable(s, expiration)
                (wire, from_address) = s.recvfrom(65535)
                t2 = time()
                if from_address == destination or \
                   (dns.inet.is_multicast(where) and \
                    from_address[1] == destination[1]):
                    rc = 'OK'
                if not ignore_unexpected:
                    rc = 'UnexpectedSource'
                break
        finally:
            s.close()
        r = message.from_wire(wire, keyring=q.keyring, request_mac=q.mac,
                              one_rr_per_rrset=one_rr_per_rrset)
        if not q.is_response(r):
            rc = 'BadResponse'

        return (r, q, t1, t2), rc


    def address_from_answer(answer, filterby=[rdatatype.A, rdatatype.AAAA]):
        address = []
        rc = 'FAIL'
        for a in answer:
            if a.rdtype in filterby :
                if a.address:
                    address.append(a.address)
                    rc = 'OK'
        return address, rc

    '''
    def distance_to_resolver(resolver, count=3, func=identity):
        qname = "%f-%f.%s" % (time(), random(), 'glbt.net.t-labs.tu-berlin.de')
        result = []
        rc = None
        # make sure the cache is hot. dirty, should check TTL (which is
        # initially 10s) to see if it actually is a cache hit
        # TODO: threshhold of failed resolutions until we declare a DNS non working
        resolve(qname, [resolver])
        for i in range(count):
            try:
                (a, q, t1, t2), _rc = udp_timing(qname, resolver)
                result.append((t2-t1))
                rc = 'OK'
            except Exception, e:
                result.append(-1)
        if not rc:
            result = []
            rc = 'FAIL'
        return func(result), rc
    '''
    _dns_domains = ["glbt.net.t-labs.tu-berlin.de",
                    "glbt.ohohlfeld.com",
                    #"segelfluglehrer.ohohlfeld.com",
                    #"test.muehlbauer.name",
                    #"glbt.lostland.de",
                    #"glbt.larp-waffenschmiede.de",
                    #"glbt.shadyhunters.de",
                    #"glbt.designarama.org",
                   ]

    def discover_external_resolver_ip(resolver, domains=_dns_domains, count=5,
                                      timeout=2.0):
        results = dict()
        rc = 'FAIL'
        for domain in domains:
            lcount = 0
            while lcount < count:
                try:
                    qname = "%f-%f.%s" % (time(), random(), domain)
                    (a, q, t1, t2), _rc = udp_timing(qname, resolver, timeout=timeout)
                    for record in a.answer:
                        for item in record.items:
                            ip = item.to_text()
                            if not ip in results:
                                results[ip] = []
                                lcount = 0
                            results[ip].append((t1,t2))
                            rc = 'OK'
                except Exception, e:
                    print >>sys.stderr, resolver, domain, type(e), e
                lcount += 1
        return results, rc

    def discover_multiple_external_resolver_ip(resolvers=get_nameservers(),
                                               domains=_dns_domains, count=5,
                                               timeout=2.0):
        results = dict()
        rc = dict()
        for resolver in resolvers:
            results[resolver] = dict()
            rc[resolver] = 'FAIL'
            for domain in domains:
                lcount = 0
                while lcount < count:
                    try:
                        qname = "%f-%f.%s" % (time(), random(), domain)
                        (a, q, t1, t2), _rc = udp_timing(qname, resolver,
                                                         timeout=timeout)
                        for record in a.answer:
                            for item in record.items:
                                ip = item.to_text()
                                if not ip in results[resolver]:
                                    results[resolver][ip] = []
                                    lcount = 0
                                    rc[resolver] = 'OK'
                                results[resolver][ip].append((t1,t2))
                    except Exception, e:
                        print resolver, domain, type(e), e
                    lcount += 1
        return results, rc

    class pdns_timeout(Exception):
        pass

    #####################################################################


    class pdns(object):

        min_intervall = 0.01
        min_burst_intervall = 0.1

        def __init__(self, timeslice=1, max_queries_per_timeslice=100,
                     max_outstanding=100, timeout=5.0, max_retries=3,
                     handle_raw_func=None, handle_reply_func=None):
            self.sockets = dict()
            self.outstanding_queries = dict()
            self.max_outstanding = max_outstanding
            self.timeslice = timeslice
            self.max_queries_per_timeslice = max_queries_per_timeslice
            self.timeout = timeout
            self.max_retries = max_retries
            self.interval =  float(timeslice) / max_queries_per_timeslice
            # custom handler functions
            if handle_raw_func:
                self._handle_raw = handle_raw_func
            if handle_reply_func:
                self._handle_reply = handle_reply_func
            # we wait between the queries only if the interval is >= 10ms,
            # otherwise burst the queries in 10ms intervals
            self.burst = None
            if self.interval < pdns.min_intervall:
                self.interval = pdns.min_burst_intervall
                self.burst = max_queries_per_timeslice / (timeslice / pdns.min_burst_intervall)

        def resolve(self, qnames, where, port=53, rdtype=rdatatype.A):
            print "AAAAAAAAAAAAAAAAAAAAAAAAAA"
            self.itime = time.time()   # init time: timestamp we started resolving
            self.stime = 0        # send time: smalles timestamp for this
                                  # timeslice we send a query
            self.btime = 0        # send time: smalles timestamp for this burst
            self.qtime = 0        # query time: largest timestamp we send a query
            self.qcount = 0       # queries (== names) asked
            self.rcount = 0       # reply count
            self.scount = 0       # send count
            self.scount_slice = 0 # sent count this timeslice
            self.tcount = 0       # timeout count
            self.bcount = 0       # burst count this timeslice
            for qname in qnames:
                # check if we can send more queries this timeslice
                if self.scount_slice >= self.max_queries_per_timeslice:
                    self._wait_timeslice()
                    #self._info()
                    # check if we need to re-send any query
                    self._resend_queries()
                # if there are to many outstanding queries, wait for one
                if len(self.outstanding_queries) >= self.max_outstanding:
                    self._wait_for_outstanding_query()
                # make a new query
                q = message.make_query(qname, rdtype, rdataclass.IN)
                # and send it
                self._send_query(q, where, port)
                # query count
                self.qcount += 1
                # check if a reply is waiting
                self._recv_reply()
            self._wait_for_outstanding_queries()
            #self._info()

        def _wait(self, timeout):
            if timeout < pdns.min_intervall:
                return
            _stime = time.time()
            while timeout > 0:
                # print >>sys.stderr, "waiting for", timeout
                self._recv_reply(timeout)
                # comput how long we need to wait
                timeout = timeout - (time.time() - _stime)

        def _wait_timeslice(self):
            # comput how long we need to wait
            timeout = self.timeslice - (time.time() - self.stime)
            if timeout > 0:
                self._wait(timeout)
            # reset state
            self.stime = 0
            self.btime = 0
            self.scount_slice = 0
            self.bcount = 0

        def _wait_for_outstanding_queries(self):
            while len(self.outstanding_queries):
                self._wait_for_outstanding_query()

        def _wait_for_outstanding_query(self):
            _outstanding = len(self.outstanding_queries)
            # wait for one outstanding query
            while True:
                # compute how long we wait for an answer
                timeout = self.timeout - (self.stime - time.time())
                # wait...
                self._recv_reply(self.timeout)
                # if we didn't recieve a reply, we have a timeout
                if _outstanding == len(self.outstanding_queries):
                    # let's resend all queries that are timed out
                    self._resend_queries()
                    # increase timeout counter
                    self.tcount += 1
                    # stop if there are too many timeouts
                    if self.tcount >= self.max_retries:
                        raise pdns_timeout("Timeout #%d. Timeout is %d seconds." \
                                               % (self.max_retries, self.timeout))
                else:
                    break

        def _get_socket(self, af):
            try:
                return self.sockets[af]
            except KeyError:
                self.sockets[af] = socket.socket(af, socket.SOCK_DGRAM, 0)
                return self.sockets[af]

        def _get_af_for_address(self, where, port):
            destination = (where, port)
            af = socket.AF_INET
            try:
                socket.inet_aton(where)
            except:
                try:
                    socket.inet_pton(socket.AF_INET6, where)
                    af = socket.AF_INET6
                    destination = (where, port, 0, 0)
                except:
                    pass
            return af, destination

        def _send_query(self, q, where, port):
            # see if we need to wait before sending a new query
            if self.interval:
                _interval = 0
                if self.burst:
                    if self.bcount >= self.burst:
                        _interval = time.time() - self.btime
                        self.bcount = 0
                        self.btime = 0
                        #self._info()
                    else:
                        _interval = self.interval
                else:
                    _interval = time.time() - self.qtime
                if _interval < self.interval:
                    self._wait(self.interval - _interval)
            af, destination = self._get_af_for_address(where, port)
            s = self._get_socket(af)
            print destination
            s.sendto(q.to_wire(), destination)
            self.qtime = time.time()
            # set stime
            if not self.stime:
                self.stime = self.qtime
            if not self.btime:
                self.btime = self.qtime
            self.scount += 1
            self.bcount += 1
            self.scount_slice += 1
            if not q in self.outstanding_queries:
               self.outstanding_queries[q.id] = (q, self.qtime, destination)
            else:
                self.outstanding_queries[q.id][1] =  self.qtime

        def _resend_queries(self):
            _t = time.time()
            _first = True
            for did, (q, stime, destination) in self.outstanding_queries.iteritems():
                if _t-stime>=self.timeout:
                    print >>sys.stderr, "resend", did
                    self._send_query(q, destination[0], destination[1])

        def _recv_reply(self, timeout=0):
            r, w, x = select(self.sockets.values(), [], [], timeout)
            for s in r:
                wire = s.recv(65535)
                self._handle_raw(wire)

        def _handle_raw(self, wire):
            # pass
            stime = 0
            etime = time.time()
            q = None
            address = None
            try:
                r = message.from_wire(wire)
                self.rcount += 1
                (q, stime, address) = self.outstanding_queries[r.id]
                if q.is_response(r):
                    del self.outstanding_queries[q.id]
            except Exception, e:
                print >>sys.stderr, "err", type(e), e
            self._handle_reply(q, r, stime, etime, address)

        def _handle_reply(self, q, r, stime, etime, address):
            if r:
                print 'dns_resolve_parallel: OK -1 -1', time.time(), etime - stime, address
                print r.to_text()

        def _info(self):
            # print stats
            _t = time.time() - self.itime
            _c = self.qcount/_t
            print >>sys.stderr, 'we queried %d names in %s seconds, that is %s q/s on average' % (self.qcount, _t, _c)
            print >>sys.stderr, 'we recieved %d answers so far' % (self.rcount)
            print >>sys.stderr, 'we send %d queries so far' % (self.scount)



    # TODO: subclass reslolver and add android discovery
    #class ResolverDiscovery:
    #    """ modified DNSpython """
    #    """ courtesy of dnspython """
    #    def __init__(self):
    #        self.os = mhelper.oslib.getOS()
    #        self.nameservers = ['127.0.0.1']
    #        self.info = ""
    #
    #    def get_resolvers(self, update=True):
    #        if update:
    #            self._find_resolvers()
    #        return self.nameservers, self.os
    #
    #    def _find_resolvers(self):
    #        self.info = ""
    #        self.nameservers = []
    #        if self.os == "windows":
    #            self._windows_resolver()
    #        elif self.os == "darwin":
    #            self._macos_resolver()
    #        elif self.os == "linux":
    #            self._linux_resolvers()
    #        elif self.os == "android":
    #            self._android_resolvers()
    #        else:
    #            self.info = "os %s not supported" % self.os
    #        if not self.nameservers:
    #            self.namesevers = ['127.0.0.1']
    #        else:
    #            self.info = "ok"
    #
    #    def _android_resolvers(self):
    #        import subprocess
    #        try:
    #            p1 = subprocess.Popen(['getprop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #            rc = p1.wait()
    #            if rc == 0:
    #                r_dns = re.compile('rmnet\d+\.dns\d+', re.IGNORECASE)
    #                r_ip = re.compile('\d+\.\d+\.\d+\.\d+')
    #                s = p1.stdout.read()
    #                for i in s.split('\n'):
    #                    if i:
    #                        x = i.split(':')
    #                        if r_dns.search(x[0]):
    #                            for ip in r_ip.findall(x[1]):
    #                                if not ip in self.nameservers:
    #                                    self.nameservers.append(ip)
    #        except Exception, e:
    #            self.info = str(e)
    #
    #    def _linux_resolvers(self):
    #        # add all possible DNS servers from /etc/resolv.conf
    #        try:
    #            f = open("/etc/resolv.conf", 'r')
    #        except IOError, e:
    #            self.info = str(e)
    #            return
    #        want_close = True
    #        try:
    #            for line in f.readlines():
    #                line = string.strip(line)
    #                if not line or line[0]==';' or line[0]=='#':
    #                    continue
    #                fields=string.split(line)
    #                if len(fields) < 2:
    #                    continue
    #                if fields[0]=='nameserver':
    #                    if not fields[1] in self.nameservers:
    #                        self.nameservers.append(fields[1])
    #        finally:
    #            if want_close:
    #                f.close()
    #
    #    ''' /etc/resolv.conf works fine due to backwards compatibility '''
    #    def _macos_resolver(self):
    #        self._linux_resolvers()
    #
    #    def _windows_resolver(self):
    #        try:
    #            self._read_win_registry()
    #        except Exception, e:
    #            self.info = str(e)
    #
    #
    #    def _read_win_registry(self):
    #        """Extract resolver configuration from the Windows registry."""
    #        lm = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    #        want_scan = False
    #        try:
    #            try:
    #                # XP, 2000
    #                tcp_params = _winreg.OpenKey(lm, 'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters')
    #                want_scan = True
    #            except EnvironmentError:
    #                # ME
    #                tcp_params = _winreg.OpenKey(lm, 'SYSTEM\CurrentControlSet\Services\VxD\MSTCP')
    #            try:
    #                self._config_win32_fromkey(tcp_params)
    #            finally:
    #                tcp_params.Close()
    #            if want_scan:
    #                interfaces = _winreg.OpenKey(lm, 'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces')
    #                try:
    #                    i = 0
    #                    while True:
    #                        try:
    #                            guid = _winreg.EnumKey(interfaces, i)
    #                            i += 1
    #                            key = _winreg.OpenKey(interfaces, guid)
    #                            if not self._win32_is_nic_enabled(lm, guid, key):
    #                                continue
    #                            try:
    #                                self._config_win32_fromkey(key)
    #                            finally:
    #                                key.Close()
    #                        except EnvironmentError:
    #                            break
    #                finally:
    #                    interfaces.Close()
    #        finally:
    #            lm.Close()
    #
    #    def _determine_split_char(self, entry):
    #        #
    #        # The windows registry irritatingly changes the list element
    #        # delimiter in between ' ' and ',' (and vice-versa) in various
    #        # versions of windows.
    #        #
    #        if entry.find(' ') >= 0:
    #            split_char = ' '
    #        elif entry.find(',') >= 0:
    #            split_char = ','
    #        else:
    #            # probably a singleton; treat as a space-separated list.
    #            split_char = ' '
    #        return split_char
    #
    #    def _config_win32_nameservers(self, nameservers):
    #        """Configure a NameServer registry entry."""
    #        # we call str() on nameservers to convert it from unicode to ascii
    #        nameservers = str(nameservers)
    #        split_char = self._determine_split_char(nameservers)
    #        ns_list = nameservers.split(split_char)
    #        for ns in ns_list:
    #            if not ns in self.nameservers:
    #                self.nameservers.append(ns)
    #
    #    def _config_win32_fromkey(self, key):
    #        """Extract DNS info from a registry key."""
    #        try:
    #            servers, rtype = _winreg.QueryValueEx(key, 'NameServer')
    #        except WindowsError:
    #            servers = None
    #        if servers:
    #            self._config_win32_nameservers(servers)
    #        else:
    #            try:
    #                servers, rtype = _winreg.QueryValueEx(key, 'DhcpNameServer')
    #            except WindowsError:
    #                servers = None
    #            if servers:
    #                self._config_win32_nameservers(servers)
    #
    #    def _win32_is_nic_enabled(self, lm, guid, interface_key):
    #        # Look in the Windows Registry to determine whether the network
    #        # interface corresponding to the given guid is enabled.
    #        #
    #        # (Code contributed by Paul Marks, thanks!)
    #        #
    #        try:
    #            # This hard-coded location seems to be consistent, at least
    #            # from Windows 2000 through Vista.
    #            connection_key = _winreg.OpenKey(lm, 'SYSTEM\CurrentControlSet\Control\Network\{4D36E972-E325-11CE-BFC1-08002BE10318}\%s\Connection' % guid)
    #            try:
    #                # The PnpInstanceID points to a key inside Enum
    #                (pnp_id, ttype) = _winreg.QueryValueEx(connection_key, 'PnpInstanceID')
    #                if ttype != _winreg.REG_SZ:
    #                    raise ValueError
    #                device_key = _winreg.OpenKey(
    #                    lm, r'SYSTEM\CurrentControlSet\Enum\%s' % pnp_id)
    #                try:
    #                    # Get ConfigFlags for this device
    #                    (flags, ttype) = _winreg.QueryValueEx(device_key, 'ConfigFlags')
    #                    if ttype != _winreg.REG_DWORD:
    #                        raise ValueError
    #                    # Based on experimentation, bit 0x1 indicates that the
    #                    # device is disabled.
    #                    return not (flags & 0x1)
    #                finally:
    #                    device_key.Close()
    #            finally:
    #                connection_key.Close()
    #        except (EnvironmentError, ValueError):
    #            # Pre-vista, enabled interfaces seem to have a non-empty
    #            # NTEContextList; this was how dnspython detected enabled
    #            # nics before the code above was contributed.  We've retained
    #            # the old method since we don't know if the code above works
    #            # on Windows 95/98/ME.
    #            try:
    #                (nte, ttype) = _winreg.QueryValueEx(interface_key, 'NTEContextList')
    #                return nte is not None
    #            except WindowsError:
    #                return False
    #    """ courtesy of dnspython """
