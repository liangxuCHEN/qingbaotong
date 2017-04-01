def traversal():
    l = [(x, x**2) for x in range(5)]
    d = dict(l)

    for i in d:
        print(i, d[i])

    for k, v in d.items():
        print("%d : %d" % (k, v))

    for k, v in zip(d.iterkeys(), d.itervalues()):
        print(k, v)


def set_value():
    d1 = {}
    d1['a'] = 1

    d2={'bb':1, 'cc':2}

    i = ['fff', 1]
    l = ['ggg', 2]
    d3 = dict([i,l])

    print(d1,d2,d3)

    d1.update(d3)
    print(d1)

if __name__ == '__main__':
    set_value()
