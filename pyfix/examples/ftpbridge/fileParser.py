from pprint import pprint as pp
from pyfix.examples.simpleordersend.sender import fix


class FileFormatException(Exception):
    pass


class FileParser(object):
    fileFormat = [
    ('Side', lambda x: {
    'B': fix.Side.BUY,
    'S': fix.Side.SELL}[x] ),
    ('Qty'   , lambda x: fix.OrderQty(int(x)) ),
    ('Symbol', lambda x: fix.Symbol(x) )]

    def parse(self, data):
        lines = [x.split(',') for x in data.split("\n")]
        header, dataLines = lines[0], lines[1:]

        # Sanity check, make sure our required fields are in the
        for q_v in self.fileFormat:
            if not q_v[0] in header:
                raise FileFormatException("Missing field %s in file" % q_v[0])
        print header
        print dataLines
        linesAccepted = {True: [],
                         False: []}
        for x in dataLines:
            linesAccepted[len(x) == len(header)].append(x)

        if linesAccepted[False]:
            print "rejecting lines %s" % linesAccepted[False]

        dicts = [dict(zip(header, x)) for x in linesAccepted[True]]
        results = []
        for d in dicts:
            rd = {}
            for field, functor in self.fileFormat:
                v = d[field]
                converted = functor(v)
                rd[converted.__class__] = converted
            results.append(rd)
        return results


testFile = """Side,Qty,Symbol
B,200,MSFT
S,300,GLW
B,100,PEB
B,2"""

if __name__ == '__main__':
    pp(FileParser().parse(testFile))
