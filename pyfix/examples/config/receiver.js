{
    "defaults" : {
	"ConnectionType" : "acceptpr",
	"FileStorePath"  : "store",
	"HeartbeatInterval" : 30,
	"PersistRoot"       : "../persist/receive",
	"BeginString"       : "FIX.4.2"
    },
    "sessions" : {
	"SenderCompID" : "BROKER",
	"Port"         : 1666,
	"TargetCompID" : "CLIENT"
    },
    "manhole" : {
	"listenPort" : 4223,
	"passwords"  : { "admin" : "aaa" }
    },
    "webServer" : {
	"listenPort" : 8101
    },
    "nevow" : {
	"listenPort" : 8102
    }
}
