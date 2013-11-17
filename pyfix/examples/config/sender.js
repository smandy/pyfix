{
    "defaults" : { 
	"ConnectionType" : "initiator",
	"HeartbeatInterval" : 30,
	"PersistRoot" : "../persist/send",
	"Host" : "localhost"
    },
    "sessions" : [
	{ 
	    "BeginString" : "FIX.4.2",
	    "SenderCompID" : "CLIENT",
	    "TargetCompID" : "BROKER",
	    "Port"         : 1666
	}
    ],
    "manhole" : {
	"listenPort" : 2223,
	"passwords"  : { "admin" : "aaa" }
    },
    "ftpServer" : {
	"passwords" : { "admin" : "aaa" }
    },
    "webServer" : {
	"listenPort" : 8001
    },
    "nevow" : {
	"listenPort" : 8002
    }
}
