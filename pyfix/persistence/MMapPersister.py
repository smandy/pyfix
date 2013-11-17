import mmap
from collections import namedtuple
import os
import struct

Buffer = namedtuple( 'Buffer', ['dat','idx', 'offset', 'fileIdx'] )

class NumberBuffer:
    def __init__(self, struct, mm):
        self.struct = struct
        self.mm     = mm
        self.ss = struct.size

    def flush(self):
        self.mm.flush()
        
    def __getitem__(self, n):
        assert n >= 0, "Negative index %s" % n
        assert (n+1)*self.ss <= len(self.mm), "Index out of bounds"
        return self.struct.unpack_from( self.mm, n*self.ss)[0]

    def __setitem__(self, idx, n):
        #print "Set %s %s" % (idx, n)
        self.struct.pack_into(self.mm, idx * self.struct.size, n)
        
def allocateMmap(fn, sz):
    #print fn
    if not os.path.exists(fn):
        f = open(fn, 'w+')
        f.seek(sz - 1 )
        f.write(' ')
        f.flush()
    else:
        f = open(fn, 'r+')
    return mmap.mmap(f.fileno(), 0 )

INT_STRUCT  = struct.Struct('<i') # Little Endian Int32
LONG_STRUCT = struct.Struct('<q') # Little Endian Int32

def makeBuffer(root, sz, offset, fileIdx):
    return Buffer( allocateMmap('%s.dat' % root, sz),
                   NumberBuffer( LONG_STRUCT, allocateMmap('%s.idx' % root, sz * 8) ) ,
                   offset, fileIdx
                   )
class MMAP(object):

    __slots__ = ['bufferSize','root','fileIdx','idx','cache','globalIdx','current','idxWithinBuffer','locWithinBuffer']

    def __init__(self, root, bufferSize, maxBuffers = 10000):
        self.bufferSize = bufferSize
        self.root = root
        self.fileIdx = 0
        self.idx     = 0
        self.cache = {}

        self.globalIdx = NumberBuffer( LONG_STRUCT, allocateMmap( "%s_globalindex.dat" % self.root, maxBuffers * 4 )  )
        self.load()

    def flush(self):
        def flushBuf(x):
            x.idx.flush()
            x.dat.flush()
        for c in self.cache.values():
            flushBuf(c)
        self.globalIdx.flush()

    def load(self):
        self.idx = 0
        self.locWithinBuffer = 0
        self.idxWithinBuffer = 0
        while True:
            pth = "%s_%05d" % (self.root, self.fileIdx)
            #print "Looper", pth
            self.current = makeBuffer( pth , self.bufferSize, self.idx, self.fileIdx)
            self.cache[ self.fileIdx ] = self.current
            #print self.globalIdx[self.fileIdx], self.idx
            self.idxWithinBuffer  = self.globalIdx[self.current.fileIdx] - self.idx
            #print "Idx now = ", self.idxWithinBuffer, self.current.idx[self.idxWithinBuffer]
            if self.idxWithinBuffer==0:
                self.locWithinBuffer = 0
            else:
                self.locWithinBuffer  = self.current.idx[self.idxWithinBuffer-1]
                #print "expect nonzero", self.current.idx[self.idxWithinBuffer - 1], " expect zero = ", self.current.idx[self.idxWithinBuffer]

            while self.current.idx[self.idxWithinBuffer]!=0:
                self.idxWithinBuffer += 1
                print "Idx is ", self.idxWithinBuffer
                
            self.idx = self.globalIdx[self.fileIdx] + 1
            self.fileIdx += 1
            
            if self.globalIdx[self.fileIdx]==0:
                break

    def allocate(self):
        pth = "%s_%05d" % (self.root, self.fileIdx)
        print pth
        self.locWithinBuffer = 0
        self.idxWithinBuffer = 0
        self.current = makeBuffer( pth , self.bufferSize, max(self.idx-1 , 0) , self.fileIdx)
        self.cache[self.fileIdx] = self.current
        self.fileIdx += 1

    def __len__(self):
        return self.findLast()[0]

    def findLast(self):
        n = 0
        current = 0
        currentIdx = 0
        while True:
            x = self.globalIdx[n]
            if x == 0:
                return current, currentIdx
            current = x
            currentIdx = n
            n += 1

    def __getitem__(self, n):
        offset, maxIdx = self.findLast()
        assert n<offset, "Out of bounds"
        assert n>=0,  "Out of bounds"
        idx = 0
        offset = 0
        while idx<maxIdx:
            newOffset = self.globalIdx[idx]
            if n <= newOffset:
                break
            idx += 1
            offset = newOffset
            
        cache = self.cache[idx]
        cache = self.cache[idx]
        startIdx = n - offset
        if startIdx == 0:
            s = 0
        else:
            s = cache.idx[startIdx-1]
        return cache.dat[ s:cache.idx[startIdx] ]
        
    def write(self, s):
        l = len(s)
        if self.locWithinBuffer + l > self.bufferSize:
            self.allocate()
            
        self.current.dat[self.locWithinBuffer:self.locWithinBuffer+l] = s
        self.locWithinBuffer += l
        
        self.current.idx[self.idxWithinBuffer] = self.locWithinBuffer
        self.idxWithinBuffer += 1
        
        self.globalIdx[self.current.fileIdx] = self.idx
        self.idx             += 1

