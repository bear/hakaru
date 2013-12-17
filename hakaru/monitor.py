#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:copyright: (c) 2013 by Mike Taylor
:license: MIT, see LICENSE for more details.

Gather metrics from a server and push to collection endpoint
"""

import os, sys
import time
import logging

from multiprocessing import Process, current_process

import psutil
import statsd

import loghandler
from tools import getRedis

workers  = []

def handleMetric(config, source, logLevel=logging.DEBUG):
    """setup and monitor the resource specified by "source"

    events are sent to the redis pubsub channel listed in config
    """
    qh  = loghandler.QueueLogHandler(loghandler.logQueue)
    log = logging.getLogger(__name__)
    log.addHandler(qh)
    log.setLevel(logLevel)

    log.info('started')

    redis      = getRedis(config)
    sample     = config['monitoring'].get('sample', 0.1)
    interval   = config['monitoring'].get('interval', 1.0)
    interfaces = config['monitoring'].get('interfaces', [])
    devices    = config['monitoring'].get('devices', [])

    allInterfaces = len(interfaces) == 0
    allDevices    = len(devices) == 0
    deviceData = {}
    if source == 'disk':
        partitions = psutil.disk_partitions()
        for partition in partitions:
            device = partition.device.replace('/dev/', '')
            if allDevices or device in devices:
                deviceData[partition.device] = partition

    while True:
        time.sleep(interval)
        log.info('handleing %s' % source)
        data = []
        if source == 'disk':
            try:
                for device in devices:
                    partition = devices[device]
                    usage     = psutil.disk_usage(partition.mountpoint)

                    data.append(('disk.usage.%s.total'   % device, usage.total))
                    data.append(('disk.usage.%s.used'    % device, usage.used))
                    data.append(('disk.usage.%s.free'    % device, usage.free))
                    data.append(('disk.usage.%s.percent' % device, usage.percent))

                io     = psutil.disk_io_counters(perdisk=True)
                iokeys = io.keys()

                for device in devices:
                    if device in iokeys:
                        data.append(('disk.io.%s.read_count'  % device, io.read_count))
                        data.append(('disk.io.%s.write_count' % device, io.write_count))
                        data.append(('disk.io.%s.read_bytes'  % device, io.read_bytes))
                        data.append(('disk.io.%s.write_bytes' % device, io.write_bytes))
                        data.append(('disk.io.%s.read_time'   % device, io.read_time))
                        data.append(('disk.io.%s.write_time'  % device, io.write_time))
            except Exception, e:
                print e

        elif source == 'memory':
            try:
                vm = psutil.virtual_memory()
                data.append(('memory.total',     vm.total))
                data.append(('memory.percent',   vm.percent))
                data.append(('memory.used',      vm.used))
                data.append(('memory.free',      vm.free))

                swap = psutil.swap_memory()
                data.append(('swap.total',     swap.total))
                data.append(('swap.percent',   swap.percent))
                data.append(('swap.used',      swap.used))
                data.append(('swap.free',      swap.free))
            except Exception, e:
                print e

        elif source == 'cpu':
            try:
                times = psutil.cpu_times_percent(interval=sample)

                data.append(('cpu.user',    times.user))
                data.append(('cpu.system',  times.system))
                data.append(('cpu.idle',    times.idle))
                data.append(('cpu.nice',    times.nice))
            except Exception, e:
                print e

        elif source == 'network':
            try:
                io = psutil.net_io_counters(pernic=True)
                iokeys = io.keys()
                for nic in iokeys:
                    if allInterfaces or nic in interfaces:
                        data.append(('network.io.%s.bytes_sent'       % nic, io[nic].bytes_sent))
                        data.append(('network.io.%s.bytes_received'   % nic, io[nic].bytes_recv))
                        data.append(('network.io.%s.packets_sent'     % nic, io[nic].packets_sent))
                        data.append(('network.io.%s.packets_received' % nic, io[nic].packets_recv))
                        data.append(('network.io.%s.errors_in'        % nic, io[nic].errin))
                        data.append(('network.io.%s.errors_out'       % nic, io[nic].errout))
                        data.append(('network.io.%s.dropped_in'       % nic, io[nic].dropin))
                        data.append(('network.io.%s.dropped_out'      % nic, io[nic].dropout))
            except Exception, e:
                print e

        for item, value in data:
            key = 'hakaru.%s' % item
            log.debug('%s = %s' % (key, value))
            redis.publish(key, value)

def start(config):
    """hakaru monitoring - start()

    Start the monitoring process based on the configuration given.

    Assumes that the config parameter is a python dictionary and
    contains an entry named 'monitoring' with the following structure:

    { "redis": { "host":    "127.0.0.1",
                            "port":    6379,
                            "channel": "monitoring"
               },
      "monitoring": { "active":     ["cpu", "disk", "memory", "network"],
                      "interval":   10,
                      "sample":     0.1,
                      "devices":    [],
                      "interfaces": []
                    }
    }
    """
    log = logging.getLogger(__name__)
    log.addHandler(loghandler.QueueLogHandler(loghandler.logQueue))
    log.setLevel(logging.DEBUG)
    log.info('start called')

    if 'monitoring' in config and 'redis' in config:
        mCfg = config['monitoring']

        for item in mCfg['active']:
            log.info('starting worker for %s' % item)
            worker = Process(name=item, target=handleMetric, args=(config, item)).start()
            workers.append(worker)
    else:
        log.error('invalid configuration given: monitoring or redis keys not present')
