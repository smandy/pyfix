lines = """93 SignatureLength N Required when trailer contains signature.  Note:  Not to be included 
within SecureData field 
89 Signature N Note:  Not to be included within SecureData field 
10 CheckSum Y (Always unencrypted, always last field in message)"""

from pprint import pprint as pp
import string

lines = lines.split("\n")
lines = [ x for x in lines if x and  x[0] in string.digits ]
trailerData = []
for line in lines:
    #print line
    x = line.split()[:3]
    trailerData.append( x )

if __name__=='__main__':
    pp(trailerData)
