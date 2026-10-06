"""Loopback-only model review and ratings; no dependency on an open Blender."""
import argparse,json,mimetypes,re,socket,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
from survey import read,write

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--port',type=int,default=8766);a=p.parse_args();root=a.root.resolve();web=root/'web';lock=threading.Lock()
    entries={e['id'] for e in read(root/'state.json')['entries']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,value,status=200):
            data=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def allowed(self):return self.headers.get('Host') in (f'127.0.0.1:{a.port}',f'localhost:{a.port}')
        def do_GET(self):
            if not self.allowed():return self.reply({'error':'Invalid host'},403)
            path=unquote(urlsplit(self.path).path)
            if path=='/api/index':return self.reply(read(web/'index.json'))
            if path=='/api/ratings':return self.reply(read(root/'ratings.json'))
            candidate=(web/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if web not in candidate.parents or not candidate.is_file():return self.reply({'error':'Not found'},404)
            data=candidate.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(candidate)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-cache');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            if not self.allowed() or self.headers.get('X-Motion-Lab')!='review':return self.reply({'error':'Local review requests only'},403)
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{a.port}',f'http://localhost:{a.port}'):return self.reply({'error':'Invalid origin'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=10000:raise ValueError('Invalid body size')
                data=json.loads(self.rfile.read(length));entry=data['entry']
                if entry not in entries:raise ValueError('Unknown survey entry')
                if self.path=='/api/ratings':
                    rating=data['rating'];valid={'action':{'','clear','partial','miss'},'plausibility':{'','convincing','cleanup','broken'},'decision':{'','keep','cleanup','reject'}}
                    if set(rating)-set(valid)-{'notes'}:raise ValueError('Invalid rating field')
                    for field,values in valid.items():
                        if rating.get(field,'') not in values:raise ValueError('Invalid rating')
                    if not isinstance(rating.get('notes',''),str) or len(rating.get('notes',''))>2000:raise ValueError('Invalid notes')
                    with lock:
                        ratings=read(root/'ratings.json');ratings[entry]=dict(rating,updated=time.time());write(root/'ratings.json',ratings)
                    return self.reply({'saved':True})
                if self.path=='/api/blender':
                    item=next(e for e in read(web/'index.json')['entries'] if e['id']==entry)
                    if item['status']!='complete':raise ValueError('This clip is not complete yet')
                    job=item['job'];assert re.fullmatch(r'[A-Za-z0-9_]+',job)
                    code="import bpy\nns=bpy.app.driver_namespace.get('motion_lab_ui')\nassert ns is not None, 'Open Motion Lab in Blender first'\nassert ns['JOB'] is None, 'Wait for the current Blender generation'\nns['refresh_history']()\nns['load_result']("+repr(job)+",True)\nbpy.context.scene.ml_history="+repr(job)+"\n"
                    try:
                        with socket.create_connection(('127.0.0.1',9876),timeout=5) as conn:
                            conn.settimeout(45);conn.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode());raw=b''
                            while True:
                                chunk=conn.recv(65536)
                                if not chunk:raise RuntimeError('Blender connection closed')
                                raw+=chunk
                                try:response=json.loads(raw);break
                                except json.JSONDecodeError:continue
                                if len(raw)>2_000_000:raise RuntimeError('Blender response too large')
                        if response.get('status')!='success':raise RuntimeError(str(response.get('message',response)))
                        return self.reply({'loaded':job})
                    except OSError:raise ValueError('Open Blender and start its MCP server, then try again. Generation and browser review do not require Blender.')
                return self.reply({'error':'Not found'},404)
            except Exception as exc:return self.reply({'error':str(exc)},400)
    print(f'Review: http://127.0.0.1:{a.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
if __name__=='__main__':main()
