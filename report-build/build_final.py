from pathlib import Path
import re,json
R=Path(__file__).resolve().parent.parent
old=(R/'tourism-report.html').read_text(encoding='utf-8')
script=old.split('<script>')[-1].split('</script>')[0]
# Keep audited source records and existing calculation logic, with explicit missing-value handling.
script=script.replace("Number(n).toLocaleString", "Number(n).toLocaleString")
script=script.replace("n==null?'غير متاح'", "n==null||!Number.isFinite(Number(n))?'غير متاح'")
script=script.replace("a.tourists+=r.tourists||0;a.spending+=r.spending||0", "a.tourists=(a.tourists===null||r.tourists===null)?null:a.tourists+r.tourists;a.spending=(a.spending===null||r.spending===null)?null:a.spending+r.spending")
script=script.replace("nf(r.spending/1e9,3),nf(r.spending/r.tourists,0)", "nf(r.spending===null?null:r.spending/1e9,3),nf(r.spending===null||r.tourists===null?null:r.spending/r.tourists,0)")
script=script.replace("(page+1)%4", "(page+1)%6").replace("(page+3)%4", "(page+5)%6").replace("next=3;else return", "next=5;else return")
script=script.replace("function update(){render();", "function update(){render();enhance();")
script=script.replace("'#176b50'", "'#294b3d'").replace("'#a36b32'", "'#a86543'")
script=script.replace('fill="#617168"','fill="#69705d"')
script=script.replace("const numeric=/^[\\d,.]+$/.test(value)","const numeric=/^[\\d,.]+$/.test(value)")
# Don't boot until extension functions are available.
script=re.sub(r'update\(\);\s*$', '', script)
(R/'tourism-final-data.js').write_text(script,encoding='utf-8')
tabs=['المشهد العام','المناطق','أنماط الرحلات','الإنفاق','الوجهات','المصادر والمنهجية']
nav=''.join(f'<button role="tab" id="tab{i}" aria-controls="p{i}" aria-selected="{str(i==0).lower()}" data-page="{i}"><span class="nav-title">{t}</span></button>' for i,t in enumerate(tabs))
pages=''.join(f'<section class="page" id="p{i}" role="tabpanel" aria-labelledby="tab{i}"'+('' if i==0 else ' hidden')+'></section>' for i in range(6))
html=f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f5f0e6"><title>السياحة في المملكة العربية السعودية | التقرير الكامل</title><link rel="stylesheet" href="assets/heritage/fonts.css"><link rel="stylesheet" href="tourism-final.css"></head><body><a class="skip" href="#report">انتقل إلى محتوى التقرير</a>
<header class="masthead"><div><h1>السياحة في المملكة العربية السعودية</h1><p>قراءة في المكان، وحركة السياح، والقيمة الاقتصادية.</p></div><div class="edition"><span>2021 — 2025</span><small>تقرير بصري تفاعلي</small></div><button id="print" class="print-button">طباعة التقرير كاملًا</button></header>
<div class="nav-shell"><nav id="nav" role="tablist" aria-label="أقسام التقرير">{nav}</nav></div>
<main id="report" class="content"><div class="toolbar"><div class="filter" id="yearLabel"><label for="year">السنة</label><select id="year"><option>2025</option><option>2024</option><option>2023</option><option>2022</option><option>2021</option></select></div><div class="filter" id="typeLabel"><label for="type">نوع السياحة</label><select id="type"><option value="all">محلية + وافدة</option><option>محلية</option><option>وافدة</option></select></div><button id="reset" class="reset">إعادة الضبط</button><span id="scope" class="hint"></span></div><span id="reportStatus" class="sr-only" role="status" aria-live="polite"></span>{pages}</main>
<footer class="site-footer"><strong>المملكة العربية السعودية</strong><p>نسخة تحليلية مستقلة · بيانات محفوظة للأعوام 2021–2025 · تاريخ المراجعة: 29 سبتمبر 2026</p><span>تحديث ملف المصدر لا يحدّث الصفحة تلقائيًا. الإنفاق السياحي لا يساوي الأرباح أو المساهمة في الناتج المحلي.</span></footer>
<script src="tourism-final-data.js"></script><script src="tourism-final.js"></script></body></html>'''
(R/'tourism-final.html').write_text(html,encoding='utf-8')
print('Built tourism-final.html and source-data logic.')
