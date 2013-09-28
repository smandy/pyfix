from pprint import pprint as pp

class AutoKeyDict(dict):
    def __init__(self, factory = lambda: []):
        dict.__init__(self)
        self.factory = factory

    def __getitem__(self, x):
        if not x in self:
            dict.__setitem__(self, x, self.factory() )
        return dict.__getitem__(self, x)
            
if __name__=='__main__':
    stockDict = AutoKeyDict( factory = lambda: [] )
    for x,y in ( ('c' , 1),
                 ('a' , 2),
                 ('c' , 3),
                 ('a' , 4),
                 ('g' , 5) ):
        stockDict[x].append(y)
    pp( stockDict )
