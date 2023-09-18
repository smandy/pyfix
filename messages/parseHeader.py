from pprint import pprint as pp
import string

lines = """April 30, 2003June 18, 2003 12 FIX 4.4 with Errata 20030618- Volume 2
Tag Field Name Req'd Comments
8 BeginString Y FIX.4.4 (Always unencrypted, must be first field in message)
9 BodyLength Y (Always unencrypted, must be second field in message)
35 MsgType Y (Always unencrypted, must be third field in message)
49 SenderCompID Y (Always unencrypted)
56 TargetCompID Y (Always unencrypted)
115 OnBehalfOfCompID N Trading partner company ID used when sending messages via a third
party (Can be embedded within encrypted data section.)
128 DeliverToCompID N Trading partner company ID used when sending messages via a third
party (Can be embedded within encrypted data section.)
90 SecureDataLen N Required to identify length of encrypted section of message. (Always
unencrypted)
April 30, 2003June 18, 2003 13 FIX 4.4 with Errata 20030618- Volume 2
91 SecureData N Required when message body is encrypted.  Always immediately
follows SecureDataLen field.
34 MsgSeqNum Y (Can be embedded within encrypted data section.)
50 SenderSubID N (Can be embedded within encrypted data section.)
142 SenderLocationID N Sender's LocationID (i.e. geographic location and/or desk) (Can be
embedded within encrypted data section.)
57 TargetSubID N reserved for administrative messages not intended for a
specific user. (Can be embedded within encrypted data section.)
143 TargetLocationID N Trading partner LocationID (i.e. geographic location and/or desk)
(Can be embedded within encrypted data section.)
116 OnBehalfOfSubID N Trading partner SubID used when delivering messages via a third
party. (Can be embedded within encrypted data section.)
144 OnBehalfOfLocationID N Trading partner LocationID (i.e. geographic location and/or desk)
used when delivering messages via a third party. (Can be embedded
within encrypted data section.)
129 DeliverToSubID N Trading partner SubID used when delivering messages via a third
party. (Can be embedded within encrypted data section.)
145 DeliverToLocationID N Trading partner LocationID (i.e. geographic location and/or desk)
used when delivering messages via a third party. (Can be embedded
within encrypted data section.)
43 PossDupFlag N Always required for retransmitted messages, whether prompted by the
sending system or as the result of a resend request. (Can be embedded
within encrypted data section.)
97 PossResend N Required when message may be duplicate of another message sent
under a different sequence number. (Can be embedded within
encrypted data section.)
52 SendingTime Y (Can be embedded within encrypted data section.)
122 OrigSendingTime N Required for message resent as a result of a ResendRequest.  If data is
not available set to same value as SendingTime  (Can be embedded
within encrypted data section.)
212 XmlDataLen N Required when specifying XmlData to identify the length of a
XmlData message block. (Can be embedded within encrypted data
section.)
213 XmlData N Can contain a XML formatted message block (e.g. FIXML).   Always
immediately follows XmlDataLen field. (Can be embedded within
encrypted data section.)
See Volume 1: FIXML Support
347 MessageEncoding N Type of message encoding (non-ASCII characters) used in a
369 LastMsgSeqNumProcessed N The last MsgSeqNum value received by the FIX engine and processedby downstream application, such as trading system or order routing
system.  Can be specified on every message sent.  Useful for detecting
a backlog with a counterparty.
"""


lines2 = lines.split("\n")
lines3 = [x for x in lines2 if x and x[0] in string.digits]
headerData = []
for line in lines:
    # print line
    x = line.split()[:3]
    headerData.append(x)

if __name__ == '__main__':
    pp(headerData)
