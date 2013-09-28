from pprint import pprint as pp
import string, os
from xml.dom import minidom
from datetime import datetime
from types import BooleanType, StringType

try:
    # Wierd assignment is just to keep pyflakes happy
    from collections import defaultdict as _defaultDict
    defaultdict = _defaultDict
except:
    from phroms.util.AutoKeyDict import AutoKeyDict as defaultdict

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
        self.mandatoryFields = []
        self.optionalFields  = []
        self.allFields       = []

class MessageIntegrityException(Exception):
    def __init__(self, strMessage, msg):
        Exception.__init__(self, strMessage)
        self.msg = msg

class BusinessReject(Exception):
    def __init__(self, strMessage, msg, field):
        Exception.__init__(self, strMessage)
        self.field = field
        self.msg   = msg

class LogicError(Exception):
    pass

class FixSpec:
    pass

class Message(object):
    def __init__(self,
                 headerFields = [], 
                 fields       = [],
                 footerFields = [],
                 isNative   = True,
                 sortFields = False ):
        self.headerFields = headerFields
        self.footerFields = footerFields
        # If things get painful remove this line. Don't know how critical this is
        if sortFields:
            fields.sort( lambda x,y: cmp( self.fieldLookup[ x.__class__].Position,
                                          self.fieldLookup[ y.__class__].Position ) )  
        self.fields = fields
        # self.pyfix = None # Created in subclass
        # if not isNative:
        # self.validate()

    def __repr__(self):
        return "%s" % self.MessageName

    def toFix(self):
        return "".join( [ x.toFix() for x in self.headerFields + self.fields + self.footerFields ] )

    def getField(self, msgClass):
        # XXX WTF!!!
        if 0:
            if not self.allFieldDict.has_key(msgClass):
                print self.allFieldDict, msgClass
                raise LogicError( "%s is not a member of %s" % ( msgClass.FieldName, self.MessageName) )

        for x in self.fields:
            if x.__class__==msgClass:
                return x
        return None

    def getOptionalFieldValue(self, msgClass, default = None):
        f = self.getField( msgClass )
        if not f:
            return default
        else:
            return f.value

    def getFieldValue(self, msgClass):
        return self.getField( msgClass ).value

    def getHeaderField( self, msgClass):
        for x in self.headerFields:
            if x.__class__==msgClass:
                return x
        return None

    def getHeaderFieldValue(self, msgClass, default = None):
        f = self.getHeaderField( msgClass )
        if f is not None:
            return f.value
        else:
            return default

    def getFields(self, msgClass):
        return [ x for x in self.fields if x.__class__==msgClass]

    def calcBodyLength(self, mutate = False):
        length = int( sum( [ x.size for x in self.headerFields[2:] + self.fields] ) )
        if mutate:
            # Okay so here we're blowing away one field but
            # want to leave fields as immutable for now
            self.headerFields[1] = self.fix.BodyLength( length )
        return length

    def calcCheckSum(self, mutate = False):
        checksum = "%03d" % (sum( [ x.checkSum for x in self.headerFields + self.fields + self.footerFields[:-1] ] ) % 256)
        if mutate:
            # Ditto - prefer to replace fields entirely rather
            # than try to mutate them in place
            self.footerFields[-1] = self.fix.CheckSum( checksum)
        return checksum

    def checkChecksum(self):
        checksum = self.calcCheckSum()
        cfSum = self.footerFields[-1].value
        if not checksum==cfSum:
            raise MessageIntegrityException( "CheckSum %s expected %s" % (cfSum, checksum), self )
            
    def checkBodyLength(self):
        calcLength = self.calcBodyLength()
        cfLength = self.headerFields[1].value
        if not calcLength==cfLength:
            raise MessageIntegrityException( "Body Length %s expected %s" % (cfLength, calcLength ), self )

    def checkStructure(self):
        if not self.getHeaderField(self.fix.MsgSeqNum): raise MessageIntegrityException("No Sequence number!", self)
        if not self.headerFields: raise MessageIntegrityException( "Can't calc body on msg without a header!", self)
        if not self.headerFields[0].__class__==self.fix.BeginString: raise MessageIntegrityException("First field in header has to be a begin!", self)
        if not self.headerFields[1].__class__==self.fix.BodyLength:  raise MessageIntegrityException("Second field in header must be BodyLength", self)
        if not self.footerFields: raise MessageIntegrityException( "Can't validate msg without a footer!", self)
        footerIdx = None
        for (i, f) in enumerate(self.footerFields):
            if f.__class__==self.fix.CheckSum:
                footerIdx = i
                break
        if footerIdx is None: raise MessageIntegrityException( "Can't find checksum in trailer fields" , self)

    def dump(self, prefix = ''):
        lines = [ "=" * 20 ] + self.headerFields + self.fields + self.footerFields + [ "=" * 20 ]
        for x in lines:
            print prefix + " " + str(x)

    def getDump(self, prefix = ''):
        lines = [ str(x) for x in self.headerFields + self.fields + self.footerFields ]
        return lines

    def validate(self):
        fix = self.fix
        # These three throw MessageIntegrityException
        # we're not required by the spec to reject anything that's not 'well-formed'
        # i.e checksum, bodylength are okay
        self.checkBodyLength()
        self.checkChecksum()
        self.checkStructure()

        # By now we've got something wellformed, anything throown from here on in
        # we shold be able to respond to with a reasonable business reject message
        # From here on in we through BusinessRejects
        self.headerMissing = fix.StandardHeader.mandatoryFieldDict.copy()
        for field in self.headerFields:
            field.validate(fix)
            try:
                del self.headerMissing[ field.__class__ ]
            except:
                pass
                #print "Failed to delete mandatory field (%s)" % field.FieldName
                
        if self.headerMissing:
            lstMissing = [ x.FieldName for x in self.headerMissing.keys() ]
            raise BusinessReject( "%s Missing Mandatory Header Field (%s)" % (self, ",".join(lstMissing) ), self,
                                  fix.SessionRejectReason.REQUIREDTAGMISSING )
                
        self.missing = self.mandatoryFieldDict.copy()
        for field in self.fields:
            field.validate(fix)
            if not self.allFieldDict.has_key( field.__class__ ):
                raise BusinessReject( "Field %s does not belong to message %s" % ( field.FieldName, self.MessageName ) , self,
                                      fix.SessionRejectReason.TAGNOTDEFINEDFORTHISMESSAGETYPE )
            
            #print field, type(field)
            try:
                del self.missing[field.__class__ ]
            except:
                #print "Failed to delete mandatory field %s" % field.FieldName
                pass
            
        if self.missing:
            pp(self.missing)
            pp(self.__class__)

            lstMissing = [ x.FieldName for x in self.missing.keys() ]
            raise BusinessReject( "Missing Mandatory Fields (%s)" % ",".join(lstMissing) , self, 
                                  fix.SessionRejectReason.REQUIREDTAGMISSING )

        self.footerMissing = fix.StandardTrailer.mandatoryFieldDict.copy()
        for field in self.footerFields:
            field.validate(fix)
            try:
                del self.footerMissing[ field.__class__ ]
            except:
                pass
                #print "Failed to delete mandatory field (%s)" % field.FieldName
        if self.footerMissing:
            lstMissing = [ x.FieldName for x in self.footerMissing.keys() ]
            raise BusinessReject( "%s Missing Mandatory Trailer Field (%s)" % (self, ",".join(lstMissing) ), self, 
                                  fix.SessionRejectReason.REQUIREDTAGMISSING )

