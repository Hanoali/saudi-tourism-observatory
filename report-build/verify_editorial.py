from pathlib import Path
import json, re, hashlib
import openpyxl

root = Path(__file__).resolve().parent.parent
source = root.parent / 'jmye_almnatq_2021_2025_3ea42fcd2d.xlsx'
book = openpyxl.load_workbook(source, read_only=True, data_only=True)
sheet = list(book['G1'].values)
data = json.loads((root/'report-build/data.json').read_text(encoding='utf-8'))
report_html = (root/'tourism-report.html').read_text(encoding='utf-8')
embedded = json.loads(re.search(r'const DATA\s*=\s*(\{.*?\});', report_html, re.S).group(1))
checks = []
annual = []
for c, year in enumerate(range(2021,2026), 3):
    totals = {}
    for key, row, scale in [('Tourists',24,1000),('OvernightStays',25,1000),('SpendingSAR',26,1e6)]:
        expected = sheet[row-1][c]*scale
        for label, records in [('data.json',data['national']),('tourism-report.html',embedded['national'])]:
            actual = sum(r[key] for r in records if r['Year']==year)
            passed = abs(actual-expected) < (0.02 if key=='SpendingSAR' else 0.001)
            checks.append({'year':year,'metric':key,'dataset':label,'cell':f'G1!{chr(65+c)}{row}','source':expected,'actual':actual,'passed':passed})
        totals[key]=expected
    totals['year']=year
    totals['averageStay']=totals['OvernightStays']/totals['Tourists']
    assert abs(totals['averageStay']-sheet[26][c])<1e-6  # Source rounding of nights/counts in 2021–2022.
    annual.append(totals)
assert all(c['passed'] for c in checks)
latest=annual[-1]; previous=annual[-2]
growth=(latest['Tourists']/previous['Tourists']-1)*100
spend_growth=(latest['SpendingSAR']/previous['SpendingSAR']-1)*100

# Real scaled positions; zero-based y axis, explicit values and units.
xs=[55,165,275,385,495]
ys=[177-r['Tourists']/1e6/150*142 for r in annual]
svg='<svg viewBox="0 0 550 215" role="img" aria-label="عدد السياح المحليين والوافدين بالمليون من 2021 إلى 2025"><title>عدد السياح المحليين والوافدين، مليون سائح</title>'
for value in [0,50,100,150]:
    y=177-value/150*142
    svg+=f'<path d="M45 {y}H515" stroke="#294b3d" opacity=".16"/><text x="35" y="{y+4}" text-anchor="end">{value}</text>'
svg+='<polyline points="'+' '.join(f'{x},{y:.3f}' for x,y in zip(xs,ys))+'" fill="none" stroke="#a86543" stroke-width="3"/>'
for r,x,y in zip(annual,xs,ys):
    svg+=f'<circle cx="{x}" cy="{y}" r="4" fill="#a86543"/><text x="{x}" y="{y-13}" text-anchor="middle">{r["Tourists"]/1e6:.2f}</text><text x="{x}" y="204" text-anchor="middle">{r["year"]}</text>'
