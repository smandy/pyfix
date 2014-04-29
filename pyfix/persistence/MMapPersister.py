import mmap
from collections import namedtuple
import os
import struct

Buffer = namedtuple('Buffer', ['dat', 'idx'])
INT_STRUCT = struct.Struct('<i') # Little Endian Int32
LONG_STRUCT = struct.Struct('<q') # Little Endian Int32


def allocateMmap(fn, sz):
    #print fn
    if not os.path.exists(fn):
        f = open(fn, 'w+')
        f.seek(sz - 1)
        f.write(' ')
        f.flush()
    else:
        f = open(fn, 'r+')
    return mmap.mmap(f.fileno(), 0)


class NumberBuffer:
    def __init__(self, s, mm):
        self.s = s
        self.mm = mm
        self.ss = s.size
        self.capacity = len(self.mm) / self.s.size
        print "Capacity = %s" % self.capacity

    def flush(self):
        self.mm.flush()

    def __getitem__(self, n):
        assert n >= 0, "Negative index %s" % n
        assert (n + 1) * self.ss <= len(self.mm), "Index out of bounds"
        return self.s.unpack_from(self.mm, n * self.ss)[0]

    def __setitem__(self, idx, n):
        #print "Set %s %s" % (idx, n)
        self.s.pack_into(self.mm, idx * self.s.size, n)

    def __len__(self):
        """Find last nonzero element"""
        lo = 0
        hi = self.capacity - 1
        while lo + 1 < hi:
            idx = (hi + lo ) / 2
            #print lo, hi, idx
            if self[idx] == 0:
                hi = idx
            else:
                lo = idx
        return hi


def dat_for_root(s):
    return "%s.dat"


def idx_for_root(s):
    return "%s.idx"


def make_buffer(root, sz, offset, fileIdx):
    return Buffer(
        allocateMmap('%s.dat' % root, sz),
        NumberBuffer(LONG_STRUCT, allocateMmap(idx_for_root(root), sz * 8))
    )


def root_for_idx(r, idx):
    return "%s_%05d" % (r, idx)


class MMAPPersister(object):
    __slots__ = ['buf_size', 'root', 'file_idx', 'idx', 'cache', 'current', 'buffer_idx', 'buffer_loc']

    def __init__(self, root, bufferSize, maxBuffers=10000):
        self.buf_size = bufferSize
        self.root = root
        self.file_idx = 0
        self.idx = 0
        self.cache = {}
        self.load()
        self.buffer_idx = 0
        self.buffer_loc = 0
        self.current = None

    def flush(self):
        def fl(x):
            x.idx.flus()
            x.dat.flush()

        for c in self.cache.values():
            fl(c)

    def load(self):
        self.idx = 0
        self.buffer_loc = 0
        self.buffer_idx = 0
        pth = root_for_idx(self.root, self.file_idx)
        while True:
            self.current = make_buffer(pth, self.buf_size, self.idx, self.file_idx)
            self.cache[self.file_idx] = self.current
            if self.buffer_idx == 0:
                self.buffer_loc = 0
            else:
                self.buffer_loc = self.current.idx[self.buffer_idx - 1]
            self.file_idx += 1
            if not os.path.exists(dat_for_root(root_for_idx(self.root, self.file_idx))):
                break

    def allocate(self):
        pth = root_for_idx(self.root, self.file_idx)
        print pth
        self.buffer_loc = 0
        self.buffer_idx = 0
        self.current = make_buffer(pth, self.buf_size, max(self.idx - 1, 0), self.file_idx)
        self.cache[self.file_idx] = self.current
        self.file_idx += 1

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
        assert n < offset, "Out of bounds"
        assert n >= 0, "Out of bounds"
        idx = 0
        offset = 0
        while idx < maxIdx:
            new_offset = self.globalIdx[idx]
            if n <= new_offset:
                break
            idx += 1
            offset = new_offset

        cache = self.cache[idx]
        startIdx = n - offset
        if startIdx == 0:
            s = 0
        else:
            s = cache.idx[startIdx - 1]
        return cache.dat[s:cache.idx[startIdx]]

    def write(self, s):
        l = len(s)
        if self.buffer_loc + l > self.buf_size:
            self.allocate()

        self.current.dat[self.buffer_loc:self.buffer_loc + l] = s
        self.buffer_loc += l

        self.current.idx[self.buffer_idx] = self.buffer_loc
        self.buffer_idx += 1

        self.globalIdx[self.current.fileIdx] = self.idx
        self.idx += 1


def choice():
    return "%s_%s_%s" % (random.choice([1, 2, 3, 4, 5]),
                         random.choice(['foo', 'bar', 'baz']),
                         random.choice(['jijwjdiw', 'fjefiejf', 'ifjeijfeijf']) )


if __name__ == '__main__':
    if 1:
        import tempfile

        d = tempfile.mkdtemp()
        if 1:
            def getMmap():
                return MMAPPersister("%s/ledger" % d, 10000)
        else:
            def getMmap():
                return MMAPPersister("/tmp/andy/ledg18", 10000)
        i = 0
        f = getMmap()
        while i < 100000:
            #print "Looping ", i
            f = getMmap()
            import random

            for x in range(random.choice([4, 10, 23])):
                f.write("Run %05d                      " % i)
                i += 1
            f.flush()

import tempfile

d = tempfile.mkdtemp()
for t in range(50):
    x = NumberBuffer(LONG_STRUCT, allocateMmap('%s/andy_%s.dat' % (d, t), 1000 * 8))
    for i in range(t):
        x[i] = t + 1 * 2
    print t, len(x)
