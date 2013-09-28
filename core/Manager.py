# $Header: /Users/andy/cvs/dev/python/phroms/core/Manager.py,v 1.7 2009-01-09 22:48:15 andy Exp $

class Manager:
    def __init__(self, klazz, defaults):
        print self.__class__
        self.klazz = klazz
        self.byId = {}
        _id = 0
        lines = defaults.split("\n")[1:-1]
        lines = [ x.split(',') for x in lines]
        dicts = [ dict( zip( lines[0], x) ) for x in lines[1:] ]
        #pp( dicts)
        #print lines
        #self.bySecurityIdentifier = {}
        self.items = []
        self.byName = {}
        self.indices = {}

        # This is a test
        for d in dicts:
            s = self.klazz()
            s.__dict__.update( d )
            s.id = _id
            self.byId[_id] = s
            self.items.append(s)
            _id += 1

    def getByFields( self, fields , val):
        for field in fields:
            if self.indices[field].has_key( val ):
                return self.indices[field][val]
        return None

    lookupByFields = getByFields

    def indexBy(self, field):
        ret = {}
        for s in self.items:
            q = getattr(s, field)
            assert not ret.has_key(q)
            ret[ q ] = s
        self.indices[field] = ret
        return ret

    def getByCriteria(self, crit):
        ret = [ x for x in self.items if crit(x) ]
        return ret

    def getUnique(self, crit):
        ret = self.getByCriteria(crit)
        assert len(ret)==1, "Expected length 1 got %s" % len(ret)
        return ret[0]

    def getDefault(self):
        return self.items[0]

    def getByName(self, name):
        return self.byName.get( name, None ) 
                  
    #def getBySecurityIdentifier(self, si):
    #    if not self.bySecurityIdentifier.has_key(si):
    #        self.bySecurityIdentifier[si] = {}
    #    return self.bySecurityIdentifier[si]
