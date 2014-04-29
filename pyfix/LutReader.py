__author__ = 'andy'



def from_file(fn):
    lines = open(fn , 'r').readlines()

if __name__=='__main__':
    fn = '/tmp/andy/lut.lut'
    xs = from_file(fn)