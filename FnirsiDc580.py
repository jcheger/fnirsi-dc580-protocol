#!/usr/bin/python3

import logging
import serial
import threading
import time

class Fnirsi_Dc580:

  prot = {0:'OK', 1:'OVP', 2:'OCP', 3:'OPP', 4:'OTP', 5:'OHP'}

  def __init__(self, dev):
    try:
      self.cb = None
      self.thread = None
      self.stop = False

      self.socket = serial.Serial(dev, baudrate=115200, xonxoff=True, timeout=0.2)

    except Exception as e:
      logging.fatal(e)
      exit()

  # thread
  def read(self):
    while True:
      if self.stop:
        self.stop = False
        return

      try:
        t = None
        while not t:
          t = self.socket.read(100).decode()
        r = {'raw': t}

        s = t.lstrip('MB').split('A')[:-1]
        l = len(s)

        r['v'] = int(s[0]) / 100
        r['i'] = int(s[1]) / 1000
        r['p'] = int(s[2]) / 100
        r['temp'] = int(s[4])
        r['mode'] = 'CC' if int(s[5]) else 'CV'
        r['prot'] = self.prot.get(int(s[6]))

        if l >  7: r['v_set'] = int(s[7]) / 100
        if l >  8: r['i_set'] = int(s[8]) / 1000
        if l >  9: r['ovp'] = int(s[9]) / 100
        if l > 10: r['ocp'] = int(s[10]) / 1000
        if l > 11: r['opp'] = int(s[11]) / 100
        if l > 12: r['ohp_enable'] = bool(int(s[12]))
        if l > 13: r['ohp_h'] = int(s[13])
        if l > 14: r['ohp_m'] = int(s[14])
        if l > 15: r['ohp_s'] = int(s[15])
        if l > 16: r['enable'] = bool(int(s[16]))

        if self.cb and r:
          self.cb(r)

      except Exception as e:
        logging.error(e)

  def set(self, cmd, value=None):

    if cmd == 'connect':
      self.write(b'Q')
    elif cmd == 'curr':
      self.write(bytearray('I{:0>4d}'.format(int(value*1000)).encode()))
    elif cmd == 'disconnect':
      self.write(b'W')
    elif cmd == 'enable':
      if value:
        self.write(b'N')
      else:
        self.write(b'F')
    # elif cmd == 'm1':
    #   self.write(b'O')
    # elif cmd == 'm2':
    #   self.write(b'P')
    elif cmd == 'ocp':
      self.write(bytearray('D{:0>4d}'.format(int(value*1000)).encode()))
    elif cmd == 'ok':
      self.write(b'Z')
    elif cmd == 'ohp':
      try:
        h, m, s = value.split(':')
        self.write(bytearray('H{:0>2d}'.format(int(h)).encode()))
        time.sleep(0.2)
        self.write(bytearray('M{:0>2d}'.format(int(m)).encode()))
        time.sleep(0.2)
        self.write(bytearray('S{:0>2d}'.format(int(s)).encode()))
      except:
        pass
    elif cmd == 'ohp_enable':
      if value:
        self.write(b'X')
      else:
        self.write(b'Y')
    elif cmd == 'opp':
      self.write(bytearray('E{:0>4d}'.format(int(value*10)).encode()))
    elif cmd == 'ovp':
      self.write(bytearray('B{:0>4d}'.format(int(value*100)).encode()))
    elif cmd == 'volt':
      self.write(bytearray('V{:0>4d}'.format(int(value*100)).encode()))
    else:
      logging.error(f'unknown command [{cmd}]')

  def start(self):
    self.thread = threading.Thread(daemon=True, target=self.read).start()
    self.set('connect')

  def stop(self):
    self.set('disconnect')
    self.stop = True

  def write(self, cmd):
    logging.info(cmd + b'\r\n')
    self.socket.write(cmd + b'\r\n')
    time.sleep(0.5) # write burst could fail

if __name__ == "__main__":

  logging.basicConfig(
    level   = logging.DEBUG,
    format  = '%(asctime)s %(levelname)8s: |%(module)s.%(funcName)s:%(lineno)s| - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
  )

  def cb(val):
    logging.debug(str(val))

  inst = Fnirsi_Dc580('/dev/ttyUSB0')
  inst.cb = cb
  inst.start()
  inst.set('volt', 1.23)
  inst.set('curr', 3.21)
  inst.set('enable', True)

  input("\nPress Enter to quit\n\n")
  exit()
