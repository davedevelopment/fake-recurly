import string, random
from datetime import datetime

class Account:

    _data = {}

    def __init__(self, accountCode):
        self.accountCode = accountCode

    @classmethod 
    def find(cls, code):
        if code in cls._data:
            return cls._data[code]
        return None

    @classmethod
    def save(cls, account):
        cls._data[account.accountCode] = account

    @classmethod
    def truncate(cls):
        cls._data = {}


class Subscription:
    _data={}
    def __init__(self):
        self.uuid = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
        self.state = 'active'
        self.past_due = False
        pass
    
    @classmethod
    def fromTree(cls, tree):
        sub = Subscription()
        if tree.find("uuid"):
            sub.uuid = tree.find("uuid").text
        sub.planCode = tree.find("plan_code").text
        sub.accountCode = tree.find("account/account_code").text
        return sub

    @classmethod 
    def find(cls, uuid):
        if uuid in cls._data:
            return cls._data[uuid]
        return None

    @classmethod
    def findByAccount(cls, code, state=False):
        subs = dict((k,v) for (k,v) in cls._data.iteritems() if v.accountCode == code)

        if state == False:
            return subs

        ret = {}
        print subs
        for uuid,sub in subs.iteritems():
            if state == 'past_due' and sub.past_due:
                ret[uuid] = sub
            elif state == sub.state:
                ret[uuid] = sub

        return ret

    @classmethod
    def save(cls, sub):
        cls._data[sub.uuid] = sub

    @classmethod
    def truncate(cls):
        cls._data = {}

class Transaction:
    _data = {}

    def __init__(self):
        self.status = 'success'
        self.recurring = True
        self.created = datetime.now()
        self.uuid = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

    @classmethod 
    def find(cls, uuid):
        if uuid in cls._data:
            return cls._data[uuid]
        return None

    @classmethod
    def findByAccount(cls, code):
        return dict((k,v) for (k,v) in cls._data.iteritems() if v.accountCode == code)

    @classmethod
    def save(cls, trans):
        cls._data[trans.uuid] = trans

    @classmethod
    def truncate(cls):
        cls._data = {}

class Plan:
    _data = {}

    def __init__(self,planCode):
        self.planCode = planCode

    @classmethod
    def fromTree(cls, tree):
        plan = Plan(tree.find("plan_code").text)
        plan.length = tree.find("plan_interval_length").text
        plan.unit   = tree.find("plan_interval_unit").text
        return plan

    @classmethod 
    def find(cls, code):
        if code in cls._data:
            return cls._data[code]
        return None

    @classmethod
    def save(cls, plan):
        cls._data[plan.planCode] = plan

    @classmethod
    def delete(cls, plan):
        del cls._data[plan.planCode]

    @classmethod
    def truncate(cls):
        cls._data = {}
