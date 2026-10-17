#!/usr/bin/env python3
"""Run the complete offline atlas on any computer with Python3.10+."""
import argparse,http.server,webbrowser
from atlas_snapshot import ROOT,load_manifests,restore,verify_files
from atlas_updates import PREFIX,handler_factory,load_update

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=56404);p.add_argument('--open',action='store_true',help='Open your web browser');p.add_argument('--check',action='store_true',help='Restore and verify files, then exit');p.add_argument('--base-snapshot',action='store_true',help='Serve the original 15 October snapshot without the reviewed overlay');a=p.parse_args()
 if not 1<=a.port<=65535:p.error('--port must be between 1 and 65535')
 try:update,routes=(None,{})if a.base_snapshot else load_update(ROOT)
 except (OSError,ValueError)as error:raise SystemExit('Atlas update rejected; files preserved: '+str(error))
 _,_,expected=load_manifests();missing,different=verify_files(expected,hashes=True)
 if different:raise SystemExit("Existing snapshot files differ and were preserved: "+repr(different))
 if missing:
  print('Restoring included snapshot data…',flush=True);print(restore(),flush=True)
  missing,different=verify_files(expected,hashes=True)
  if missing or different:raise SystemExit('Restored snapshot verification failed')
 if a.check:
  print('Complete atlas snapshot verified.'+(' Reviewed overlay '+update['update_id']+' verified.'if update else ' Original base snapshot selected.'));return
 root=ROOT/'outputs/p5_workflow';url=f'http://127.0.0.1:{a.port}'+PREFIX+'index.html'+('#rna'if update else'#qc-progress')
 handler=handler_factory(root,routes)
 try:server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler)
 except OSError as e:raise SystemExit(f'{e}. Choose another port with --port 56405.')
 print('Atlas: '+url,flush=True)
 print('Display: '+(update['update_id']if update else'original 15 October snapshot'),flush=True)
 print('Press Ctrl+C to stop. No Internet/CDN is required after downloading.',flush=True)
 if a.open:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
