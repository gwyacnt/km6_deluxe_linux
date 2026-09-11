#!/usr/bin/env python3
"""Local Firefox rendering benchmark over localhost Marionette; no browsing data."""
import argparse
import json
import socket
import time


class Marionette:
    def __init__(self):
        self.s = socket.create_connection(('127.0.0.1', 2828), 10)
        self.s.settimeout(45)
        self.seq = 0
        self.receive()

    def receive(self):
        size = b''
        while not size.endswith(b':'):
            chunk = self.s.recv(1)
            if not chunk:
                raise EOFError('Marionette disconnected')
            size += chunk
        data = b''
        while len(data) < int(size[:-1]):
            chunk = self.s.recv(int(size[:-1]) - len(data))
            if not chunk:
                raise EOFError('Marionette disconnected')
            data += chunk
        return json.loads(data)

    def call(self, name, args):
        self.seq += 1
        data = json.dumps([0, self.seq, name, args]).encode()
        self.s.sendall(str(len(data)).encode() + b':' + data)
        response = self.receive()
        if response[2]:
            raise RuntimeError(response[2])
        return response[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    m = Marionette()
    m.call('WebDriver:NewSession', {'capabilities': {}})
    m.call('WebDriver:SetTimeouts', {'script': 60000})
    m.call('WebDriver:SetWindowRect', {'width': 1500, 'height': 900})
    m.call('WebDriver:Navigate', {'url': 'about:blank'})
    m.call('Marionette:SetContext', {'value': 'chrome'})
    graphics = m.call('WebDriver:ExecuteAsyncScript', {
        'script': 'const done=arguments[arguments.length-1]; ChromeUtils.importESModule("resource://gre/modules/Troubleshoot.sys.mjs").Troubleshoot.snapshot().then(s=>done(s.graphics));',
        'args': [], 'newSandbox': True})
    m.call('Marionette:SetContext', {'value': 'content'})
    script = r'''
const done = arguments[arguments.length - 1];
document.body.style.cssText = 'margin:0;background:#132238;color:white;font:18px sans-serif';
document.body.innerHTML = '<h1>KM6 local rendering benchmark</h1>';
const boxes = [];
for (let i=0;i<160;i++) {
 let e=document.createElement('div');
 e.style.cssText=`position:absolute;width:64px;height:48px;left:${(i%20)*70}px;top:${80+Math.floor(i/20)*70}px;background:hsl(${i*13},65%,50%);border-radius:8px`;
 document.body.append(e); boxes.push(e);
}
let frames=[], start=performance.now(), last=start;
function tick(now) {
 if (now-start>1000) frames.push(now-last);
 last=now;
 boxes.forEach((e,i)=>e.style.transform=`translateY(${Math.sin(now/300+i)*16}px)`);
 if(now-start<11000) return requestAnimationFrame(tick);
 frames.sort((a,b)=>a-b);
 const begin=performance.now();let count=0, value=1;
 while(performance.now()-begin<1000) {
  for(let i=0;i<10000;i++) value=Math.imul(value^i,1664525)+1013904223|0;
  count+=10000;
 }
 done({frames:frames.length, median_ms:frames[Math.floor(frames.length*.5)],
       p95_ms:frames[Math.floor(frames.length*.95)],
       over_25ms:frames.filter(x=>x>25).length, integer_iterations:count});
}
requestAnimationFrame(tick);
'''
    result = m.call('WebDriver:ExecuteAsyncScript', {'script': script, 'args': [], 'newSandbox': True})
    print(json.dumps({'label': args.label, 'timestamp': time.time(), 'result': result, 'graphics': graphics}, indent=2))
    # DeleteSession closes the benchmark window. Restart the disposable browser
    # before the next run rather than benchmarking a hidden/closed context.
    m.call('WebDriver:DeleteSession', {})


if __name__ == '__main__':
    main()
