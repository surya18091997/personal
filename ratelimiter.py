import datetime
import time


def RateLimited(maxPerMinute):
    minInterval = 60
    print(minInterval)

    def decorate(func):
        start_time = datetime.datetime.now()
        count = 0
        print(start_time)

        def rateLimitedFunction(*args, **kargs):
            nonlocal start_time
            nonlocal count
            if (
                (datetime.datetime.now() - start_time).total_seconds()
            ) < minInterval and count > maxPerMinute:
                print(
                    minInterval - (datetime.datetime.now() - start_time).total_seconds()
                )
                time.sleep(
                    minInterval - (datetime.datetime.now() - start_time).total_seconds()
                )
                start_time = datetime.datetime.now()
                count = 0
            elif ((datetime.datetime.now() - start_time).total_seconds()) > minInterval:
                count = 0
                start_time = datetime.datetime.now()
                print(start_time)
            ret = func(*args, **kargs)
            count += 1
            return ret

        return rateLimitedFunction

    return decorate


@RateLimited(80)
def func(no):
    time.sleep(2)
    print(no)


for i in range(1, 60):
    func(i)