class UnknownMessage( Message ):
    MessageName = "UnknownMessage"

class FieldValueException(Exception):
    pass

class ImmutableException( Exception ):
    pass

class Field(object):
    __slots__=[ 'value','fixValue' ]
    def __init__(self, value, isNative=True, collector = None ):
        self.value = None
        self.exception = None
        # We'll catch anything during construction
        # ( this will be called from the parsed).
        # the main protocol will call 'validate' on the message
        if isNative:
            self.value = value
            try:
                self.native2fix()
            except Exception, e:
                self.exception = e
        else:
            # Okay fairs fair if you pass non-string to nonnative
            # you don't deserve any sympathy :-)
            assert type(value)==StringType
            self.fixValue = value
            try:
                self.fix2native()
            except Exception, e:
                self.exception = e
        #if not self.validate():
        #    raise FieldValueException("Failed Validation on %s <%s> %s" %
        #                              (self.FieldName, str( self.__class__.Type ) , self.__class__.__bases__[0] ) )
        if collector:
            collector[self.collectorIndex].append(self)

        # Amortise the checksum calculation. The field will have done
        # the majority of the checksum/size calculation at class
        # creation time
        self.size = len(self.Tag) + 2 + len(self.fixValue)
        self.checkSum = self.OrdWithoutFixValue
        for x in self.fixValue:
            self.checkSum += ord(x)
        self.frozen = True

    #def __setattr__(self, attr, value):
    #    if 'frozen' in self.__dict__:
    #        raise ImmutableException( "Fields can't be modified")
    #    else:
    #        super.__setattr__(self, attr, value)
            
    def getFixValue(self):
        if self.fixValue:
            return self._fix
        else:
            return self.valueToFix(self)

    def fix2native(self):
        self.value = self.fixValue

    def __eq__(self, rhs):
        return rhs.__class__==self.__class__ and rhs.value==self.value

    def __hash__(self):
        return hash(self.toFix())

    def native2fix(self):
        self.fixValue = str(self.value)

    def validate(self, fix):

        if hasattr(fix, 'SessionRejectReason' ):
            badValueField = fix.SessionRejectReason.VALUEISINCORRECT
        else:
            badValueField = None
        
        if self.exception:
            raise BusinessReject( "Bad Value for %s : %s" % (self,
                                                             self.exception.message) ,
                                  self, 
                                  badValueField)

        try:
            ret = self._validate()
        except Exception, e:
            raise BusinessReject( "Bad Value for %s : %s" % (self,
                                                             e.message) ,
                                  self,
                                  badValueField )
        #print "Ret is %s" % ret
        if not ret:
            raise BusinessReject( "Invalid value for %s (%s vs %s)" % (self,
                                                                       self.value,
                                                                       self.fixValue),
                                  self,
                                  fix.SessionRejectReason.VALUEISINCORRECT )
    def _validate(self):
        return self.value is not None
            
    def __repr__(self):
        return "%s(%s->%s)" % ( self.FieldName, self.Tag, self.fixValue )

    def toFix(self):
        return "".join( [ self.Tag, '=', self.fixValue, SOH ])

