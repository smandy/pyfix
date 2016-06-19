from pprint import pprint as pp
import string, os
from xml.dom import minidom
from datetime import datetime
from types import BooleanType, StringType
from collections import defaultdict

SOH = chr(1)
FIX_UTC_TIMESTAMP_FORMAT = "%Y%m%d-%H:%M:%S"


class MessageContent(object):
    def __init__(self, d):
        try:
            d['Position'] = int(d['Position'])
        except:
            #print "WTF?"
            #pp(d)
            d['Position'] = float(d['Position'])

        self.__dict__.update(d)
        self.field = None

    def __repr__(self):
        if not self.field:
            return "Field(%s)" % self.TagText
        else:
            return "Field(%s)" % self.field.FieldName


class SpecialField(object):
    def __init__(self):
        self.mandatory_fields = []
        self.optional_fields = []
        self.all_fields = []


class MessageIntegrityException(Exception):
    def __init__(self, message_string, msgobj):
        Exception.__init__(self, message_string)
        self.msg = msgobj


class BusinessReject(Exception):
    def __init__(self, message_string, msg, field):
        Exception.__init__(self, message_string)
        self.field = field
        self.msg = msg


class LogicError(Exception):
    pass


class FixSpec:
    pass


class Message(object):
    def __init__(self,
                 header_fields=[],
                 fields=[],
                 footer_fields=[],
                 is_native=True,
                 sort_fields=False):
        self.header_fields = header_fields
        self.footer_fields = footer_fields
        # If things get painful remove this line. Don't know how critical this is
        if sort_fields:
            fields.sort(lambda x, y: cmp(self.fieldLookup[x.__class__].Position,
                                         self.fieldLookup[y.__class__].Position))
        self.fields = fields
        # self.pyfix = None # Created in subclass
        # if not isNative:
        # self.validate()

    def __repr__(self):
        return "%s" % self.MessageName

    def to_fix(self):
        return "".join([x.to_fix() for x in self.header_fields + self.fields + self.footer_fields])

    def get_field(self, klazz):
        # XXX WTF!!!
        if 0:
            if not self.allFieldDict.has_key(klazz):
                print self.allFieldDict, klazz
                raise LogicError("%s is not a member of %s" % (klazz.FieldName, self.MessageName))

        for x in self.fields:
            if x.__class__ == klazz:
                return x
        return None

    def get_optional_field_values(self, klazz, default=None):
        f = self.get_field(klazz)
        if not f:
            return default
        else:
            return f.value

    def get_field_value(self, klazz):
        return self.get_field(klazz).value

    def get_header_field(self, klazz):
        for x in self.header_fields:
            if x.__class__ == klazz:
                return x
        return None

    def get_header_field_value(self, msgClass, default=None):
        f = self.get_header_field(msgClass)
        if f is not None:
            return f.value
        else:
            return default

    def get_fields(self, msgClass):
        return [x for x in self.fields if x.__class__ == msgClass]

    def calc_body_length(self, mutate=False):
        length = int(sum([x.size for x in self.header_fields[2:] + self.fields]))
        if mutate:
            # Okay so here we're blowing away one field but
            # want to leave fields as immutable for now
            self.header_fields[1] = self.fix.BodyLength(length)
        return length

    def calc_check_sum(self, mutate=False):
        checksum = "%03d" % (sum([x.checksum for x in self.header_fields + self.fields + self.footer_fields[:-1]]) % 256)
        if mutate:
            # Ditto - prefer to replace fields entirely rather
            # than try to mutate them in place
            self.footer_fields[-1] = self.fix.CheckSum(checksum)
        return checksum

    def check_checksum(self):
        checksum = self.calc_check_sum()
        cf_sum = self.footer_fields[-1].value
        if not checksum == cf_sum:
            raise MessageIntegrityException("CheckSum %s expected %s" % (cf_sum, checksum), self)

    def check_body_length(self):
        calc_length = self.calc_body_length()
        cf_length = self.header_fields[1].value
        if not calc_length == cf_length:
            raise MessageIntegrityException("Body Length %s expected %s" % (cf_length, calc_length ), self)

    def check_structure(self):
        if not self.get_header_field(self.fix.MsgSeqNum): raise MessageIntegrityException("No Sequence number!", self)
        if not self.header_fields: raise MessageIntegrityException("Can't calc body on msg without a header!", self)
        if not self.header_fields[0].__class__ == self.fix.BeginString: raise MessageIntegrityException(
            "First field in header has to be a begin!", self)
        if not self.header_fields[1].__class__ == self.fix.BodyLength:  raise MessageIntegrityException(
            "Second field in header must be BodyLength", self)
        if not self.footer_fields: raise MessageIntegrityException("Can't validate msg without a footer!", self)
        footer_idx = None
        for (i, f) in enumerate(self.footer_fields):
            if f.__class__ == self.fix.CheckSum:
                footer_idx = i
                break
        if footer_idx is None: raise MessageIntegrityException("Can't find checksum in trailer fields", self)

    def dump(self, prefix=''):
        lines = ["=" * 20] + self.header_fields + self.fields + self.footer_fields + ["=" * 20]
        for x in lines:
            print prefix + " " + str(x)

    def get_dump(self, prefix=''):
        lines = [str(x) for x in self.header_fields + self.fields + self.footer_fields]
        return lines

    def validate(self):
        fix = self.fix
        # These three throw MessageIntegrityException
        # we're not required by the spec to reject anything that's not 'well-formed'
        # i.e checksum, body length are okay
        self.check_body_length()
        self.check_checksum()
        self.check_structure()

        # By now we've got something well formed, anything thrown from here on in
        # we shold be able to respond to with a reasonable business reject message
        # From here on in we through BusinessRejects
        self.header_missing = fix.standard_header.mandatory_field_dict.copy()
        for field in self.header_fields:
            field.validate(fix)
            try:
                del self.header_missing[field.__class__]
            except:
                pass
                #print "Failed to delete mandatory field (%s)" % field.FieldName

        if self.header_missing:
            missing = [x.FieldName for x in self.header_missing.keys()]
            raise BusinessReject("%s Missing Mandatory Header Field (%s)" % (self, ",".join(missing) ), self,
                                 fix.SessionRejectReason.REQUIREDTAGMISSING)

        self.missing = self.mandatoryFieldDict.copy()
        for field in self.fields:
            field.validate(fix)
            if not self.allFieldDict.has_key(field.__class__):
                raise BusinessReject("Field %s does not belong to message %s" % ( field.FieldName, self.MessageName ),
                                     self,
                                     fix.SessionRejectReason.TAGNOTDEFINEDFORTHISMESSAGETYPE)

            try:
                del self.missing[field.__class__]

            except:
                ### TODO
                #print "Failed to delete mandatory field %s" % field.FieldName
                pass

        if self.missing:
            pp(self.missing)
            pp(self.__class__)

            missing = [x.FieldName for x in self.missing.keys()]
            raise BusinessReject("Missing Mandatory Fields (%s)" % ",".join(missing), self,
                                 fix.SessionRejectReason.REQUIREDTAGMISSING)

        self.footer_missing = fix.standard_trailer.mandatory_field_dict.copy()
        for field in self.footer_fields:
            field.validate(fix)
            try:
                del self.footer_missing[field.__class__]
            except:
                pass
                #print "Failed to delete mandatory field (%s)" % field.FieldName
        if self.footer_missing:
            missing = [x.FieldName for x in self.footer_missing.keys()]
            raise BusinessReject("%s Missing Mandatory Trailer Field (%s)" % (self, ",".join(missing) ), self,
                                 fix.SessionRejectReason.REQUIREDTAGMISSING)


