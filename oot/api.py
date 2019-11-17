def attrsettermethod(method, attr, value):
    return setattr(method, attr, value) or method


def attrsetter(attr, value):
    """ Return a function that sets ``attr`` on its argument and returns it. """
    return lambda method: attrsettermethod(method, attr, value)


def oot(method):
    return attrsettermethod(method, "_oot_process", True)


def amqp(command):
    return attrsetter("_amqp_command", command)
