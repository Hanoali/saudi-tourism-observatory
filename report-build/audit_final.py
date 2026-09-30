from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parent.parent
# Re-run source-cell reconciliation without overwriting earlier audit documents.
code=(R/'report-build/audit_report.py').read_text(encoding='utf-8')
namespace={'__file__':str(R/'report-build/audit_report.py')}
exec(compile(code.split("report={'source_sha256'")[0],str(R/'report-build/audit_report.py'),'exec'),namespace)
summary=namespace['summary']; checks=namespace['checks']; S=namespace['S']
payload={'checked_on':'2026-09-29','source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'summary':summary,'checks':checks,'notes':['Known source rounding differences are retained.','Missing governorate cells propagate to unavailable annual totals.']}
(R/'report-build/final-audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
for group in ['annual_cells','monthly_cells','governorate_cells','source_ratios']:
    assert summary[group]['failed']==0,(group,summary[group])
original=json.loads(re.search(r'const DATA\s*=\s*(\{.*?\});',(R/'tourism-final-data.js').read_text(encoding='utf-8'),re.S).group(1))
for key in ['national','regional','monthly','governorates']:
    assert original[key]==namespace['d'][key],key
print(json.dumps(summary)); print('Final dataset equals source-audited records. Core source-cell comparisons passed.')
