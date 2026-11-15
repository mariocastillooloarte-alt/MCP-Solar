const loginScreen=document.getElementById('login-screen');
const loginForm=document.getElementById('login-form');
const loginError=document.getElementById('login-error');
function unlockApp(){loginScreen.classList.add('hidden');document.body.classList.remove('locked')}
async function checkSession(){try{const response=await fetch('/api/auth/me',{credentials:'include'});if(response.ok){unlockApp()}}catch(error){console.warn('API de autenticación no disponible')}}
checkSession();
loginForm.addEventListener('submit',async event=>{event.preventDefault();loginError.textContent='';const email=document.getElementById('login-email').value.trim();const password=document.getElementById('login-password').value;try{const response=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({email,password})});const data=await response.json();if(!response.ok)throw new Error(data.detail||'No se pudo iniciar sesión');unlockApp()}catch(error){loginError.textContent=error.message}});
const products=[
 {sku:'PAN-450-MONO',name:'Panel monocristalino 450W',category:'panel',power:'450 W',price:189,stock:120},
 {sku:'PAN-550-MONO',name:'Panel monocristalino 550W',category:'panel',power:'550 W',price:239,stock:80},
 {sku:'INV-5K-HIB',name:'Inversor híbrido 5kW',category:'inversor',power:'5 kW',price:1290,stock:18},
 {sku:'BAT-10K',name:'Batería de litio 10kWh',category:'bateria',power:'10 kWh',price:4850,stock:7},
 {sku:'EST-01',name:'Estructura residencial',category:'estructura',power:'—',price:620,stock:35},
 {sku:'MON-01',name:'Monitorización remota',category:'monitorizacion',power:'—',price:180,stock:50}
];
const euro=new Intl.NumberFormat('es-ES',{style:'currency',currency:'EUR',maximumFractionDigits:0});
const views=document.querySelectorAll('.view');
function showView(id){views.forEach(v=>v.classList.toggle('active-view',v.id===id));document.querySelectorAll('.nav-item').forEach(n=>n.classList.toggle('active',n.dataset.view===id));const titles={dashboard:'Resumen',quote:'Nuevo presupuesto',products:'Productos y stock',leads:'Leads',installations:'Instalaciones y citas'};document.getElementById('page-title').textContent=titles[id]||'Resumen';window.scrollTo(0,0)}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
document.querySelectorAll('[data-go]').forEach(button=>button.addEventListener('click',()=>showView(button.dataset.go)));
const quoteModal=document.getElementById('quote-modal');
const quoteModalForm=document.getElementById('quote-modal-form');
const modalResult=document.getElementById('modal-quote-result');
const createQuoteButton=document.getElementById('create-quote-button');
const closeQuoteModal=document.getElementById('close-quote-modal');
function openQuoteModal(){quoteModal.hidden=false;document.body.style.overflow='hidden';document.getElementById('modal-consumption').focus()}
function closeQuoteModalWindow(){quoteModal.hidden=true;document.body.style.overflow=''}
createQuoteButton.addEventListener('click',openQuoteModal);
closeQuoteModal.addEventListener('click',closeQuoteModalWindow);
quoteModal.addEventListener('click',event=>{if(event.target===quoteModal)closeQuoteModalWindow()});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!quoteModal.hidden)closeQuoteModalWindow()});
function calculateValues(consumption,power,tariff,battery){const panels=Math.max(1,Math.round(power*1000/450));const equipment=panels*189+1290+620+(battery?4850:0);const install=Math.max(900,power*220);const total=(equipment+install)*1.21;const production=power*4.5*365*.8;const annual=Math.min(production,consumption*12)*tariff;return {panels,total,production,annual,roi:annual?total/annual:0}}
quoteModalForm.addEventListener('submit',event=>{event.preventDefault();const values=calculateValues(Number(document.getElementById('modal-consumption').value),Number(document.getElementById('modal-power').value),Number(document.getElementById('modal-tariff').value),document.getElementById('modal-battery').checked);document.getElementById('modal-total').textContent=euro.format(values.total);document.getElementById('modal-saving').textContent=euro.format(values.annual);document.getElementById('modal-roi').textContent=`${values.roi.toFixed(1).replace('.',',')} años`;document.getElementById('modal-panels').textContent=`${values.panels} × 450 W`;document.getElementById('modal-production').textContent=`${Math.round(values.production).toLocaleString('es-ES')} kWh`;modalResult.hidden=false;quoteModalForm.classList.add('is-hidden')});
document.getElementById('new-quote-button').addEventListener('click',()=>{modalResult.hidden=true;quoteModalForm.classList.remove('is-hidden');document.getElementById('modal-consumption').focus()});
function calculate(){const consumption=Number(document.getElementById('consumption').value)||650;const power=Number(document.getElementById('power').value)||5;const tariff=Number(document.getElementById('tariff').value)||.2;const battery=document.getElementById('battery').checked;const panels=Math.max(1,Math.round(power*1000/450));const equipment=panels*189+1290+620+(battery?4850:0);const install=Math.max(900,power*220);const total=(equipment+install)*1.21;const production=power*4.5*365*.8;const annual=Math.min(production,consumption*12)*tariff;document.getElementById('quote-title').textContent=`Sistema residencial ${power} kW`;document.getElementById('quote-total').textContent=euro.format(total);document.getElementById('quote-saving').textContent=euro.format(annual);document.getElementById('quote-roi').textContent=`${(total/annual).toFixed(1).replace('.',',')} años`;document.getElementById('quote-panels').textContent=`${panels} × 450 W`;document.getElementById('quote-production').textContent=`${Math.round(production).toLocaleString('es-ES')} kWh`}
document.getElementById('quote-form').addEventListener('submit',e=>{e.preventDefault();calculate()});
function renderProducts(){const q=(document.getElementById('product-search').value||'').toLowerCase();const cat=document.getElementById('product-filter').value;const rows=products.filter(p=>(!q||`${p.name} ${p.sku}`.toLowerCase().includes(q))&&(!cat||p.category===cat)).map(p=>`<tr><td><strong>${p.name}</strong><small>${p.sku}</small></td><td>${p.category}</td><td>${p.power}</td><td><strong>${euro.format(p.price)}</strong></td><td>${p.stock}</td><td><span class="pill ${p.stock<10?'orange-pill':'green-pill'}">${p.stock<10?'Stock bajo':'Disponible'}</span></td></tr>`).join('');document.getElementById('product-rows').innerHTML=rows||'<tr><td colspan="6">No hay productos que coincidan.</td></tr>'}
document.getElementById('product-search').addEventListener('input',renderProducts);document.getElementById('product-filter').addEventListener('change',renderProducts);renderProducts();calculate();