class UnknownMessage(Message):
    MessageName = "UnknownMessage"


class FieldValueException(Exception):
    pass


class ImmutableException(Exception):
    pass


class Field(object):
    __slots__ = ['value', 'fix_value']

    def __init__(self, value, is_native=True, collector=None):
        self.value = None
        self.exception = None
        # We'll catch anything during construction
        # ( this will be called from the parsed).
        # the main protocol will call 'validate' on the message
        if is_native:
            self.value = value
            try:
                self.native2fix()
            except Exception, e:
                self.exception = e
        else:
            # Okay fairs fair if you pass non-string to nonnative
            # you don't deserve any sympathy :-)
            assert type(value) == StringType
            self.fix_value = value
            try:
                self.fix2native()
            except Exception, e:
                self.exception = e
                #if not self.validate():
                #    raise FieldValueException("Failed Validation on %s <%s> %s" %
                #                              (self.FieldName, str( self.__class__.Type ) , self.__class__.__bases__[0] ) )
        if collector:
            collector[self.collector_index].append(self)

        # Amortise the checksum calculation. The field will have done
        # the majority of the checksum/size calculation at class
        # creation time
        self.size = len(self.Tag) + 2 + len(self.fix_value)
        self.checksum = self.OrdWithoutFixValue
        for x in self.fix_value:
            self.checksum += ord(x)
        self.frozen = True

    #def __setattr__(self, attr, value):
    #    if 'frozen' in self.__dict__:
    #        raise ImmutableException( "Fields can't be modified")
    #    else:
    #        super.__setattr__(self, attr, value)

    def get_fix_value(self):
        if self.fix_value:
            return self._fix
        else:
            return self.valueToFix(self)

    def fix2native(self):
        self.value = self.fix_value

    def __eq__(self, rhs):
        return rhs.__class__ == self.__class__ and rhs.value == self.value

    def __hash__(self):
        return hash(self.to_fix())

    def native2fix(self):
        self.fix_value = str(self.value)

    def validate(self, fix):

        if hasattr(fix, 'SessionRejectReason'):
            bad_field_value = fix.SessionRejectReason.VALUEISINCORRECT
        else:
            bad_field_value = None

        if self.exception:
            raise BusinessReject("Bad Value for %s : %s" % (self,
                                                            self.exception.message),
                                 self,
                                 bad_field_value)

        try:
            ret = self._validate()
        except Exception, e:
            raise BusinessReject("Bad Value for %s : %s" % (self,
                                                            e.message),
                                 self,
                                 bad_field_value)
            #print "Ret is %s" % ret
        if not ret:
            raise BusinessReject("Invalid value for %s (%s vs %s)" % (self,
                                                                      self.value,
                                                                      self.fix_value),
                                 self,
                                 fix.SessionRejectReason.VALUEISINCORRECT)

    def _validate(self):
        return self.value is not None

    def __repr__(self):
        return "%s(%s->%s)" % ( self.FieldName, self.Tag, self.fix_value )

    def to_fix(self):
        return "".join([self.Tag, '=', self.fix_value, SOH])