class BooleanField(Field):
    def fix2native(self):
        self.value = { 'Y' : True,
                       'N' : False }.get( self.fixValue, None )
    def _validate(self):
        return type( self.value==BooleanType ) and self.fixValue in "YN"

    def native2fix( self ):
        if self.value:
            self.fixValue = "Y"
        else:
            self.fixValue = "N"

class IntegerField(Field):
    def fix2native( self ):
        self.value = int( self.fixValue)

    def _validate( self ):
        return int(self.value)==self.value

class FloatField(Field):
    def fix2native(self):
        self.value = float( self.fixValue)
    def _validate(self):
        return float(self.value)==self.value

class CharField(Field):
    def _validate(self):
        return type( self.value )==StringType and len(self.value)==1 and len(self.fixValue)==1

class EnumInstance(CharField):
    pass

class EnumBuilder(object):
    def __init__(self):
        self.instanceClass = None
        self.dicts = []

def weakAssert(clause,s):
    if not clause:
        raise Exception( s )

class EnumField( CharField ):
    def __init__(self, value, isNative = False, collector = None):
        CharField.__init__(self, value, isNative, collector)

    def _validate(self):
        if not self.__class__.lookupByValue.has_key( self.value ):
            raise Exception(  "invalue enum value %s" % self.value )
        return True
        

