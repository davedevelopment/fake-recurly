
class FieldError(ValueError):
    def __init__(self, resource, name, symbol):
        self.resource = resource
        self.name = name
        self.symbol = symbol

    def __unicode__(self):
        msg = 'unknown'
        if self.symbol == "taken":
            msg = 'has already been taken'
        return "<error field=\"%s.%s\" symbol=\"%s\">%s</error>" % (self.resource, self.name, self.symbol, msg)

class NotFoundError(ValueError):
    def __init__(self, msg):
        self.msg = msg

    def __unicode__(self):
        return "<error><symbol>not_found</symbol><description lang=\"en-US\">%s</description></error>" % (self.msg)

