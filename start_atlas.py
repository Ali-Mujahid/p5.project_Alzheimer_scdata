#!/usr/bin/env python3
"""Run the complete offline atlas on any computer with Python3.10+."""
import argparse,functools,http.server,pathlib,webbrowser
from atlas_snapshot import ROOT,load_manifests,restore,verify_files

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=56404);p.add_argument('--open',action='store_true',help='Open your web browser');p.add_argument('--check',action='store_true',help='Restore and verify files, then exit');a=p.parse_args()
 _,_,expected=load_manifests();missing,different=verify_files(expected,hashes=True)
 if different:raise SystemExit("Existing snapshot files differ and were preserved: "+repr(different))
 if missing:
  print('Restoring included snapshot data…',flush=True);print(restore(),flush=True)
  missing,different=verify_files(expected,hashes=True)
  if missing or different:raise SystemExit('Restored snapshot verification failed')
 if a.check:
  missing,different=verify_files(expected)
  if missing or different:raise SystemExit('Snapshot verification failed: '+repr({'missing':missing,'different':different}))
  print('Complete atlas snapshot verified.');return
 root=ROOT/'outputs/p5_workflow';url=f'http://127.0.0.1:{a.port}/full_workflow_20261014/atlas_preview/index.html#qc-progress'
 handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
 try:server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler)
 except OSError as e:raise SystemExit(f'{e}. Choose another port with --port 56405.')
 print('Atlas: '+url,flush=True);print('Press Ctrl+C to stop. No Internet/CDN is required after downloading.',flush=True)
 if a.open:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
