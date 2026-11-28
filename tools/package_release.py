"""Package only the release software, sources, docs, proofs and QA reports."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION=json.loads((ROOT/'design/config.json').read_text())['version']
DIRECTORIES=['desktop','web','sources','design','tools','qa','specimen','LICENSES']
DOCS=['README.md','OFL.txt','AUTHORS.md','FONTLOG.md','PROVENANCE.md']
def files():
 return sorted([p for d in DIRECTORIES for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not any(part.startswith('.') for part in p.relative_to(ROOT).parts)]+[ROOT/n for n in DOCS])
if __name__=='__main__':
 for n in ['validation','coretext','source-roundtrip','browser','refinement-checks']:
  assert json.loads((ROOT/'qa'/f'{n}.json').read_text())['pass'],n+' has not passed'
 paths=files();manifest=ROOT/'MANIFEST.sha256';manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in paths))
 target=ROOT/f'AT-KPN-{VERSION}.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in paths+[manifest]:z.write(p,f'AT-KPN-{VERSION}/'+p.relative_to(ROOT).as_posix())
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for line in manifest.read_text().splitlines():
   sha,name=line.split('  ',1);assert hashlib.sha256(z.read(f'AT-KPN-{VERSION}/'+name)).hexdigest()==sha,name
 report={'pass':True,'archive':target.name,'bytes':target.stat().st_size,'files':len(paths)+1,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'verification':'ZIP CRC and SHA-256 of every manifest entry passed'}
 (ROOT/'PACKAGE-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
