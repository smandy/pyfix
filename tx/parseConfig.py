import yaml
from pprint import pprint as pp

lines = open('tradeclient.cfg','r').read()
chunks =lines.split("\n\n")
chunks_hld = [ x.split("\n") for x in chunks]

def dictFromChunk(x):
    ret = {}
    for line in x[1:]:
        print line
        bits = line.split('=')
        if not len(bits)==2:
            print "DODGY LINE : %s" % line
            continue
        q,v = bits
        ret[q] = v
    return ret
    
chunks = [ dictFromChunk(x) for x in chunks_hld]

chunks2  = [ dictFromChunk(x) for x in chunks_hld]

#chunks2 = chunks[:]
s = { 'initiators' : { 'default' : chunks[0],
                       'sessions' : chunks[1:] },
      'receivers'  : { 'default' : chunks2[0],
                       'sessions' : chunks2[3:] }
      }

print yaml.dump_all( [s, s])

config = """
initiators:
  default: {ConnectionType: initiator, EndTime: '00:00:00', FileLogPath: log, FileStorePath: store,
    HeartBtInt: '30', ReconnectInterval: '1', SocketConnectHost: localhost, StartTime: '00:00:00',
    UseDataDictionary: N}
  sessions:
  - {BeginString: FIX.4.2, SenderCompID: CLIENT1, SocketConnectPort: '5002', TargetCompID: ORDERMATCH}
  - {BeginString: FIX.4.0, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.1, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.2, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.3, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.4, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
receivers:
  default: {ConnectionType: initiator, EndTime: '00:00:00', FileLogPath: log, FileStorePath: store,
    HeartBtInt: '30', ReconnectInterval: '1', SocketConnectHost: localhost, StartTime: '00:00:00',
    UseDataDictionary: N}
  sessions:
  - {BeginString: FIX.4.0, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.0, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.1, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.1, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.2, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.2, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.3, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.3, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.4, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}
  - {BeginString: FIX.4.4, SenderCompID: CLIENT1, SocketConnectPort: '5001', TargetCompID: EXECUTOR}"""

#from pprint import pprint as pp
#pp( yaml.load( config ) )

import quickfix as fix
ss = fix.SessionSettings()
for chunk in chunks[1:]:
    sess = chunks[0].copy()
    sess.update( chunk )

    pp(sess)
    sid = fix.SessionID( sess['BeginString'],
                         sess['SenderCompID'],
                         sess['TargetCompID'],
                         sess.get( 'SessionQualifier', '') )
    d = fix.Dictionary()
    for q,v in sess.items():
        d.setString(q, v)
    ss.set(sid, d)

print ss
    
    
    
    
    
    
    
    



