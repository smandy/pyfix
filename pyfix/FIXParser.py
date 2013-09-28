from pprint import pprint as pp
from FIXSpec import SOH, BusinessReject

FIX_PREAMBLE = "8=FIX"
FIX_PREAMBLE_FIELD_PAIR = FIX_PREAMBLE.partition("=")


class ParseException(Exception):
    pass


class FIXParser:
    def __init__(self,
                 spec,
                 cb=None,
                 on_discard=None,
                 send_data=True):
        self.fix = spec
        self.buf = ''
        if cb is None:
            self.callback = self.print_msg
        else:
            self.callback = cb

        self.on_discard = on_discard
        iter_fields = [self.fix.StandardHeader.mandatoryFields + self.fix.StandardTrailer.mandatoryFields]
        self.min_size = sum([len(x.Tag) + 2 for x in iter_fields])
        self.send_data = send_data
        self.reset()
        self.triplets = []
        self.bytes_in_buffer = 0

    @staticmethod
    def print_msg(msg, data=''):
        print "%s %s" % (msg, data )

    def reset(self):
        self.buf = ''
        self.triplets = []
        self.bytes_in_buffer = 0

    def checksum(self):
        return sum([len(x[1]) + 1 for x in self.triplets]) + len(self.buf)

    def _feed(self, data):
        self._feed(data)
        pp({"buf": self.buf,
            "triplets": self.triplets,
            "checksum": self.checksum(),
            "bytes": self.bytes_in_buffer})
        assert self.bytes_in_buffer == self.checksum(), "consistency check have %s bytes but calculate %s" % (
            self.bytes_in_buffer, self.checksum() )

    def feed(self, data):
        fix = self.fix
        self.buf += data
        self.bytes_in_buffer += len(data)

        if not self.bytes_in_buffer > self.min_size:
            return

        if not "10=" in self.buf:
            return
            #self.bytesInBuffer

        # Not even worth trying up till this point
        # partition string gives a list of 3-tuples.
        # can ensure our fields are well-formed
        # partition -> [ ( '8' ,'=','FIX' ), ( '35' ,'=','D' ) ....
        bits = [(x.partition('='), x) for x in self.buf.split(SOH)]
        if self.buf.endswith(SOH):
            # Clean message. Blat the buffer
            self.buf = ''
            # Trailing SOH needs to be consumed
            bits.pop()
        else:
            # Push trailing field back onto the buffer
            remainder = bits.pop()[1]
            #print "Pushing %s back onto buffer - start of a new field that's not been terminated yet" % remainder
            self.buf = remainder
        self.triplets += bits

        while self.triplets and not self.triplets[0][1].startswith(FIX_PREAMBLE):
            self.bytes_in_buffer -= len(self.triplets[0][1])
            if self.on_discard:
                crud = self.triplets[0][1] + SOH
                self.on_discard(crud)

            #print "Removing %s" % str(self.triplets[0])
            self.triplets.remove(self.triplets[0])

        # These turned out to be hotspots so we'll look them up outside the main loop
        msg_type_tag = fix.MsgType.Tag
        check_sum_tag = fix.CheckSum.Tag
        #sequenceNumberTag = pyfix.MsgSeqNum.Tag

        # Okay by now we've consumed all fieldpairs, put whatever isn't a pair back on the buffer,
        # and consumed everything up to the sync FIX= tag
        #fieldCollector = (headerFields, messageFields, footerFields) = ( [], [], [] )
        msg_class, start_idx, field_collector, l = None, 0, ( [], [], [] ), 0
        exception = None

        for i, ((key, sep, val), original_field) in enumerate(self.triplets):
            # Okay we took out time to complain about malformed field but
            # since it's game over we've only delayed the inevitable by a small
            # amount of time :-)
            if not sep:
                raise ParseException("Malformed field %s" % original_field)
            l += len(original_field) + 1

            # This looks like a noop but has the side effect of adding the created field to the appropriate
            # collector bucket
            fix.fieldByID[key](val, is_native=False, collector=field_collector)

            if key == msg_type_tag:
            #if isinstance( field, self.pyfix.MsgType):  -> Hotspot
                msg_class = fix.messageByID.get(val, fix.UnknownMessage)
                if msg_class == fix.UnknownMessage:
                    exception = BusinessReject("Unknown Message Type %s" % val,
                                               None,
                                               fix.SessionRejectReason.INVALIDMSGTYPE)
            elif key == check_sum_tag:
            #elif isinstance( field, self.pyfix.CheckSum): -> HotSpot
                if not msg_class:
                    # At this point all bets are off
                    self.reset()
                    raise ParseException(
                        "Have checksum but no MsgType") # Spec says we don't need to respond - malformed message
                    # At this point we know we've got something of reasonable size
                # isnative = False will force parse
                #print fieldCollector

                msg = msg_class(header_fields=field_collector[0],
                                fields=field_collector[1],
                                footer_fields=field_collector[2],
                                is_native=True)
                msg.exception = exception

                self.bytes_in_buffer -= l
                msg_class, field_collector, l = None, ( [], [], []), 0

                if self.send_data:
                    as_fix = "".join(x[1] + SOH for x in self.triplets[start_idx:i + 1])
                    if as_fix != msg.to_fix():
                        print as_fix
                        print msg.to_fix()
                else:
                    as_fix = None
                start_idx = i + 1
                self.callback(msg, data=as_fix)

        if start_idx:
            # Need to slice off everything *beyond* the index
            # otherwise end up with loads of checksums
            self.triplets = self.triplets[start_idx:]


class SynchronousParser(FIXParser):
    def __init__(self, spec):
        FIXParser.__init__(self,
                           spec,
                           cb=self.collect,
                           on_discard=self.discard,
                           send_data=False)
        self.msg = None
        self.fix_string = None
        self.discarded = ''

    def collect(self, msg, data=''):
        self.msg = msg
        self.fix_string = data

    def discard(self, x):
        self.discarded += x

    def reset(self):
        FIXParser.reset(self)
        self.msg = None
        self.fix_string = None
        self.discarded = ''

    def feed(self, data):
        FIXParser.feed(self, data)
        ret = self.msg, self.fix_string, self.discarded
        if self.msg is None:
            raise ParseException("Problem parsing message")
        self.reset()
        return ret

    parse = feed
