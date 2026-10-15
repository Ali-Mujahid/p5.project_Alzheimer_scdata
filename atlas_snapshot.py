"""Verify and restore the lossless atlas snapshot using Python's standard library."""
from __future__ import annotations
import hashlib,json,pathlib,tarfile,tempfile,os
ROOT=pathlib.Path(__file__).resolve().parent

def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def target(name):
 p=pathlib.PurePosixPath(name)
 if p.is_absolute() or not p.parts or '..' in p.parts or '.git' in p.parts:raise ValueError('Unsafe snapshot member: '+name)
 q=ROOT.joinpath(*p.parts)
 if not q.resolve().is_relative_to(ROOT):raise ValueError('Snapshot path leaves repository: '+name)
 return q

def load_manifests():
 base=ROOT/'snapshot';m=json.loads((base/'manifest.json').read_text())
 f=base/m['file_manifest']
 if digest(f)!=m['file_manifest_sha256']:raise ValueError('File manifest checksum mismatch')
 spec=json.loads(f.read_text());rows=spec['files'];expected={r['path']:r for r in rows}
 if len(expected)!=len(rows) or len(rows)!=m['files']:raise ValueError('Duplicate/missing snapshot inventory')
 for name in expected:target(name)
 return m,spec,expected

class PartStream:
 def __init__(self,paths):self.paths=iter(paths);self.current=None
 def read(self,size=-1):
  if size<0:size=1024*1024
  result=[];remaining=size
  while remaining:
   if self.current is None:
    try:self.current=next(self.paths).open('rb')
    except StopIteration:break
   chunk=self.current.read(remaining)
   if not chunk:self.current.close();self.current=None;continue
   result.append(chunk);remaining-=len(chunk)
  return b''.join(result)
 def close(self):
  if self.current:self.current.close();self.current=None

def verify_parts(m):
 paths=[]
 for r in m['parts']:
  name=pathlib.PurePosixPath(r['path'])
  if len(name.parts)!=1:raise ValueError('Unsafe archive part')
  p=ROOT/'snapshot'/r['path']
  if not p.is_file() or p.is_symlink() or p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:raise ValueError('Archive part corrupt/missing: '+r['path'])
  paths.append(p)
 return paths

def verify_files(expected,hashes=True):
 missing=[];different=[]
 for name,r in expected.items():
  p=target(name)
  if not p.is_file():missing.append(name)
  elif p.is_symlink() or p.stat().st_size!=r['bytes'] or (hashes and digest(p)!=r['sha256']):different.append(name)
 return missing,different

def restore():
 m,spec,expected=load_manifests();paths=verify_parts(m);seen=set();restored=0;stream=PartStream(paths)
 try:
  with tarfile.open(fileobj=stream,mode='r|gz')as tar:
   for member in tar:
    if not member.isfile() or member.name not in expected or member.name in seen:raise ValueError('Unexpected archive member: '+member.name)
    row=expected[member.name]
    if member.size!=row['bytes']:raise ValueError('Archive member size mismatch')
    seen.add(member.name);dest=target(member.name)
    if dest.exists():
     if not dest.is_file() or dest.is_symlink() or digest(dest)!=row['sha256']:raise ValueError('Existing file differs; preserved: '+member.name)
     continue
    dest.parent.mkdir(parents=True,exist_ok=True);src=tar.extractfile(member);h=hashlib.sha256();size=0
    fd,tmp=tempfile.mkstemp(prefix='.atlas-tmp-',dir=dest.parent)
    try:
     with os.fdopen(fd,'wb')as out:
      while chunk:=src.read(1024*1024):out.write(chunk);h.update(chunk);size+=len(chunk)
     if size!=row['bytes'] or h.hexdigest()!=row['sha256']:raise ValueError('Extracted bytes fail checksum: '+member.name)
     # Never replace an existing user file.
     if dest.exists():raise ValueError('Destination appeared during restoration: '+member.name)
     os.link(tmp,dest);os.unlink(tmp);restored+=1
    except BaseException:
     if os.path.exists(tmp):os.unlink(tmp)
     raise
 finally:stream.close()
 if seen!=set(expected):raise ValueError('Snapshot did not contain every inventoried file')
 return {'snapshot_files':len(expected),'restored_files':restored,'bytes':spec['uncompressed_bytes'],'SHA256_verified':True}

def main():
 import argparse
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--restore',action='store_true');args=a.parse_args()
 if args.restore:print(json.dumps(restore(),indent=2))
 else:
  m,s,e=load_manifests();verify_parts(m);missing,different=verify_files(e)
  print(json.dumps({'files':len(e),'missing':missing,'different':different,'valid':not missing and not different},indent=2))
  if missing or different:raise SystemExit(1)
if __name__=='__main__':main()