class BooleanField(Field):
    def fix2native(self):
        self.value = {'Y': True,
                      'N': False}.get(self.fix_value, None)

    def _validate(self):
        return type(self.value == BooleanType) and self.fix_value in "YN"

    def native2fix(self):
        if self.value:
            self.fix_value = "Y"
        else:
            self.fix_value = "N"


class IntegerField(Field):
    def fix2native(self):
        self.value = int(self.fix_value)

    def _validate(self):
        return int(self.value) == self.value


class FloatField(Field):
    def fix2native(self):
        self.value = float(self.fix_value)

    def _validate(self):
        return float(self.value) == self.value


class CharField(Field):
    def _validate(self):
        return type(self.value) == StringType and len(self.value) == 1 and len(self.fix_value) == 1


class EnumInstance(CharField):
    pass


class EnumBuilder(object):
    def __init__(self):
        self.instance_class = None
        self.dicts = []


def weakAssert(clause, s):
    if not clause:
        raise Exception(s)


class EnumField(CharField):
    def __init__(self, value, is_native=False, collector=None):
        CharField.__init__(self, value, is_native, collector)

    def _validate(self):
        if not self.__class__.lookupByValue.has_key(self.value):
            raise Exception("invalid enum value %s" % self.value)
        return True


class UTCTimeStampField(Field):
    def fix2native(self):
        # NB Python 2.6 supports microseconds in 'strftime' formats so might be worth
        # revisiting this
        # NB The strptime calls were a hotspot when I profiled so have implemented a quicker
        # parse of a UTC timestAmpvs-

        s = self.fix_value.split('.')[0]
        args = [int(x) for x in s[:4], s[4:6], s[6:8], s[9:11], s[12:14], s[15:17]]
        self.value = datetime(*args)

    def native2fix(self):
        self.fix_value = ''
        self.fix_value = self.value.strftime(FIX_UTC_TIMESTAMP_FORMAT)

    def _validate(self):
        return type(self.value) == datetime

    def __repr__(self):
        return "%s(%s)" % (self.FieldName, self.fix_value)