class UTCTimeStampField(Field):
    def fix2native(self):
        # NB Python 2.6 supports microseconds in strftime formats so might be worth
        # revisiting this
        # NB The strptime calls were a hotspot when I profiled so have implemented a quicker
        # parse of a UTC timestAmpvs-

        s = self.fixValue.split('.')[0]
        args = [ int(x) for x in s[:4],s[4:6],s[6:8],s[9:11],s[12:14],s[15:17] ]
        self.value = datetime(*args)

    def native2fix(self):
        self.fixValue = ''
        self.fixValue = self.value.strftime( FIX_UTC_TIMESTAMP_FORMAT )

    def _validate(self):
        return type( self.value ) == datetime

    def __repr__(self):
        return "%s(%s)" % (self.FieldName, self.fixValue)

def stripTextNodes(nodeList):
    ret = [ x for x in nodeList if not x.nodeType == minidom.Node.TEXT_NODE ]
    return ret

def parseMsgType(node):
    ret = {}
    children = stripTextNodes( node.childNodes )
    dodgy = False
    for child in children:
        if not len( child.childNodes)==1:
            dodgy = True
            continue
        nodeName = child.nodeName
        assert not ret.has_key( nodeName )
        ret[nodeName.encode('utf-8')] = child.childNodes[0].data.encode('utf-8')

    if dodgy:
        # print "Skipping malformed field %s" % ret
        return None
    return ret

def getDictionariesFromFile( fn , nodeName):
    d = minidom.parse( fn)
    dr = d.getElementsByTagName( "dataroot")
    msgTypeNodes = [ x for x in dr[0].childNodes if
                     x.nodeType==minidom.Node.ELEMENT_NODE and
                     x.nodeName==unicode(nodeName) ]
    dictionaries= [ parseMsgType(x) for x in msgTypeNodes ]
    ret = [ x for x in dictionaries if x ]
    return ret

def makeString(s):
    return "".join( [ x for x in s if x in string.ascii_letters ] )

import re
bracketRe = re.compile("(.*)\(.*\).*")
def parseDescription(x):
    x = x.upper()
    match = bracketRe.match( x )
    if match:
        return makeString(match.groups()[0])
    else:
        return(makeString(x))


# Map FIX Field type to our Field validators
subClasses = { 'UTCTimestamp' : UTCTimeStampField,
               'Length'       : IntegerField,
               'Amt'          : IntegerField,
               ' char'        : CharField,
               'char'         : CharField,
               'float'        : FloatField,
               'PriceOffset'  : FloatField,
               'Boolean'      : BooleanField, 
               'Price'        : FloatField,
               'Qty'          : IntegerField,
               'SeqNum'       : IntegerField,
               'int'          : IntegerField,
               'Quantity'     : IntegerField }