svg+='</svg>'
html=(root/'concepts.html').read_text(encoding='utf-8')
html=html.replace('١ · الأطلس','١ · التصميم المختار').replace('١. أطلس المملكة','السياحة في المملكة العربية السعودية').replace('<strong>أطلس المملكة</strong>','')
html=html.replace('أربع طرق لرؤية المملكة.','السياحة في المملكة العربية السعودية.').replace('اختاري الاتجاه الأقرب لكِ. كبّري أي نموذج لاستكشافه، ثم عودي للمقارنة.','التصميم المختار بعد مراجعة مؤشرات 2025 والسلسلة الزمنية 2021–2025.')
html=html.replace('معاينات تصميمية أولية • الأرقام والرسوم توضيحية وليست إحصاءات معتمدة','التصميم المختار: أرقام مطابقة لملف البيانات G1 • التصاميم البديلة ما زالت أمثلة توضيحية')
start=html.index('<article class="concept" id="atlas">'); end=html.index('</article>',start)+len('</article>')
section=html[start:end]
section=re.sub(r'<div class="a-stats">.*?</div></div>\s*<div class="a-bottom">',f'''<div class="a-stats"><div><span>السياح المحليون والوافدون</span><strong><bdi>{latest['Tourists']/1e6:.2f}</bdi><span> مليون سائح</span></strong><small>زوار المبيت · نمو {growth:.2f}% عن 2024</small></div><div><span>إنفاق السياح</span><strong><bdi>{latest['SpendingSAR']/1e9:.2f}</bdi><span> مليار ر.س</span></strong><small>نمو {spend_growth:.2f}% عن 2024</small></div><div><span>متوسط مدة الإقامة</span><strong><bdi>{latest['averageStay']:.2f}</bdi><span> ليلة / رحلة</span></strong><small>إجمالي الليالي ÷ إجمالي السياح</small></div></div>
<div class="a-bottom">''',section,flags=re.S)
section=section.replace('اتجاه حركة السياحة • رسم توضيحي','المحلية + الوافدة • مليون سائح • المصدر: G1')
section=section.replace('<div class="chart-slot" data-color="#a86543"></div>',f'<div class="chart-slot" data-verified="true">{svg}</div>')
section=section.replace('تصوّر تحريري / بيانات توضيحية','المصدر: ملف البيانات G1 / المؤشرات الرئيسية للسياحة')
table=''.join(f'<tr><th scope="row">{r["year"]}</th><td>{r["Tourists"]:,.0f}</td><td>{r["SpendingSAR"]/1e9:.2f}</td><td>{r["averageStay"]:.2f}</td></tr>' for r in annual)
notes=f'''<details class="source-details"><summary>المصادر وطريقة احتساب الأرقام</summary><p>النطاق: السياحة المحلية والوافدة (زوار المبيت). «الداخلية» هي مجموعهما وليست فئة ثالثة. لا يُفسّر العدد باعتباره عدد أفراد فريدين.</p><p>المصدر الحسابي: ملف <a href="../jmye_almnatq_2021_2025_3ea42fcd2d.xlsx">بيانات السياحة 2021–2025</a>، ورقة G1، الخلايا D24:H27؛ آخر تحديث مكتوب في الملف: 12-04-2026. طابقتُ إجمالياته مع البيانات المضمّنة في التقرير الأصلي.</p><div class="source-table"><table><thead><tr><th>السنة</th><th>السياح</th><th>الإنفاق / مليار ريال</th><th>ليلة / رحلة</th></tr></thead><tbody>{table}</tbody></table></div><p>متوسط 2025 = 1,111,752,334 ليلة ÷ 122,578,300 سائح = {latest['averageStay']:.8f} ليلة. المتوسط موزون بحجم الرحلات، وليس متوسطًا بسيطًا لمتوسطي المحلية والوافدة. يُجرى التقريب للعرض فقط.</p><p>التحقق الخارجي: <a href="https://www.spa.gov.sa/en/N2615138" target="_blank" rel="noopener">إعلان وزارة السياحة عبر واس، 18 يونيو 2026</a> يذكر نحو 123 مليون سائح و304 مليارات ريال، ونموًا بنحو 6% و7%؛ وهي متوافقة مع التقريب من ملف البيانات. الإعلان لا يثبت كل منزلة عشرية أو متوسط الإقامة؛ مصدرهما الحسابي هو G1.</p><p>المراجعة: 29 سبتمبر 2026. المطابقة تثبت النقل والحساب مقابل الملف؛ لا تُعد تدقيقًا مستقلاً للمسح الأصلي. صورة الحِجر توضيح لوجهة، والمؤشرات وطنية وليست أرقامًا خاصة بالعلا.</p></details>'''
section=section.replace('</article>',notes+'</article>')
html=html[:start]+section+html[end:]
html=html.replace('أيّ اتجاه أقرب إلى رؤيتكِ؟','التصميم المختار، بأرقام موثّقة.').replace('أرسلي اسم النموذج أو رقمه في المحادثة لنطوّر التقرير بناءً عليه.','يمكن فتح المصادر أسفل التصميم للاطلاع على القيم وطريقة الحساب.')
html=html.replace('<title>السياحة السعودية — أربعة اتجاهات بصرية</title>','<title>السياحة في المملكة العربية السعودية</title>')
(root/'concepts.html').write_text(html,encoding='utf-8')
record={'checked_on':'2026-09-29','source_file':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'annual':annual,'checks':checks,'official_cross_check':'https://www.spa.gov.sa/en/N2615138','limitations':'Source workbook match and rounded external headline confirmation; not a survey audit.'}
(root/'report-build/editorial-verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks_passed':len(checks),'annual':annual,'tourist_growth_percent':growth,'spending_growth_percent':spend_growth},ensure_ascii=True))