def strip_text_nodes(node_list):
    ret = [x for x in node_list if not x.nodeType == minidom.Node.TEXT_NODE]
    return ret


def parse_msg_type(node):
    ret = {}
    children = strip_text_nodes(node.childNodes)
    dodgy = False
    for child in children:
        if not len(child.childNodes) == 1:
            dodgy = True
            continue
        node_name = child.nodeName
        assert not ret.has_key(node_name)
        ret[node_name.encode('utf-8')] = child.childNodes[0].data.encode('utf-8')

    if dodgy:
        # print "Skipping malformed field %s" % ret
        return None
    return ret


def get_dictionaries_from_file(fn, nodeName):
    d = minidom.parse(fn)
    dr = d.getElementsByTagName("dataroot")
    message_type_nodes = [x for x in dr[0].childNodes if
                          x.nodeType == minidom.Node.ELEMENT_NODE and
                          x.nodeName == unicode(nodeName)]
    dictionaries = [parse_msg_type(x) for x in message_type_nodes]
    ret = [x for x in dictionaries if x]
    return ret


def make_string(s):
    return "".join([x for x in s if x in string.ascii_letters])


import re

bracketRe = re.compile("(.*)\(.*\).*")


def parse_description(x):
    x = x.upper()
    match = bracketRe.match(x)
    if match:
        return make_string(match.groups()[0])
    else:
        return make_string(x)


# Map FIX Field type to our Field validators
subClasses = {'UTCTimestamp': UTCTimeStampField,
              'Length': IntegerField,
              'Amt': IntegerField,
              ' char': CharField,
              'char': CharField,
              'float': FloatField,
              'PriceOffset': FloatField,
              'Boolean': BooleanField,
              'Price': FloatField,
              'Qty': IntegerField,
              'SeqNum': IntegerField,
              'int': IntegerField,
              'Quantity': IntegerField}


from os.path import dirname as opdn, join as opj

xmlLocation = opj( opdn( opdn( __file__)), 'xml')
print "Xml location is %s" % xmlLocation