def choice():
    return "%s_%s_%s" % (random.choice( [1,2,3,4,5] ),
                         random.choice( ['foo','bar','baz'] ),
                         random.choice( [ 'jijwjdiw','fjefiejf','ifjeijfeijf']) )

if __name__=='__main__':
    import tempfile
    d = tempfile.mkdtemp( )
    if 1:
        def getMmap():
            return MMAP( "%s/ledger" % d, 10000)
    else:
        def getMmap():
            return MMAP( "/tmp/andy/ledg18" , 10000 )

    i = 0
    f = getMmap()
    while i < 100000:
        #print "Looping ", i
        invar1 = (f.fileIdx, len(f.cache), f.globalIdx[f.fileIdx], f.idx, f.idxWithinBuffer, f.locWithinBuffer  )
        f = getMmap()
        invar2 = (f.fileIdx, len(f.cache), f.globalIdx[f.fileIdx], f.idx, f.idxWithinBuffer, f.locWithinBuffer  )

        if not invar1==invar2:
            print "Bad invariants %s %s" % (str(invar1), str(invar2))
            break

        import random
        for x in range( random.choice( [ 4,  10, 23])):
            f.write( "Run %05d                      " % i)
            i += 1
        f.flush()

    #f = getMmap()
    if 0:
        f = getMmap()
        choices = {}
        if 1:
            for i in range(100):
                f.write("%05d" % i)

        print "Before ", f.globalIdx[0], f.idx, f.idxWithinBuffer, f. locWithinBuffer, f.current.idx[100]
        if 0:
            for i in range(101):
                if f[i] != "Choice number %s" % i:
                    print "Bad idx %s %s" % (i, f[i])
                if i % 1000 == 0:
                    print i, f[i]

        f = getMmap()
        print "Idx is " , f.idxWithinBuffer, f.current.dat[f.current.idx[f.idxWithinBuffer]:f.current.idx[f.idxWithinBuffer+10]]
        print len(f)
        #f.write('foo')rr
        print len(f)
        print f.idx, f.idxWithinBuffer, f.findLast(), len(f), f.current.dat[:600]
        print "After ", f.globalIdx[0], f.idx, f.idxWithinBuffer, f.locWithinBuffer, f.current.idx[100]

        if 0:
            print "Writing", len(f)
            print f[100]
            f.write('bar')
            print 'afterbar ', f.idx, f.idxWithinBuffer, f.findLast(), len(f), f.current.dat[:600]

            f.write('booyakasha')
            print 'afterbooya ', f.idx, f.idxWithinBuffer, f.findLast(), len(f), f.current.dat[:600]

