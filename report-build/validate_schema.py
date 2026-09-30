from pathlib import Path
import json,urllib.request,jsonschema
from referencing import Registry,Resource
p=Path(__file__).resolve().parent
cache=json.loads((p/'schema-cache.json').read_text()) if (p/'schema-cache.json').exists() else {}
for f in ['page-schema.json','visual-schema.json','extension-schema.json']:
    x=json.loads((p/f).read_text());cache[x['$id']]=x
def retrieve(uri):
    if uri not in cache:
        if not uri.startswith('https://developer.microsoft.com/json-schemas/fabric/'):
            raise ValueError('Unexpected schema host')
        with urllib.request.urlopen(uri,timeout=15) as res:cache[uri]=json.load(res)
    return Resource.from_contents(cache[uri])
reg=Registry(retrieve=retrieve)
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
for row in m:
    jsonschema.Draft7Validator(cache[row['page']['$schema']],registry=reg).validate(row['page'])
    for v in row['visuals']:jsonschema.Draft7Validator(cache[v['$schema']],registry=reg).validate(v)
result={'pages':len(m),'visuals':sum(len(r['visuals']) for r in m),'passed':True,'schemas':list(cache)}
(p/'schema-validation.json').write_text(json.dumps(result,indent=2))
(p/'schema-cache.json').write_text(json.dumps(cache))
print('Microsoft schema validation passed:',result['pages'],'pages,',result['visuals'],'visuals')