def parse_specification(version="FIX.4.2",
                        file_root= xmlLocation ):
    fix = FixSpec()
    fix.version = version
    version_root = os.path.join(file_root, version)
    files = ['MsgType', 'Fields', 'MsgContents', 'Enums']
    msg_types, fields, msg_content, enums = \
        [get_dictionaries_from_file(os.path.join(version_root, "%s.xml" % x), x) for x in files]

    message_class_lookup = {}
    for d in msg_types:
        class_name = make_string(d['MessageName'])
        # These will be populated once we've got the message contents
        class_dict = d.copy()
        class_dict['mandatoryFields'] = []
        class_dict['optionalFields'] = []
        class_dict['allFields'] = []
        # Using attributes of our new class will show it's working
        #print d
        message_class_lookup[d['MsgID']] = (class_name, class_dict)
        #cls = type( klazzName, ( Message, ), klazzDict )

    print "Generating classes for pyfix fields ..."

    enum_lookup = defaultdict(lambda: EnumBuilder())
    for d in enums:
        tag = d['Tag']
        b = enum_lookup[tag]
        #inst = CharField( d['Enum'] )
        #b.desc.append( "%s = %s" % ( value, d['Description']) )
        b.dicts.append(d)

    field_by_name, field_by_id = {}, {}
    for f in fields:
        #pp( vars(f) )
        class_name = make_string(f['FieldName'])
        class_dict = f
        class_dict['TagEquals'] = f['Tag'] + "="
        class_dict['collectorIndex'] = None
        class_dict['OrdWithoutFixValue'] = sum([ord(x) for x in class_dict['TagEquals'] + SOH])
        class_dict['__doc__'] = f['Desc']

        is_enum = False
        if enum_lookup.has_key(f['Tag']):
            is_enum = True
            klazz = CharField
        elif subClasses.has_key(f['Type']):
            klazz = subClasses[f['Type']]
        else:
            klazz = Field

        cls = type(class_name, (klazz,), class_dict)

        if is_enum:
            builder = enum_lookup[f['Tag']]
            builder.instance_class = cls

        field_by_name[cls.FieldName] = cls
        field_by_id[cls.Tag] = cls

    # Fix up our enumerations.
    for q, builder in enum_lookup.items():
        cls = builder.instance_class
        lookup_by_description = {}
        lookup_by_value = {}
        description_for_field = {}
        desc = []
        for d in builder.dicts:
            inst = cls(d['Enum'])
            pd = parse_description(d['Description'])
            lookup_by_description[pd] = inst
            lookup_by_value[d['Enum']] = inst
            description_for_field[inst] = pd
            desc.append("%s = %s" % (d['Enum'], d['Description'] ))

        setattr(cls, 'lookupByDesc', lookup_by_description)
        setattr(cls, 'lookupByValue', lookup_by_value)
        setattr(cls, 'descriptionForField', description_for_field)
        for q, v in lookup_by_description.items():
            setattr(cls, q, v)

    for q, builder in enum_lookup.items():
        cls = builder.instance_class
        cls.__bases__ = (EnumField,)

    ################################################################################
    # MSG CONTENTS
    ################################################################################

    print "Generating message content classes ..."

    content_by_message_id = defaultdict(lambda: SpecialField())

    for x in msg_content:
        obj = MessageContent(x)
        target_message_id = x['MsgID']
        target_field_id = x['TagText']

        target = content_by_message_id[target_message_id]
        assert x['Reqd'] in ['0', '1'], "Required field expected string zero or one"
        if x['Reqd'] == '0':
            target.optional_fields.append(obj)
        else:
            target.mandatory_fields.append(obj)
        target.all_fields.append(obj)

        if not field_by_id.has_key(target_field_id):
            #print "Couldn't find field %s continuing %s"  % (targetFieldID, x)
            continue

        target_field = field_by_id[target_field_id]
        obj.field = target_field
        target_field.collector_index = 1

    # Header/Trailer stuff didn't seem to be immediately available
    # from the XML file so parsed them up from the PDFs

    header_data = [['8', 'BeginString', 'Y'],
                   ['9', 'BodyLength', 'Y'],
                   ['35', 'MsgType', 'Y'],
                   ['49', 'SenderCompID', 'Y'],
                   ['56', 'TargetCompID', 'Y'],
                   ['115', 'OnBehalfOfCompID', 'N'],
                   ['128', 'DeliverToCompID', 'N'],
                   ['90', 'SecureDataLen', 'N'],
                   ['91', 'SecureData', 'N'],
                   ['34', 'MsgSeqNum', 'Y'],
                   ['50', 'SenderSubID', 'N'],
                   ['142', 'SenderLocationID', 'N'],
                   ['57', 'TargetSubID', 'N'],
                   ['143', 'TargetLocationID', 'N'],
                   ['116', 'OnBehalfOfSubID', 'N'],
                   ['144', 'OnBehalfOfLocationID', 'N'],
                   ['129', 'DeliverToSubID', 'N'],
                   ['145', 'DeliverToLocationID', 'N'],
                   ['43', 'PossDupFlag', 'N'],
                   ['97', 'PossResend', 'N'],
                   ['52', 'SendingTime', 'Y'],
                   ['122', 'OrigSendingTime', 'N'],
                   ['212', 'XmlDataLen', 'N'],
                   ['213', 'XmlData', 'N'],
                   ['347', 'MessageEncoding', 'N'],
                   ['369', 'LastMsgSeqNumProcessed', 'N']]

    trailer_data = [['93', 'SignatureLength', 'N'],
                    ['89', 'Signature', 'N'],
                    ['10', 'CheckSum', 'Y']]

    def index_fields(data, collector_index):
        ordinal = 0
        field_to_ordinal = {}
        mandatory_fields = []
        optional_fields = []
        all_field_dict = {}
        mandatory_field_dict = {}
        optional_field_dict = {}

        for tagNumber, MessageName, mandatory in data:
            if not field_by_name.has_key(MessageName):
                print "Skipping %s %s" % (MessageName, version)
                continue
            tmpField = field_by_name[MessageName]
            assert tmpField is not None, "Can't find %s" % MessageName
            tmpField.collector_index = collector_index
            assert mandatory in 'YN'
            if mandatory == 'Y':
                mandatory_fields.append(tmpField)
                mandatory_field_dict[tmpField] = None
            else:
                optional_fields.append(tmpField)
                optional_field_dict[tmpField] = None
            all_field_dict[tmpField] = None
            field_to_ordinal[tmpField] = ordinal
            ordinal += 1
        return type('ret', (Message,), locals())

    standard_header = index_fields(header_data, 0)
    standard_trailer = index_fields(trailer_data, 2)

    message_by_name, message_by_id = {}, {}
    for msgID, n_d in message_class_lookup.items():
        (class_name, class_dict) = n_d
        field_holder = content_by_message_id[msgID]

        for field in field_holder.mandatory_fields:
            assert field is not None

        for field in field_holder.optional_fields:
            assert field is not None

        class_dict['fix'] = fix
        class_dict['MessageName'] = class_name
        class_dict['mandatoryFields'] = field_holder.mandatory_fields
        class_dict['optionalFields'] = field_holder.optional_fields
        class_dict['allFields'] = field_holder.all_fields
        class_dict['mandatoryFieldDict'] = dict([(x.field, None) for x in field_holder.mandatory_fields[1:-1]])
        class_dict['optionalFieldDict'] = dict([(x.field, None) for x in field_holder.optional_fields])
        d = class_dict['mandatoryFieldDict'].copy()
        d.update(class_dict['optionalFieldDict'])
        class_dict['allFieldDict'] = d
        class_dict['fieldLookup'] = dict(
            [(x.field, x) for x in field_holder.mandatory_fields[1:-1] + field_holder.optional_fields])
        class_dict['msgTypeField'] = field_by_name['MsgType'](class_dict['MsgType'])
        cls = type(class_name, (Message, ), class_dict)
        message_by_name[class_name] = cls
        message_by_id[cls.MsgType] = cls

    # Make an 'unknown' message type.
#TODO maybe delete
#    class _UnKnownBase(Message):
#        def validate(self):
#            # All validation from here on in will be rubbish so we
#            assert self.exception is not None
#            raise self.exception

    # Message Type field I'll leave blank.
    # Thought about an arbitrary 'null' message field.
    # But would be too hacky.
    unknown_dict = {'fix': fix,
                   'MessageName': 'Unknown',
                   'mandatoryFields': [],
                   'optionalFields': [],
                   'allFields': [],
                   'mandatoryFieldDict': {},
                   'optionalFieldDict': {},
                   'allFieldDict': {},
                   'allFieldLookup': {}
    }

    fix.UnknownMessage = type('UnknownMessage', (Message, ), unknown_dict)

    fix.__dict__.update(field_by_name)
    fix.__dict__.update(message_by_name)
    fix.field_by_id = field_by_id
    fix.message_by_id = message_by_id
    fix.standard_header = standard_header
    fix.standard_trailer = standard_trailer
    return fix


if __name__ == '__main__':
    fix40 = parse_specification('FIX.4.0')
    fix41 = parse_specification('FIX.4.1')
    fix42 = parse_specification('FIX.4.2')
    fix43 = parse_specification('FIX.4.3')

