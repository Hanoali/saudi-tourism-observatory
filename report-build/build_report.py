from pathlib import Path
import json, zipfile, uuid, copy, hashlib, math

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'تقرير-السياحة-السعودية'
OUT.mkdir(exist_ok=True)
SOURCE=next(p for p in ROOT.glob('*.pbix') if p.name.endswith('نسخة - نسخة.pbix'))
model=json.loads((ROOT/'relationship-repair/model-after-annual.json').read_text(encoding='utf-8-sig'))['model']
tables={t['name']:t for t in model['tables']}
def uid(): return uuid.uuid4().hex[:20]
def lit(v):
    return {'expr':{'Literal':{'Value':str(v).lower() if isinstance(v,bool) else str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"}}}
def col(t,c,label=None):
    assert any(x['name']==c for x in tables[t]['columns']),(t,c)
    return {'field':{'Column':{'Expression':{'SourceRef':{'Entity':t}},'Property':c}},'queryRef':f'{t}.{c}','nativeQueryRef':label or c}
def measure(t,c,label=None):
    assert any(x['name']==c for x in tables[t].get('measures',[])),(t,c)
    return {'field':{'Measure':{'Expression':{'SourceRef':{'Entity':t}},'Property':c}},'queryRef':f'{t}.{c}','nativeQueryRef':label or c}
def agg(t,c,label):
    p=col(t,c,label);p['field']={'Aggregation':{'Expression':p['field'],'Function':0}};p['queryRef']=f'Sum({t}.{c})';return p
def color(c):return {'solid':{'color':lit(c)}}
def obj(**kw):return [{'properties':kw}]
NAVY='#102F35';TEAL='#087F8C';GOLD='#BA8B48';BG='#F3F6F5';INK='#19383E';GRAY='#60777A'
pages=[]
def page(name,subtitle,scope,number):
    p={'name':uid(),'displayName':name,'displayOption':'FitToPage','height':1080,'width':1600,'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json','objects':{'background':obj(color=color(BG),transparency=lit(0))}}
    p['_visuals']=[];pages.append(p)
    text(p,name,(32,18,1536,57),30,'#FFFFFF',NAVY)
    text(p,subtitle,(32,83,1536,36),13,GRAY)
    text(p,scope,(32,1023,1536,32),10,GRAY)
    text(p,f'{number:02d} / 04   |   وزارة السياحة · بيانات المصدر 2021–2025 · زوار المبيت',(32,1056,1536,20),9,GRAY)
    return p
def visual(p,kind,title,rect,roles=None,units=0,precision=1,filters=None,sort=None):
    x,y,w,h=rect;i=len(p['_visuals']);v={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json','name':uid(),'position':{'x':x,'y':y,'width':w,'height':h,'z':i*1000,'tabOrder':i*1000},'visual':{'visualType':kind,'drillFilterOtherVisuals':True}}
    vc=v['visual'];vc['visualContainerObjects']={'title':obj(show=lit(bool(title)),text=lit(title),fontColor=color(INK),fontSize=lit(13),fontFamily=lit('Segoe UI'),alignment=lit('right')),'background':obj(show=lit(True),color=color('#FFFFFF'),transparency=lit(0)),'border':obj(show=lit(True),color=color('#DFE8E5'),radius=lit(8)),'visualHeader':obj(show=lit(False))}
    vc['objects']={'legend':obj(show=lit(True),position=lit('Bottom'),fontSize=lit(10),labelColor=color(GRAY)),'categoryAxis':obj(show=lit(True),fontSize=lit(10),labelColor=color(GRAY),showAxisTitle=lit(False)),'valueAxis':obj(show=lit(True),fontSize=lit(10),labelColor=color(GRAY),showAxisTitle=lit(False),labelDisplayUnits=lit(units),labelPrecision=lit(precision)),'labels':obj(show=lit(False),fontSize=lit(10),labelDisplayUnits=lit(units),labelPrecision=lit(precision))}
    if roles:
        vc['query']={'queryState':{r:{'projections':copy.deepcopy(ps)} for r,ps in roles.items()}}
        if sort:vc['query']['sortDefinition']={'sort':[{'field':sort[0]['field'],'direction':sort[1]}]}
    if filters:v['filterConfig']={'filters':filters}
    p['_visuals'].append(v);return v
def text(p,content,rect,size=14,fg=INK,bg=None):
    v=visual(p,'textbox','',rect);vc=v['visual']
    vc['objects']={'general':obj(paragraphs=[{'textRuns':[{'value':content,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':fg}}],'horizontalTextAlignment':'right'}])}
    vc['visualContainerObjects']['background']=obj(show=lit(bg is not None),color=color(bg or BG),transparency=lit(0))
    vc['visualContainerObjects']['border']=obj(show=lit(False));return v
def card(p,title,m,rect,units=0,precision=1):
    v=visual(p,'card',title,rect,{'Values':[m]},units,precision)
    v['visual']['objects']={'labels':obj(color=color(TEAL),fontSize=lit(32),labelDisplayUnits=lit(units),labelPrecision=lit(precision)),'categoryLabels':obj(show=lit(False)),'wordWrap':obj(show=lit(True))}
    return v
def filter_(table,column,values,negate=False):
    field=col(table,column)['field'];inside={'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':column}}],'Values':[[{'Literal':{'Value':str(x)+'L' if isinstance(x,int) else "'"+x.replace("'","''")+"'"}}] for x in values]}}
    condition={'Not':{'Expression':inside}} if negate else inside
    return {'name':uid(),'field':field,'type':'Categorical','filter':{'Version':2,'From':[{'Name':'s','Entity':table,'Type':0}],'Where':[{'Condition':condition}]},'howCreated':'User'}
def slicer(p,title,t,c,rect,selected=None):
    v=visual(p,'slicer',title,rect,{'Values':[col(t,c,title)]})
    v['visual']['objects']={'data':obj(mode=lit('Dropdown')),'selection':obj(singleSelect=lit(False),selectAllCheckboxEnabled=lit(True)),'header':obj(show=lit(False)),'items':obj(fontSize=lit(11),fontColor=color(INK))}
    if selected is not None:v['visual']['objects']['general']=obj(filter={'filter':filter_(t,c,selected)['filter']})
    return v
def table(p,title,projs,rect,filters=None,sort=None):
    v=visual(p,'tableEx',title,rect,{'Values':projs},filters=filters,sort=sort)
    v['visual']['objects']={'columnHeaders':obj(fontColor=color('#FFFFFF'),backColor=color(TEAL),fontSize=lit(10),wordWrap=lit(True)),'values':obj(fontColorPrimary=color(INK),backColorPrimary=color('#FFFFFF'),backColorSecondary=color('#F0F5F3'),fontSize=lit(10)),'grid':obj(gridVertical=lit(False),gridHorizontal=lit(True),rowPadding=lit(5)),'total':obj(totals=lit(False))}
    return v
def cards(p,specs):
    for i,(title,m,u,prec) in enumerate(specs):card(p,title,m,(32+i*389,209,369,112),u,prec)
def annual(t,m,label=None):return measure(t,m,label)
N='Annual_National_Tourism';R='Annual_Regional_Tourism';K='KPI_Measures';Y=col('DimYear','Year','السنة');T=col('DimTourismType','TourismType','نوع السياحة');MO=col('DimMonth','Month Number','رقم الشهر')
nt=measure(N,'National Tourists','عدد السياح');ns=measure(N,'National Spending SAR','الإنفاق بالريال');nn=measure(N,'National Overnight Stays','ليالي الإقامة');na=measure(N,'National Average Stay','متوسط الليالي');np=measure(N,'National Spend per Trip','ريال لكل رحلة');nd=measure(N,'National Spend per Night','ريال لكل ليلة')
rt=measure(R,'Regional Tourists','عدد السياح');rs=measure(R,'Regional Spending SAR','الإنفاق بالريال');ra=measure(R,'Regional Average Stay','متوسط الليالي');rp=measure(R,'Regional Spend per Trip','ريال لكل رحلة');reg=col(R,'Region','المنطقة')
dt=measure(K,'Total Tourists','السياح المحليون');ds=measure(K,'Total Spending','الإنفاق المحلي');hotel=measure(K,'Hotel Tourists','الفنادق');private=measure(K,'Private Accommodation','السكن الخاص');air=measure(K,'Air Tourists','جواً');gov=measure(K,'Governorate Tourists','عدد السياح')

p=page('01  المشهد السياحي في المملكة','المحلية والوافدة | الحجم والقيمة ومدة الإقامة | مؤشرات سنوية','النطاق: السياحة الداخلية = المحلية + الوافدة. الاتجاهات تعرض 2021–2025؛ اختيار السنة يغيّر البطاقات وجدول المقارنة.',1)
sy=slicer(p,'السنة','DimYear','Year',(1180,128,388,62),[2025]);st=slicer(p,'نوع السياحة','DimTourismType','TourismType',(780,128,380,62))
text(p,'غيّر السنة والنوع لاستكشاف المؤشرات',(32,139,720,39),14)
cards(p,[('عدد السياح | مليون',nt,1e6,2),('الإنفاق | مليار ريال',ns,1e9,2),('متوسط الإقامة | ليلة',na,1,2),('متوسط الإنفاق للرحلة | ريال',np,1,0)])
v1=visual(p,'clusteredColumnChart','تطور أعداد السياح | مليون',(32,343,758,285),{'Category':[Y],'Series':[T],'Y':[nt]},1e6,1,sort=(Y,'Ascending'))
v2=visual(p,'lineChart','تطور الإنفاق | مليار ريال',(810,343,758,285),{'Category':[Y],'Series':[T],'Y':[ns]},1e9,1,sort=(Y,'Ascending'))
p['visualInteractions']=[{'source':sy['name'],'target':v['name'],'type':'NoFilter'} for v in [v1,v2]]
table(p,'مقارنة النوعين للفترة المختارة | القيم بالوحدات الكاملة',[T,nt,ns,na,np,nd],(32,650,1536,212))
text(p,'قراءة مرجعية لعام 2025: الوافدة 23.9% من السياح، لكنها 58.2% من الإنفاق. متوسط إنفاق الرحلة الوافدة يعادل نحو 4.43 أمثال المحلية.',(32,883,1536,65),17,'#FFFFFF',NAVY)
text(p,'تفسير: اختلاف مدة الإقامة يفسّر جزءًا من فجوة الإنفاق للرحلة؛ لا يعني الفرق وحده اختلاف الأسعار أو الربحية.',(32,959,1536,43),12,GRAY)

p=page('02  المناطق ومصادر القيمة','13 منطقة | حجم الطلب والإنفاق ومتوسط قيمة الرحلة | مقارنة سنوية','النطاق: المحلية والوافدة حسب المنطقة. تُحسب المتوسطات من المجاميع؛ بيانات المناطق هي الأساس للمقارنة الجغرافية.',2)
slicer(p,'السنة','DimYear','Year',(1180,128,388,62),[2025]);slicer(p,'نوع السياحة','DimTourismType','TourismType',(780,128,380,62));slicer(p,'المنطقة','Annual_Regional_Tourism','Region',(32,128,728,62))
cards(p,[('عدد السياح | مليون',rt,1e6,2),('الإنفاق | مليار ريال',rs,1e9,2),('متوسط الإقامة | ليلة',ra,1,2),('متوسط إنفاق الرحلة | ريال',rp,1,0)])
visual(p,'clusteredBarChart','ترتيب المناطق حسب السياح | مليون',(32,343,758,424),{'Category':[reg],'Y':[rt]},1e6,1,sort=(rt,'Descending'))
visual(p,'clusteredBarChart','ترتيب المناطق حسب الإنفاق | مليار ريال',(810,343,758,424),{'Category':[reg],'Y':[rs]},1e9,1,sort=(rs,'Descending'))
table(p,'تفاصيل المناطق | مرّر لعرض المناطق كافة',[reg,rt,rs,rp,ra],(32,787,1010,219),sort=(rs,'Descending'))
text(p,'قراءة مرجعية · 2025\nمكة والرياض والشرقية تستحوذ على 73.2% من السياح.\nمكة وحدها: 40.0% من السياح و61.9% من الإنفاق.\nالحصة المرتفعة لا تساوي ربحية مرتفعة؛ التكاليف غير متاحة.',(1062,787,506,219),15,'#FFFFFF',NAVY)

p=page('03  أنماط السياحة المحلية','متى يسافر المقيمون؟ لماذا؟ وكيف يتنقلون وأين يقيمون؟','النطاق: محلية فقط. الأرقام الشهرية بالألف في المصدر؛ عُرضت بالمليون. نوع الإقامة لا يمثل نسبة إشغال الغرف.',3)
slicer(p,'السنة','DimYear','Year',(1180,128,388,62),[2025]);text(p,'بيانات شهرية | لا تشمل تفاصيل السياحة الوافدة',(32,139,1120,40),16)
cards(p,[('السياح المحليون | مليون',dt,1e3,2),('سياح الفنادق | مليون',hotel,1e3,2),('السكن الخاص | مليون',private,1e3,2),('السياح جوًا | مليون',air,1e3,2)])
visual(p,'lineChart','الموسمية | السياح المحليون بالمليون',(32,343,758,284),{'Category':[MO],'Y':[dt]},1e3,1,sort=(MO,'Ascending'))
purposes=[agg('Monthly_Trip_Purpose',c,l) for c,l in [('Religious','ديني'),('Business','أعمال'),('Leisure','ترفيه'),('Visiting Friends& Relatives','زيارة الأقارب والأصدقاء'),('Other','أخرى')]]
visual(p,'stackedColumnChart','أغراض الرحلة عبر الأشهر | مليون',(810,343,758,284),{'Category':[MO],'Y':purposes},1e3,1,sort=(MO,'Ascending'))
visual(p,'donutChart','وسيلة النقل الرئيسية',(32,647,492,277),{'Y':[air,measure(K,'Land Tourists','براً'),measure(K,'Sea Tourists','بحراً')]},1e3,1)
visual(p,'donutChart','نوع الإقامة',(544,647,492,277),{'Y':[hotel,private,measure(K,'Apartments Tourists','الشقق'),measure(K,'Other Accommodation','أخرى')]},1e3,1)
text(p,'قراءة مرجعية · 2025\n40.4% لزيارة الأقارب والأصدقاء.\n32.4% للترفيه.\n93.8% استخدموا النقل البري.\n42.7% أقاموا في سكن خاص.\n\nهذه توزيعات منفصلة؛ لا تثبت تفضيلات الفئة نفسها عبر الجداول.',(1056,647,512,277),16,'#FFFFFF',NAVY)
text(p,'المقارنة الشهرية تظهر الموسمية، لكنها لا تثبت أسبابها. راجع الإجازات والمواسم والتقويم الهجري قبل نسبة القمم إلى حدث محدد.',(32,946,1536,61),13,GRAY)

p=page('04  الإنفاق المحلي والوجهات التفصيلية','أين يذهب الإنفاق؟ وما قيمة الرحلات في المحافظات؟','النطاق: محلية فقط. لا نجمع عدد السياح والريالات في Amount. بيانات المحافظات ذات هامش خطأ أعلى من بيانات المناطق.',4)
slicer(p,'السنة','DimYear','Year',(1180,128,388,62),[2025]);text(p,'المؤشرات تستجيب للسنة | تفاصيل المحافظات في الجدول السفلي',(32,139,1120,40),15)
cards(p,[('الإنفاق المحلي | مليار ريال',ds,1e3,2),('الطعام والشراب | مليار ريال',measure(K,'Food Spending','الطعام'),1e3,2),('الإيواء | مليار ريال',measure(K,'Accommodation Spending','الإيواء'),1e3,2),('المواصلات | مليار ريال',measure(K,'Local Transport Spending','المواصلات'),1e3,2)])
visual(p,'lineChart','الإنفاق المحلي عبر الأشهر | مليار ريال',(32,343,758,268),{'Category':[MO],'Y':[ds]},1e3,1,sort=(MO,'Ascending'))
sp=[measure(K,n,l) for n,l in [('Food Spending','الطعام والشراب'),('Local Transport Spending','المواصلات'),('Accommodation Spending','الإيواء'),('Shopping Spending','التسوق'),('Entertainment Spending','الترفيه'),('Other Spending','أخرى')]]
visual(p,'donutChart','توزيع الإنفاق حسب البند',(810,343,758,268),{'Y':sp},1e3,1)
gsp=agg('Monthly_Destination_Governorate','Amount','إنفاق السياح بالريال')
table(p,'المحافظات | عدد السياح والإنفاق بالريال — مرّر لعرض التفاصيل',[col('D5_Geography_EN','Region_AR','المنطقة'),col('D5_Geography_EN','Governorate_AR','المحافظة'),gov,gsp],(32,632,1010,374),filters=[filter_('Monthly_Destination_Governorate','Indicator',['Tourists Spending (SAR)']),filter_('Monthly_Destination_Governorate','Governorate',['الإجمالي'],True)],sort=(gsp,'Descending'))
text(p,'قراءة مرجعية · 2025\n127.08 مليار ريال إنفاق محلي.\nالطعام والشراب: 32.3%.\nالمواصلات: 26.7%.\nالإيواء: 23.1%.\n\nالبنود الثلاثة تمثل نحو 82.0% من الإنفاق.\n\nدقة المصدر: تفاصيل D8 في 2021 و2022 مقربة إلى مليون ريال؛ تظهر فروق طفيفة عند المطابقة مع إجمالي D1 الأدق.',(1062,632,506,374),15,'#FFFFFF',NAVY)

# Editorial evidence panels are deliberately dated, and do not pretend to react
# to the year slicer. Numeric charts above remain driven by the existing model.
events=json.loads((OUT/'سجل-الأحداث-والمصادر.json').read_text(encoding='utf-8'))
evidence=json.loads((ROOT/'report-build/evidence-panels.json').read_text(encoding='utf-8'))
event_groups=[[0,1,2,3,5],[7,9,12],[4,6,8,10,11],[13]]
for index,p in enumerate(pages):
    p['height']=1860;p['displayOption']='FitToWidth'
    text(p,'لماذا تغيّرت الأرقام؟ | قراءة تاريخية ثابتة 2021–2025',(32,1098,1536,48),23,'#FFFFFF',NAVY)
    text(p,'الأرقام في الرسوم تتفاعل مع الفلاتر؛ التفسيرات التالية مرجعية مؤرخة ولا تتغير باختيار السنة.',(32,1155,1536,34),12,GRAY)
    text(p,evidence[index]['title'],(32,1200,550,55),19,TEAL)
    text(p,evidence[index]['body'],(32,1268,550,386),16,INK,'#FFFFFF')
    for j,eid in enumerate(event_groups[index]):
        e=events[eid];y=1200+j*111
        text(p,f"{e['period']} | {e['event']}",(610,y,958,31),14,TEAL)
        text(p,e['interpretation'],(610,y+32,958,44),12,INK)
        v=text(p,'المصدر الرسمي: '+e['source'],(610,y+77,958,27),10,GRAY)
        v['visual']['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['url']=e['source']
    text(p,evidence[index]['limit'],(32,1770,1536,57),13,INK,'#E5EEEA')
    text(p,'مصدر الأرقام: ملف وزارة السياحة المرفق • بحث الأحداث: 28 سبتمبر 2026 • المطابقة والملاحظات في ملف سجل التحقق المرفق',(32,1836,1536,20),9,GRAY)

def encode(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode('utf-8')
manifest=[];new={}
for p in pages:
    vs=p.pop('_visuals');folder='Report/definition/pages/'+p['name']
    new[folder+'/page.json']=encode(p)
    for v in vs:new[folder+'/visuals/'+v['name']+'/visual.json']=encode(v)
    manifest.append({'page':p,'visuals':vs})
new['Report/definition/pages/pages.json']=encode({'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json','pageOrder':[p['name'] for p in pages],'activePageName':pages[0]['name']})
with zipfile.ZipFile(SOURCE) as z:
    report=json.loads(z.read('Report/definition/report.json'))
    # Use the existing registered base theme, preserving its schema and defaults.
    theme_path=next(n for n in z.namelist() if '/BaseThemes/' in n)
    theme=json.loads(z.read(theme_path));theme['dataColors']=[TEAL,GOLD,'#568C6A','#7B829C','#D98B66','#7CAAAF','#A89269','#5E7074']
    new[theme_path]=encode(theme)
    target=OUT/'السياحة-السعودية-تقرير-متكامل-بالأحداث.pbix'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as dest:
        for info in z.infolist():
            if info.filename.startswith('Report/definition/pages/') or info.filename in new or info.filename=='SecurityBindings':continue
            data=z.read(info.filename)
            if info.filename=='[Content_Types].xml':
                import re
                # Preserve Power BI's default namespace and unprefixed Types tag.
                # Its package reader rejects ElementTree's ns0:Types serialization.
                data=re.sub(rb'<Override\s+PartName="/SecurityBindings"[^>]*/>',b'',data)
            dest.writestr(copy.copy(info),data)
        for name,data in new.items():dest.writestr(name,data)
    original_hash=hashlib.sha256(z.read('DataModel')).hexdigest()
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert hashlib.sha256(z.read('DataModel')).hexdigest()==original_hash
    assert len([n for n in z.namelist() if n.endswith('/page.json')])==4
for row in manifest:
    for v in row['visuals']:
        a=v['position'];assert 0<=a['x'] and 0<=a['y'] and a['x']+a['width']<=1600 and a['y']+a['height']<=row['page']['height']
    for i,a in enumerate(row['visuals']):
        a=a['position']
        for b in row['visuals'][i+1:]:
            b=b['position'];assert min(a['x']+a['width'],b['x']+b['width'])<=max(a['x'],b['x']) or min(a['y']+a['height'],b['y']+b['height'])<=max(a['y'],b['y']),'Overlapping visuals'
(ROOT/'report-build/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Built:',target)
print('Pages:',len(pages),'Visuals:',sum(len(r['visuals']) for r in manifest),'DataModel unchanged:',original_hash)
