#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import time
import sys

from ws4py.messaging import TextMessage
from ws4py.client.threadedclient import WebSocketClient

import libardrone

import state

'''
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

win = pg.GraphicsWindow(title="Basic plotting examples")
win.resize(1000,600)

pg.setConfigOptions(antialias=True)
'''

## starting myo states

class PairState(state.BaseState):

    def __init__(self, *args, **kwargs):
        super(PairState, self).__init__(*args, **kwargs)
        self._priority = 42
        self._keep_me = False

    def start(self, data):
        event = data[1]
        print('Paired to Myo: {0}'.format('.'.join((str(v) for v in event['version']))))

    def update(self, data):
        return False

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        if data[0] != 'event':
            return False
        event = data[1]
        if event['type'] == 'paired':
            return True
        return False




class ConnectState(state.BaseState):

    def __init__(self, *args, **kwargs):
        super(ConnectState, self).__init__(*args, **kwargs)
        self._priority = 42
        self._keep_me = False

    def start(self, data):
        event = data[1]
        print('Connected to Myo: {0}'.format('.'.join((str(v) for v in event['version']))))

    def update(self, data):
        return False

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        if data[0] != 'event':
            return False
        event = data[1]
        if event['type'] == 'connected':
            return True
        return False




### drone control states

class TakeOffState(state.BaseState):

    def __init__(self, drone, *args, **kwargs):
        super(TakeOffState, self).__init__(*args, **kwargs)
        self._priority = 42
        self._drone = drone

    def start(self, data):
        self._drone.takeoff()

        self._start_time = time.time()
        self._started = False

        '''
        self._plotX = win.addPlot(title="Vx")
        self._curveX = self._plotX.plot(pen='y')
        self._plotY = win.addPlot(title="Vy")
        self._curveY = self._plotY.plot(pen='y')
        self._plotZ = win.addPlot(title="Vz")
        self._curveZ = self._plotZ.plot(pen='y')
        self._plotAngle = win.addPlot(title="Angle")
        self._curveAngle = self._plotAngle.plot(pen='y')
        '''
        data = {'x' : 0, 'y' : 0, 'z' : 0}
        self._state_machine = state.StateMachine()
        self._state_machine.add_state(OrientationState(self._drone, data))
        self._state_machine.add_state(LandState(self._drone))
        print('waiting')

    def update(self, data):
        wait_time = time.time() - self._start_time
        if wait_time < 3:
            return True
        if self._started == False:
            self._started = True
            self._drone.hover()
        return self._state_machine.update(data)

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        if data[0] != 'event':
            return False
        event = data[1]
        if event['type'] == 'pose' and event['pose'] == 'fist':
            return True
        return False


class LandState(state.BaseState):

    def __init__(self, drone, *args, **kwargs):
        super(LandState, self).__init__(*args, **kwargs)
        self._priority = 42
        self._drone = drone

    def start(self, data):
        self._drone.land()
        self.machine.kill_self()

    def update(self, data):
        return False

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        if data[0] != 'event':
            return False
        event = data[1]
        if event['type'] == 'pose' and event['pose'] == 'fist':
            return True
        return False


class OrientationState(state.BaseState):

    def __init__(self, drone, data, *args, **kwargs):
        super(OrientationState, self).__init__(*args, **kwargs)
        self._data = data
        self._priority = 10
        self._next_state = MoveDroneState(drone, data)

    def start(self, data):
        event = data[1]
        gyroscope = event['gyroscope']
        orientation = event['orientation']
        self._last_gyroscope = gyroscope
        self._data['x'] = gyroscope[0] / 100 # wirst axe ?
        self._data['y'] = gyroscope[1] / 100# orientation['y'] * 2 # up/down
        self._data['z'] = gyroscope[2] / 100# left/right

    def update(self, data):
        return False

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        if data[0] != 'event':
            return False
        event = data[1]
        if event['type'] == 'orientation':
            gyroscope = event['gyroscope']
            if not hasattr(self, '_last_gyroscope') or math.fabs(self._last_gyroscope[0] - gyroscope[0]) > 10 or math.fabs(self._last_gyroscope[1] - gyroscope[1]) > 10 or math.fabs(self._last_gyroscope[2] - gyroscope[2]) > 10:
                return True
        return False


class MoveDroneState(state.BaseState):

    def __init__(self, drone, data, *args, **kwargs):
        super(MoveDroneState, self).__init__(*args, **kwargs)
        self._drone = drone
        self._data = data

        '''
        self._curveX = curveX
        self._curveY = curveY
        self._curveZ = curveZ
        self._curveAngle = curveAngle
        self._valuesX = []
        self._valuesY = []
        self._valuesZ = []
        self._valuesAngle = []
        '''
        self._time = time.time()

    def start(self, data):
        pass

    def update(self, data):

        def translate(value):
            return max(min(float(int((value)  * 10)) / 10, 1), -1)

        waiting_time = time.time() - self._time
        if waiting_time < 0.1:
            return True
        self._time = time.time()

        Vx = -translate(self._data['z'])
        Vy = -translate(self._data['y'])
        angle = 0#-translate('z')
        self._drone.move_drone(Vx, Vy, 0, angle)
        print('{0: <10} {1: <10} {2: <10}'.format(Vx, Vy, angle))
        #print('{0: <10} {1: <10} batt: {2: <10}'.format(self._drone.navdata[0]['Vx'], self._drone.navdata[0]['Vy'], angle))
        #self.updateCurves(Vx, 0, Vy, angle)
        return True

    '''
    def updateCurves(self, Vx, Vy, Vz, angle):
        def appendValue(array, curve, value):
            array.append(value)
            if len(array) > 100:
                array = array[1:]
            curve.setData(array)

        appendValue(self._valuesX, self._curveX, Vx)
        appendValue(self._valuesY, self._curveY, Vy)
        appendValue(self._valuesZ, self._curveZ, Vz)
        appendValue(self._valuesAngle, self._curveAngle, angle)
    '''

    def end(self, data=None):
        pass

    def should_trigger(self, data):
        return True




# MyoDrone !

class MyoDrone(WebSocketClient):

    def __init__(self):
        super(MyoDrone, self).__init__('ws://127.0.0.1:10138/myo/3', protocols=['http-only', 'chat'])
        self._drone = libardrone.ARDrone2()
        self._state_machine = state.StateMachine()
        self._state_machine.add_state(TakeOffState(self._drone))
        self._state_machine.add_state(ConnectState())
        self._state_machine.add_state(PairState())

        self.connect()

    def close(self, *args, **kwargs):
        super(MyoDrone, self).close(*args, **kwargs)
        self._drone.land()

    def opened(self):
        print('Myo websocket connected')

    def closed(self, code, reason=None):
        print('Myo websocket closed: {0}'.format(reason))

    def received_message(self, message):
        decoded_message = json.loads(str(message))

        if self._state_machine.update(decoded_message) == False:
            pass
            # print('nothing to do for:\n{0}'.format(message))

### Websocket client

if __name__ == '__main__':
    ws = MyoDrone()

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
        exit()

    '''
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):                                        
        pg.QtGui.QApplication.exec_()
    '''
