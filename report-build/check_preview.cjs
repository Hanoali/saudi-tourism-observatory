const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..');
const file=path.join(root,'تقرير-السياحة-السعودية','معاينة-التقرير.html');
const html=fs.readFileSync(file,'utf8');
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements={};
function el(s){return elements[s]??=( {value:s==='#year'?'2025':s==='#type'?'all':'',innerHTML:'',style:{},classList:{toggle(){}},querySelectorAll(){return []}} );}
const buttons=Array.from({length:4},(_,i)=>({dataset:{page:String(i)},classList:{toggle(){}}}));
const context={document:{querySelector:el,querySelectorAll:s=>s==='nav button'?buttons:Array.from({length:4},(_,i)=>el('#p'+i))},window:{scrollTo(){},print(){}},console};
vm.createContext(context);vm.runInContext(code,context);
let checks=0;
for(let y=2021;y<=2025;y++)for(const t of ['all','محلية','وافدة']){
 el('#year').value=String(y);el('#type').value=t;vm.runInContext('render()',context);
 for(let i=0;i<4;i++){
  const h=el('#p'+i).innerHTML;
  if(!h.includes('<h2>')||/NaN|undefined|Infinity/.test(h))throw Error('Invalid output '+y+' '+t+' '+i);
  checks++;
 }
}
buttons[2].onclick();if(el('#typeLabel').style.display!=='none')throw Error('Local scope filter');
buttons[0].onclick();if(el('#typeLabel').style.display==='none')throw Error('Annual scope filter');
el('#reset').onclick();if(el('#year').value!=='2025'||el('#type').value!=='all')throw Error('Reset');
fs.writeFileSync(path.join(__dirname,'preview-checks.json'),JSON.stringify({renderedViews:checks,filterScope:'passed',reset:'passed',note:'DOM logic checks; not a browser visual rendering test'},null,2));
console.log('Passed '+checks+' year/type/page combinations, scope switching and reset.');
