import time

try:
    CLOCK_BOOTTIME = time.CLOCK_BOOTTIME
except AttributeError:
    CLOCK_BOOTTIME = time.CLOCK_MONOTONIC

def nanos_since_boot():
    t = time.clock_gettime(CLOCK_BOOTTIME)
    return int(t * 1e9)

def millis_since_boot():
    t = time.clock_gettime(CLOCK_BOOTTIME)
    return t * 1e3

def seconds_since_boot():
    return time.clock_gettime(CLOCK_BOOTTIME)

def nanos_since_epoch():
    t = time.time()
    return int(t * 1e9)

def seconds_since_epoch():
    return time.time()

def nanos_monotonic():
    t = time.clock_gettime(time.CLOCK_MONOTONIC)
    return int(t * 1e9)

def nanos_monotonic_raw():
    try:
        t = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    except AttributeError:
        t = time.clock_gettime(time.CLOCK_MONOTONIC)
    return int(t * 1e9)