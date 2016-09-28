MODE_BARE_METAL = 0
MODE_DOCKER = 1
MODE_VM = 2

def str_to_mode(s):
    if s in ('bm', 'bare', 'bare_metal'):
        return MODE_BARE_METAL
    elif s in ('d', 'docker'):
        return MODE_DOCKER
    elif s in ('vm', 'kvm', 'virtual_machine'):
        return MODE_VM
    raise ValueError("Unsupported mode: \"%s\"" % s)
