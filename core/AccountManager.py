from Manager import Manager

from Account import Account
accountDefaults = """
id,name
1,ACCOUNT1
2,ACCOUNT2
3,ACCOUNT3
"""

class AccountManager(Manager):
    def __init__(self, manageClass = Account, defaults = accountDefaults):
        Manager.__init__(self, manageClass, defaults)
        self.byName = self.indexBy( 'name' )

#sm = SecurityManager( defaults)
#def get():

if __name__=='__main__':
    am = AccountManager()