def parseSpecification( version  = "FIX.4.2" ,
                        fileRoot = "/home/andy/wc/resources/pyfix/pyfix-repository",):
    fix = FixSpec()
    fix.version = version

    versionRoot = os.path.join( fileRoot, version)

    files = ['MsgType','Fields','MsgContents', 'Enums']
    msgTypes, fields, msgContent, enums = \
       [ getDictionariesFromFile( os.path.join( versionRoot, "%s.xml" % x) , x) for x in files ]

    messageClassLookup = {}
    for d in msgTypes:
        klazzName = makeString( d['MessageName'] )
        # These will be popualated once we've got the messagecontents
        klazzDict = d.copy()
        klazzDict['mandatoryFields'] = []
        klazzDict['optionalFields']  = []
        klazzDict['allFields' ]      = []
        # Using attributes of our new class will show it's working
        #print d
        messageClassLookup[ d['MsgID'] ] = ( klazzName, klazzDict )
        #cls = type( klazzName, ( Message, ), klazzDict )

    print "Generating classes for pyfix fields ..."

    d2 ={' char': None,
     'Amt': None,
     'Boolean': None,
     'Char': None,
     'Currency': None,
     'Exchange': None,
     'Length': None,
     'LocalMktDate': None,
     'MultipleValueString': None,
     'Price': None,
     'PriceOffset': None,
     'Qty': None,
     'Quantity': None,
     'String': None,
     'UTCDate': None,
     'UTCTimeOnly': None,
     'UTCTimestamp': None,
     'char': None,
     'data': None,
     'day-of-month': None,
     'float': None,
     'int': None,
     'month-year': None,
     'n/a': None}

    # [ x for x in d2.keys() if not subClasses.has_key(x) ]

    ['n/a',
     'MultipleValueString',
     'UTCDate',
     'String',
     'Exchange',
     'UTCTimeOnly',
     'data',
     'day-of-month',
     'Char',
     'Currency',
     'month-year',
     'LocalMktDate']


    # Make an index for the enumerations
    enumLookup = defaultdict( lambda: EnumBuilder() )
    for d in enums:
        tag   = d['Tag']
        b = enumLookup[tag]
        #inst = CharField( d['Enum'] )
        #b.desc.append( "%s = %s" % ( value, d['Description']) )
        b.dicts.append( d )

    fieldByName, fieldByID = {}, {}
    for f in fields:
        #pp( vars(f) )
        klassName = makeString(f['FieldName'])
        klassDict = f
        klassDict[ 'TagEquals'] = f['Tag'] + "="
        klassDict[ 'collectorIndex'] = None
        klassDict[ 'OrdWithoutFixValue' ] = sum( [ ord(x) for x in klassDict['TagEquals'] + SOH ] )
        klassDict[ '__doc__' ]=f['Desc']
        
        isEnum = False
        if enumLookup.has_key( f['Tag'] ):
            isEnum = True
            Klass = CharField
        elif subClasses.has_key( f['Type'] ):
            Klass = subClasses[f['Type']]
        else:
            Klass = Field

        cls = type( klassName , (Klass,), klassDict )

        if isEnum:
            builder = enumLookup[f['Tag']]
            builder.instanceClass = cls
            builder = None
        fieldByName[cls.FieldName] = cls
        fieldByID[cls.Tag ]   = cls

    # Fix up our enumerations.
    for q,bldr in enumLookup.items():
        cls = bldr.instanceClass
        lookupByDesc        = {}
        lookupByValue       = {}
        desc = []
        descriptionForField = {}
        for d in bldr.dicts:
            inst = cls( d['Enum'] )
            pd =  parseDescription( d['Description'] )
            lookupByDesc[ pd] = inst
            lookupByValue[ d['Enum'] ] = inst
            descriptionForField[ inst ] = pd
            desc.append( "%s = %s" % (d['Enum'], d['Description'] ))
            
        setattr( cls, 'lookupByDesc' , lookupByDesc  )
        setattr( cls, 'lookupByValue', lookupByValue )
        setattr( cls, 'descriptionForField', descriptionForField )
        for q,v in lookupByDesc.items():
            setattr(cls, q, v)

    for q,bldr in enumLookup.items():
        cls = bldr.instanceClass
        cls.__bases__=(EnumField,)

    ################################################################################
    # MSG CONTENTS
    ################################################################################

    print "Generating message content classes ..."

    #msgContent = getDictionariesFromFile( "/Users/andy/downloads/pyfix-repository_20080317/FIX.4.2/MsgContents.xml",
    #                                      'MsgContents')
    contentByMessageId = defaultdict( lambda: SpecialField() )

    for x in msgContent:
        obj = MessageContent(x)
        targetMessageID = x['MsgID']
        targetFieldID   = x['TagText']

        target = contentByMessageId[targetMessageID]
        assert x['Reqd'] in [ '0', '1' ], "Required field expected string zero or one"
        if x['Reqd']=='0':
            target.optionalFields.append( obj )
        else:
            target.mandatoryFields.append( obj )
        target.allFields.append( obj )

        if not fieldByID.has_key( targetFieldID ):
            #print "Couldn't find field %s continuing %s"  % (targetFieldID, x)
            continue

        targetField = fieldByID[ targetFieldID ]
        obj.field = targetField
        targetField.collectorIndex = 1

    # Header/Trailer stuff didn't seem to be immediately available
    # from the XML file so parsed them up from the PDFs

    headerData = [['8', 'BeginString', 'Y'],
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

    trailerData = [['93', 'SignatureLength', 'N'],
     ['89', 'Signature', 'N'],
     ['10', 'CheckSum', 'Y']]

    def indexFields(data, collectorIndex):
        ordinal = 0
        fieldToOrdinal = {}
        mandatoryFields = []
        optionalFields  = []
        allFieldDict = {}
        mandatoryFieldDict = {}
        optionalFieldDict  = {}

        for tagNumber, MessageName, mandatory in data:
            if not fieldByName.has_key(MessageName):
                print "Skipping %s %s" % (MessageName, version)
                continue
            field = fieldByName[MessageName]
            assert field is not None, "Can't find %s" % MessageName
            field.collectorIndex = collectorIndex
            assert mandatory in 'YN'
            if mandatory=='Y':
                mandatoryFields.append( field )
                mandatoryFieldDict[field] = None
            else:
                optionalFields.append( field )
                optionalFieldDict[field] = None
            allFieldDict[field] = None
            fieldToOrdinal[field] = ordinal
            ordinal += 1
        return type( 'ret', (Message,), locals() )

    StandardHeader  = indexFields( headerData  , 0)
    StandardTrailer = indexFields( trailerData , 2)

    messageByName, messageByID = {}, {}
    for msgID, n_d in messageClassLookup.items():
        (klazzName, klazzDict) = n_d
        fieldHolder = contentByMessageId[ msgID ]

        for field in fieldHolder.mandatoryFields:
            assert field is not None
        
        for field in fieldHolder.optionalFields:
            assert field is not None
        
        klazzDict['pyfix']             = fix
        klazzDict['MessageName']     = klazzName
        klazzDict['mandatoryFields'] = fieldHolder.mandatoryFields
        klazzDict['optionalFields']  = fieldHolder.optionalFields
        klazzDict['allFields' ]       = fieldHolder.allFields
        klazzDict['mandatoryFieldDict'] = dict( [ (x.field,None) for x in fieldHolder.mandatoryFields[1:-1 ] ] )
        klazzDict['optionalFieldDict']  = dict( [ (x.field,None) for x in fieldHolder.optionalFields ] )
        d = klazzDict['mandatoryFieldDict'].copy()
        d.update( klazzDict['optionalFieldDict'] )
        klazzDict['allFieldDict'] = d
        klazzDict['fieldLookup'] = dict( [ (x.field,x) for x in fieldHolder.mandatoryFields[1:-1 ]+fieldHolder.optionalFields ] )
        klazzDict['msgTypeField' ] = fieldByName['MsgType']( klazzDict['MsgType'])
        cls = type(klazzName, (Message, ), klazzDict)
        messageByName[ klazzName ] = cls
        messageByID[ cls.MsgType ] = cls

    # Make an 'unknown' message type.

    class _UnKnownBase( Message ):
        def validate(self):
            # All validation from here on in will be rubbish so we 
            assert self.exception is not None
            raise self.exception

    # Message Type field I'll leave blank.
    # Thought about an arbitrary 'null' message field.
    # But would be too hacky.
    unknownDict = { 'pyfix' : fix,
                    'MessageName' : 'Unknown',
                    'mandatoryFields' : [],
                    'optionalFields'  : [],
                    'allFields'       : [],
                    'mandatoryFieldDict' : {},
                    'optionalFieldDict'  : {},
                    'allFieldDict'       : {},
                    'allFieldLookup'     : {}
                    }

    fix.UnknownMessage = type( 'UnknownMessage', (Message, ) , unknownDict)

    fix.__dict__.update( fieldByName   )
    fix.__dict__.update( messageByName ) 
    fix.fieldByID   = fieldByID
    fix.messageByID = messageByID
    fix.StandardHeader  = StandardHeader
    fix.StandardTrailer = StandardTrailer
    return fix

if __name__=='__main__':
    fix40 = parseSpecification( 'FIX.4.0')
    fix41 = parseSpecification( 'FIX.4.1')
    fix42 = parseSpecification( 'FIX.4.2')
    fix43 = parseSpecification( 'FIX.4.3')

