#!/usr/bin/env python3
"""Remove non-runtime build metadata from a release ZIP without changing PT_LOAD bytes.

Preserves executable load segments and refreshes runtime checksums. Run before computing the final release archive SHA-256.
"""
from pathlib import Path
import argparse, hashlib, re, struct, tempfile, zipfile

def elf_clean(data,name):
 if not data.startswith(b'\x7fELF'):return data
 assert data[4:6]==b'\x02\x01',name
 b=bytearray(data);shoff=struct.unpack_from('<Q',b,40)[0];ents,n,idx=struct.unpack_from('<HHH',b,58)
 def sh(i):return struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*ents)
 names=sh(idx);strings=data[names[4]:names[4]+names[5]]
 phoff=struct.unpack_from('<Q',data,32)[0];phents,phnum=struct.unpack_from('<HH',data,54);loads=[]
 for i in range(phnum):
  p=struct.unpack_from('<IIQQQQQQ',data,phoff+i*phents)
  if p[0]==1:loads.append((p[2],p[2]+p[5]))
 removed=[]
 for i in range(n):
  s=sh(i);label=strings[s[0]:].split(b'\0',1)[0].decode(errors='replace')
  if (label.startswith(('.debug','.zdebug','.stab')) or label in {'.comment','.gnu_debuglink'}) and not s[2]&2:
   a,z=s[4],s[4]+s[5];assert not any(a<y and z>x for x,y in loads),label
   b[a:z]=bytes(z-a);struct.pack_into('<Q',b,shoff+i*ents+32,0);removed.append(label)
 for a,z in loads:assert b[a:z]==data[a:z],name
 if removed:pass
 return bytes(b)
def zip_clean(src,dest):
 with zipfile.ZipFile(src) as z:
  files={i.filename:z.read(i) for i in z.infolist() if not i.is_dir() and not any(p in {'__MACOSX','.DS_Store'} or p.startswith('._') for p in Path(i.filename).parts)}
  for name,data in files.copy().items():files[name]=elf_clean(data,src.name+'!'+name)
  for name,data in files.copy().items():
   if name.endswith('runtime.sha256'):
    parent=str(Path(name).parent);lines=[]
    for line in data.decode().splitlines():
     _,filename=line.split(None,1);key=parent+'/'+filename.strip().lstrip('*');assert key in files,key
     lines.append(hashlib.sha256(files[key]).hexdigest()+'  '+filename.strip())
    files[name]=('\n'.join(lines)+'\n').encode()
  dest.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as o:
   for name,data in files.items():
    orig=z.getinfo(name);info=zipfile.ZipInfo(name,(2026,10,16,0,0,0));info.external_attr=orig.external_attr;info.compress_type=zipfile.ZIP_DEFLATED;o.writestr(info,data)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        clean = Path(folder) / args.archive.name
        zip_clean(args.archive, clean)
        with zipfile.ZipFile(clean) as archive:
            for name in archive.namelist():
                data = archive.read(name)
                if data.startswith(b'\x7fELF') and re.search(rb'/(?:Users|Volumes|home)/[^\x00\s]+', data):
                    raise SystemExit('Host path remains in ELF: ' + name)
        args.archive.write_bytes(clean.read_bytes())
    print('Release ZIP sanitized; executable load segments unchanged.')
