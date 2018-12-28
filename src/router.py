import re

g_data_route = dict()
g_mqtt_data_route = dict()


def reroute(reg):
    def func1(func):
        g_data_route[reg] = func

        # def func2(name):
        #     print('haha1')
        #     return func(name)

        # return func2

    return func1


def mqtt_reroute(reg):
    def func1(func):
        g_mqtt_data_route[reg] = func

    return func1


if __name__ == '__main__':

    data = '01_40_10_647'

    print(g_data_route)

    for k in g_data_route:
        try:
            res = re.match(k, data)
            # print(res.group())
        except Exception as e:
            print(e)
        else:
            if res is None:
                continue
            # print(res.groups())
            if len(res.groups()) > 0:
                g_data_route[k](data, res.groups())
            else:
                g_data_route[k](data)
