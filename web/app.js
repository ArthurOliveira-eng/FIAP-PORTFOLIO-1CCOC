// ESTADO TEMPORÁRIO DA ABA
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let sid = crypto.randomUUID().replaceAll('-', ''), tema = '', modelo = '', historico = [], avisos = [], base = [], estado;
let geracao = 0, ultima = null;
let perguntaAtual = '', selecionada = null;
const movimentoReduzido=()=>matchMedia('(prefers-reduced-motion: reduce)').matches || document.body.classList.contains('semMovimento');
// ANIMAÇÃO DO TEXTO
function revelar(elemento,texto,animar=true){
 elemento.replaceChildren();
 texto.split(/(\s+)/).forEach((palavra,i)=>{const span=document.createElement('span');span.textContent=palavra;
 if(palavra.trim() && animar && !movimentoReduzido()){span.className='palavra';span.style.animationDelay=`${Math.min(i*22,1000)}ms`;}
 elemento.append(span);});
}
function perguntaDireita(texto){perguntaAtual=texto;$('#perguntaDireita').hidden=!texto.trim();$('#perguntaDireita').textContent=texto;}
const corpo = $('.body');
const dialogo = document.createElement('dialog');
dialogo.innerHTML = '<header><h2 id="dialogTitle"></h2><button class="sm" id="fechar">Fechar</button></header><div id="dialogBody"></div>';
dialogo.setAttribute('aria-labelledby', 'dialogTitle'); document.body.append(dialogo);
$('#fechar').onclick = () => dialogo.close();
function painel(titulo, html) { $('#dialogTitle').textContent = titulo; $('#dialogBody').innerHTML = html; if (!dialogo.open) dialogo.showModal(); }
let naoLidas = 0, toastTimer;
const toast = document.createElement('div'); toast.className='toast'; toast.hidden=true; toast.setAttribute('role','status'); document.body.append(toast);
function registrarAviso(texto) {
  avisos.unshift({texto,hora:new Date().toLocaleTimeString('pt-BR')}); avisos=avisos.slice(0,50);
  naoLidas++; $('.dot').hidden=false; $('.dot').textContent=String(Math.min(naoLidas,99));
  toast.textContent=texto; toast.hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>toast.hidden=true,5000);
}
async function api(url, pedido) {
  const r = await fetch(url, pedido ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pedido)} : undefined);
  const dados = await r.json();
  if (!r.ok) throw new Error(dados.erro || dados.mensagem || 'Não foi possível concluir a solicitação.');
  return dados;
}
function status(texto) { $('#st').textContent = texto; }
function temaAtual(t) { tema = t || ''; document.querySelectorAll('[data-tema]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.tema === tema))); }
const data = d => d ? d.split('-').reverse().join('/') : 'Não informada';
function cartao(r, relacionado = false) {
  return `<article class="card"><strong>${esc(r.pergunta)}</strong><small>${esc(r.id)} · ${esc(r.tema)}</small><div class="row"><span class="chip ${relacionado?'g':''}">${relacionado?'Relacionado':r.defasado?'Revisão necessária':'Fonte oficial'}</span><button class="sm" data-id="${esc(r.id)}">Abrir orientação</button></div></article>`;
}
function marcarSecao(id, titulo) {
 document.querySelectorAll('.rail button').forEach(b => b.removeAttribute('aria-current'));
 $(id).setAttribute('aria-current', 'page');
 $('h1').textContent = titulo;
 document.title = `${titulo} · Orientação cidadã`;
 $('.bc').textContent = 'Citizen Assist · Orientação cidadã';
}
function consulta() {
 location.hash = 'consulta'; corpo.classList.remove('modoHistorico'); corpo.hidden = false;
 $('#temasView').hidden = true; marcarSecao('#rConsulta', 'Fale por voz');
}
function temas() {
 pararVoz(); location.hash = 'temas'; corpo.classList.remove('modoHistorico'); corpo.hidden = true;
 $('#temasView').hidden = false; marcarSecao('#rTemas', 'Explore os temas'); atualizarTemas();
}
function abrirHistorico() {
 pararVoz(); location.hash = 'conversas'; corpo.hidden = false; corpo.classList.add('modoHistorico');
 $('#temasView').hidden = true; marcarSecao('#rConversas', 'Vamos conversar'); listarHistorico();
}
function listarHistorico(){
 const filtro=$('#filtroHistorico').value.toLocaleLowerCase();
 $('#listaHistorico').innerHTML=historico.filter(h=>h.pergunta.toLocaleLowerCase().includes(filtro)).map(h=>`<button class="conversaItem ${h.chave===selecionada?'selecionada':''}" data-hist="${h.chave}"><span class="avatarMini">✦</span><span><strong>${esc(h.pergunta)}</strong><small>${esc(h.hora||'Nesta sessão')}</small></span></button>`).join('')||'<p class="hint">Nenhuma conversa encontrada.</p>';
}
function lerConversa(chave){
 const h=historico.find(v=>v.chave===chave);if(!h)return;selecionada=chave;abrirHistorico();desenharConversa();
}

// CONVERSAS POR TEXTO
function criarConversa(texto, sessao = crypto.randomUUID().replaceAll('-', '')) {
 const conversa = {chave:crypto.randomUUID(), sid:sessao, pergunta:texto, tema:'', ids:[],
  hora:new Date().toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'}), mensagens:[], pendente:false};
 historico.unshift(conversa);
 historico = historico.slice(0, 50);
 return conversa;
}
function guardarResposta(conversa, mensagem, resposta) {
 mensagem.resposta = resposta; conversa.resposta = resposta;
 conversa.ids = resposta.ids; conversa.tema = resposta.tema || '';
 renderHistorico(); listarHistorico();
}
function desenharConversa(animar = false) {
 const conversa = historico.find(h => h.chave === selecionada);
 const mensagens = conversa?.mensagens || [];
 $('#historicoVazio').hidden = mensagens.length > 0;
 $('#mensagensHistorico').hidden = !mensagens.length;
 $('#sugestoesChat').hidden = mensagens.length > 0;
 $('#enviarChat').disabled = Boolean(conversa?.pendente);
 $('#chatStatus').textContent = conversa?.pendente ? 'Consultando a base…' : 'Enter envia · Shift + Enter quebra a linha';
 $('#mensagensHistorico').replaceChildren();
 mensagens.forEach((m, i) => {
  const ultimo = i === mensagens.length - 1;
  const bloco = document.createElement('article'); bloco.className = 'trocaMensagem';
  bloco.innerHTML = `<p class="balaoPergunta" ${ultimo?'id="perguntaHistorico"':''}></p>
   <div class="respostaConversa"><span class="avatarMini" aria-hidden="true">✦</span><div class="conteudoResposta">
   <pre ${ultimo?'id="respostaHistorico"':''}></pre><div class="fontesChat"></div></div></div>`;
  bloco.querySelector('.balaoPergunta').textContent = m.pergunta;
  const texto = m.resposta?.texto || m.erro || 'Consultando a base…';
  revelar(bloco.querySelector('pre'), texto, animar && ultimo);
  const fontes = bloco.querySelector('.fontesChat');
  if (m.resposta) {
   fontes.innerHTML = m.resposta.registros.filter(() => m.resposta.status === 'match').map(r =>
    `<a class="sm" href="${esc(r.fonte)}" target="_blank" rel="noopener noreferrer">Fonte oficial · ${esc(r.id)}</a>`).join('');
   const opcoes = m.resposta.status === 'match' ? m.resposta.relacionados : m.resposta.registros;
   fontes.innerHTML += opcoes.map(r => `<button class="sm" data-chat-id="${esc(r.id)}">${esc(r.id)} · ${esc(r.pergunta)}</button>`).join('');
  } else if (m.erro) {
   fontes.innerHTML = `<button class="sm" data-repetir="${i}">Tentar novamente</button>`;
  }
  $('#mensagensHistorico').append(bloco);
 });
 const rolagem = $('#chatRolagem');
 const ultimaMensagem = $('#mensagensHistorico').lastElementChild;
 if (ultimaMensagem) rolagem.scrollTop += ultimaMensagem.getBoundingClientRect().top - rolagem.getBoundingClientRect().top - 16;
}
function novaConversa() {
 selecionada = null; $('#chatPergunta').value = ''; $('#filtroHistorico').value = ''; $('#q').value = '';
 abrirHistorico(); desenharConversa(); $('#chatPergunta').focus();
}
async function enviarChat(texto, repetida = null) {
 texto = texto.trim(); if (!texto) return;
 let conversa = historico.find(h => h.chave === selecionada);
 if (conversa?.pendente) return;
 if (!conversa) conversa = criarConversa(texto);
 selecionada = conversa.chave;
 const mensagem = repetida || {pergunta:texto};
 if (!repetida) conversa.mensagens.push(mensagem);
 delete mensagem.erro; conversa.pendente = true;
 $('#chatPergunta').value = ''; abrirHistorico(); desenharConversa();
 try {
  const resposta = await api('/api/consultar', {sid:conversa.sid, texto, modelo, tema:conversa.tema});
  if (!historico.includes(conversa)) return;
  guardarResposta(conversa, mensagem, resposta);
  if (resposta.log_erro) registrarAviso(resposta.log_erro);
 } catch (e) {
  mensagem.erro = `${e.message} Confira o servidor local e tente novamente.`;
 } finally {
  conversa.pendente = false;
  if (selecionada === conversa.chave) desenharConversa(true);
 }
}
function atualizarTemas() {
  if (!estado) return;
  $('#listaTemas').innerHTML = estado.temas.map((t,i) => `<button class="themeCard" data-abrir-tema="${esc(t.nome)}"><span class="themeIcon">${['▤','◈','♧'][i] || '○'}</span><strong>${esc(t.nome)}</strong><span>${esc(base.filter(r=>r.tema===t.nome).map(r=>r.id).join(' · '))}</span><span class="chip">${t.total} registros</span><b>Abrir →</b></button>`).join('');
  $('#resumoTemas').textContent = `A base tem ${estado.total} orientações em ${estado.temas.length} temas. Escolha um para filtrar a consulta.`;
  $('#temaAplicado').textContent = tema ? `✓ Tema “${tema}” aplicado · use “voltar” para remover o filtro` : 'Todos os temas disponíveis para consulta.';
  renderHistorico();
}
function renderHistorico(filtro='') {
  $('#hist').innerHTML = historico.slice(0,2).map(h=>`<div><span>Você</span> ${esc(h.pergunta)}</div><div><b>Sistema</b> ${esc(h.ids.join(', ') || 'Sem correspondência')}</div>`).join('') || '<span>Nada ainda</span>';
  $('#conversas').innerHTML = historico.filter(h=>h.pergunta.toLocaleLowerCase().includes(filtro.toLocaleLowerCase())).map(h=>`<button class="historyItem" data-hist="${h.chave}">${esc(h.pergunta)}</button>`).join('') || '<p class="hint">Nenhuma consulta nesta sessão.</p>';
}
function mostrar(r) {
  ultima = r; temaAtual(r.tema);
  const encontrado = r.status === 'match';
  status(encontrado ? 'Consulta concluída' : ['browse','menu','related'].includes(r.status) ? 'Escolha uma orientação' : r.status === 'ambiguous' ? 'Preciso de mais detalhes' : r.status === 'quit' ? 'Sessão encerrada' : 'Confira a orientação abaixo');
  $('#ps').textContent = encontrado ? `Resposta consultada · ${r.latencia_ms} ms` : 'Consulta à base local';
  $('#ans').className = 'q' + (encontrado ? '' : ' idle');
  revelar($('#ans'), encontrado ? r.registros[0].resumo : r.mensagem);
  $('#cards').innerHTML = (encontrado ? r.registros.map(v=>`<article class="card"><strong>${esc(v.pergunta)}</strong><small>${esc(v.id)} · ${esc(v.tema)}</small><div class="row"><span class="chip">${v.defasado?'Revisão necessária':'Fonte oficial'}</span><a class="sm" href="${esc(v.fonte)}" target="_blank" rel="noopener noreferrer">Ver fonte</a></div></article>`).join('') : r.registros.map(v=>cartao(v)).join('')) + r.relacionados.map(v=>cartao(v,true)).join('');
  if (!$('#cards').innerHTML) $('#cards').innerHTML = '<div class="empty">Nenhuma orientação para mostrar.</div>';
  const reg = encontrado && r.registros[0];
  $('#box').innerHTML = reg ? `<div class="warn"><h2>Aviso de confirmação</h2><p>${esc(reg.aviso)}</p><div class="ok">Fonte consultada em ${data(reg.data)}</div></div><div class="lim"><h2>Limitações</h2><p>${esc(estado.limitacao)}</p>${reg.defasado?'<p>Registro com mais de 180 dias. Confira a fonte atual.</p>':''}</div>` : '';
  $('#box').parentElement.insertBefore($('#box'), $('#cards').nextSibling);
  $('#respostaCompleta').textContent = r.texto;
  $('#textoCompleto').hidden = false;
  if (r.log_erro) registrarAviso(r.log_erro);
}
async function perguntar(texto, reiniciar=false) {
  pararVoz(); $('#pergunta').value=texto; $('#q').value=texto;
  perguntaDireita(texto);
  const versao = ++geracao;
  consulta(); $('#win').classList.add('busy'); status('Buscando na base…');
  try {
    const r = await api('/api/consultar',{sid,texto,modelo,tema,reiniciar});
    if (versao !== geracao) return;
    mostrar(r);
    registrarAviso(r.status==='match'?'Consulta concluída. A orientação e a fonte estão disponíveis.':r.mensagem);
    if (texto.trim() && !reiniciar) {
     const conversa = historico.find(h => h.sid === sid) || criarConversa(texto, sid);
     const mensagem = {pergunta:texto}; conversa.mensagens.push(mensagem);
     if (location.hash === '#consulta') selecionada = conversa.chave;
     guardarResposta(conversa, mensagem, r);
     if (selecionada === conversa.chave) desenharConversa();
    }
  } catch(e) {
    if (versao !== geracao) return;
    status('Conexão indisponível'); $('#ans').textContent = `${e.message} Verifique se o servidor local está em execução e tente novamente.`;
    $('#cards').innerHTML = '<div class="empty">Não foi possível consultar a base.</div>'; $('#box').innerHTML=''; $('#textoCompleto').hidden=true;
    registrarAviso(e.message);
  } finally { if (versao === geracao) $('#win').classList.remove('busy'); }
}
function novaConsulta() { ++geracao; sid = crypto.randomUUID().replaceAll('-',''); temaAtual(''); ultima = null; $('#q').value=''; $('#cards').innerHTML='<div class="empty">As orientações aparecem aqui quando você consulta.</div>'; $('#box').innerHTML=''; $('#textoCompleto').hidden=true; $('#ans').textContent='Pergunte sobre documentos, serviços digitais ou apoio comunitário.'; status('Pronto para consultar'); $('#win').classList.remove('busy'); consulta(); $('#q').focus(); }
async function indicadores() {
  painel('Indicadores','<p>Carregando relatórios…</p>');
  try {
    const r = await api('/api/indicadores');
    painel('Indicadores', r.avaliacao ? `<p>Ambiente: ${esc(r.avaliacao.environment)} · Execução: ${esc(r.avaliacao.executed_at)}</p><table><thead><tr><th>Modelo</th><th>Corretas</th><th>Tempo médio</th></tr></thead><tbody>${Object.entries(r.avaliacao.metrics_by_template || {}).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v.correct}/${v.total}</td><td>${v.average_query_time_ms} ms</td></tr>`).join('')}</tbody></table><p>${esc(r.avaliacao.methodology)}</p>${r.usabilidade?`<h3>Roteiros de uso</h3><p>Conclusão: ${(r.usabilidade.task_completion_rate*100).toFixed(0)}% · Participantes humanos: ${r.usabilidade.human_participants}</p><p>${esc(r.usabilidade.limitations)}</p>`:''}` : '<p>Nenhum relatório de avaliação disponível. Execute a avaliação local para gerar os indicadores.</p>');
  } catch(e) { painel('Indicadores',`<p>${esc(e.message)}</p>`); }
}
const view=document.createElement('section'); view.id='temasView'; view.hidden=true;
view.innerHTML=`<aside class="conversationSidebar"><button class="sm" id="nova">+ Nova consulta</button><label for="buscarConversas">Buscar conversas</label><input id="buscarConversas" placeholder="Buscar nesta sessão…"><span class="lab">Hoje</span><div id="conversas"></div><p class="lab">Navegação sugerida</p><button class="sm" data-id="D02">D02 → S05 → S03 → C01</button><p class="hint">Sem dados pessoais. Protótipo independente, sem ligação com órgãos públicos.</p></aside><main class="themesMain"><header><strong>Orientação cidadã</strong><button class="sm" id="abrirConsulta">Abrir consulta guiada →</button></header><h2>Quais temas estão disponíveis?</h2><p id="resumoTemas"></p><div id="listaTemas"></div><p>Quer seguir a navegação D02 → S05 → S03?</p><div class="fl"><button class="sm" data-id="D02">Sim, abrir D02</button><button class="sm" id="agoraNao">Agora não</button></div><p id="temaAplicado" class="applied"></p><div class="suggestions"><button class="f" data-pergunta="Como recuperar minha senha do gov.br?">Como recuperar minha senha do gov.br?</button><button class="f" data-pergunta="Onde buscar atendimento do CRAS?">Onde buscar atendimento do CRAS?</button><button class="f" id="ajudaTemas">Ajuda</button></div><form id="temaForm"><label class="sr" for="temaPergunta">Sua pergunta</label><input id="temaPergunta" maxlength="500" placeholder="Pergunte ou digite um ID, como D02…"><button class="sm">Enviar →</button></form></main>`;
$('.win').append(view);
$('#stage').insertAdjacentHTML('beforeend','<details id="textoCompleto" hidden><summary>Resposta completa · modelo selecionado</summary><pre id="respostaCompleta"></pre></details>');
$('.win').insertAdjacentHTML('beforeend','<footer class="hint">Protótipo educacional independente. Não é um canal oficial. Não informe dados pessoais, senhas ou documentos.</footer>');
$('#demo').remove(); $('.dot').hidden=true;
$('#wave').innerHTML=[6,10,16,24,14,30,20,38,26,44,30,40,24,32,16,26,18,12,8].map(h=>`<i style="--h:${h}px"></i>`).join('');
$('#form').onsubmit=e=>{e.preventDefault(); corpo.classList.contains('modoHistorico') ? enviarChat($('#q').value) : perguntar($('#q').value);};
$('#temaForm').onsubmit=e=>{e.preventDefault(); perguntar($('#temaPergunta').value);};
$('#bClear').onclick=novaConsulta; $('#nova').onclick=novaConsulta;
$('#bEdit').onclick=()=>{pararVoz();status('Edite sua pergunta à direita');$('#pergunta').scrollIntoView({block:'nearest'});$('#pergunta').focus();$('#pergunta').select();};
$('#bBack').onclick=()=>{temaAtual('');temas();};
$('#rTemas').onclick=temas; $('#rConsulta').onclick=consulta; $('#abrirConsulta').onclick=consulta;
$('#agoraNao').onclick=()=>$('#temaPergunta').focus();
$('#ajudaTemas').onclick=()=>painel('Ajuda','<p>Escolha um tema, faça uma pergunta ou abra uma orientação pelo ID. Use “Todos os temas” para pesquisar em toda a base. Os assuntos relacionados permitem continuar a consulta.</p>');
$('#buscarConversas').oninput=e=>renderHistorico(e.target.value);
const botoes=$$('.rail button');
function $$(s){return [...document.querySelectorAll(s)];}
botoes[1].onclick=()=>painel('Fontes verificadas',base.map(r=>`<article class="card"><strong>${esc(r.pergunta)}</strong><p>Revisão: ${data(r.data)}${r.defasado?' · Atualização necessária':''}</p><a href="${esc(r.fonte)}" target="_blank" rel="noopener noreferrer">Consultar fonte oficial</a></article>`).join(''));
botoes[3].onclick=()=>{temaAtual('Apoio comunitário');perguntar('');};
botoes[4].onclick=abrirHistorico;
botoes[5].onclick=indicadores;
botoes[6].onclick=()=>painel('Configurações',`<label for="modelo">Modelo de resposta</label><select id="modelo">${(estado?.modelos || []).map(m=>`<option ${m===modelo?'selected':''}>${esc(m)}</option>`).join('')}</select><label><input type="checkbox" id="movimento" ${document.body.classList.contains('semMovimento')?'checked':''}> Reduzir animações</label><p>Histórico apenas na memória desta aba. Telemetria ${estado?.log?'ativada com metadados minimizados':'desativada'}.</p>`);
$('.round').onclick=()=>{painel('Notificações',avisos.length?'<p>Eventos desta aba, sem notificações externas.</p><button class="sm" id="limparAvisos">Limpar notificações</button>'+avisos.map(a=>`<article class="card"><small>${esc(a.hora)}</small><p>${esc(a.texto)}</p></article>`).join(''):'<p>Nenhum aviso no momento.</p>');naoLidas=0;$('.dot').hidden=true;};
document.addEventListener('change',e=>{if(e.target.id==='modelo') modelo=e.target.value;if(e.target.id==='movimento') document.body.classList.toggle('semMovimento',e.target.checked);});
document.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.id){dialogo.close();perguntar(b.dataset.id);}
 if(b.dataset.pergunta)perguntar(b.dataset.pergunta);
 if(b.dataset.tema!==undefined){temaAtual(b.dataset.tema);perguntar('');}
 if(b.dataset.abrirTema){temaAtual(b.dataset.abrirTema);perguntar('');}
 if(b.dataset.hist){dialogo.close();lerConversa(b.dataset.hist);}
 if(b.id==='apagarHistorico'){historico=[];renderHistorico();dialogo.close();}
 if(b.id==='limparAvisos'){avisos=[];naoLidas=0;$('.dot').hidden=true;dialogo.close();}
});
addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('#q').focus();}});
function navegar() {
 if (location.hash === '#temas') temas();
 else if (location.hash === '#consulta') consulta();
 else { abrirHistorico(); desenharConversa(); }
}
addEventListener('hashchange', navegar);
async function iniciar(){try{[estado,base]=await Promise.all([api('/api/estado'),api('/api/base')]);modelo=estado.modelo;$('#q').maxLength=estado.max;$('#nTemas').textContent=estado.temas.length;$('#fl').innerHTML=['',...estado.temas.map(t=>t.nome)].map(t=>`<button class="f" data-tema="${esc(t)}" aria-pressed="${!t}">${esc(t||'Todos os temas')}</button>`).join('');base.filter(r=>r.defasado).forEach(r=>registrarAviso(`${r.id}: fonte revisada há mais de ${estado.dias} dias.`));atualizarTemas();if(location.hash==='#temas')temas();}catch(e){status('Servidor indisponível');$('#ans').textContent='Não foi possível carregar a base. Verifique o servidor local e recarregue a página.';registrarAviso(e.message);}}
iniciar();

// ENVIO DAS CONSULTAS
$('#perguntaForm').onsubmit=e=>{e.preventDefault();perguntar($('#pergunta').value);};
$('#form svg').outerHTML='<button type="submit" class="searchTop" aria-label="Pesquisar no campo superior"><svg width="16" height="16"><use href="#search"/></svg></button>';
$('#bClear').addEventListener('click',()=>{pararVoz();$('#pergunta').value='';$('#ps').textContent='Aguardando pergunta';$('#vozStatus').textContent='Toque no microfone para falar ou escreva sua pergunta à direita.';});
$('#nova').addEventListener('click',()=>{pararVoz();$('#pergunta').value='';$('#pergunta').focus();});

// PREFERÊNCIA DE TEMA
const noite=document.createElement('button'); noite.className='round'; noite.id='noite'; noite.textContent='☾'; noite.setAttribute('aria-label','Alternar modo noturno'); $('.tools').prepend(noite);
let escuro=matchMedia('(prefers-color-scheme: dark)').matches;
try{const salvo=localStorage.getItem('citizen-tema');if(salvo)escuro=salvo==='escuro';}catch(e){}
function aplicarNoite(){document.body.classList.toggle('dark',escuro);noite.setAttribute('aria-pressed',String(escuro));noite.textContent=escuro?'☀':'☾';}
aplicarNoite(); noite.onclick=()=>{escuro=!escuro;aplicarNoite();try{localStorage.setItem('citizen-tema',escuro?'escuro':'claro');}catch(e){}};

// DITADO PELO NAVEGADOR
const Reconhecimento=window.SpeechRecognition||window.webkitSpeechRecognition;
let reconhecimento=null, consentiuVoz=false;
function pararVoz(){if(reconhecimento){const atual=reconhecimento;reconhecimento=null;atual.abort();}$('#microfone').setAttribute('aria-pressed','false');$('#wave').classList.remove('on');document.body.classList.remove('ouvindo');}
function iniciarVoz(){
 dialogo.close();
 if(!Reconhecimento){$('#vozStatus').textContent='Ditado indisponível neste navegador. Use um navegador compatível ou digite a pergunta.';return;}
 const r=new Reconhecimento(); reconhecimento=r;r.lang='pt-BR';r.continuous=false;r.interimResults=true;
 r.onstart=()=>{if(reconhecimento!==r)return;document.body.classList.add('ouvindo');status('Ouvindo sua pergunta…');revelar($('#ans'),'Pode falar. Estou ouvindo.',false);$('#microfone').setAttribute('aria-pressed','true');$('#vozStatus').textContent='Ouvindo… fale sua pergunta. Clique no microfone para cancelar.';$('#wave').classList.add('on');};
 r.onresult=e=>{if(reconhecimento!==r)return;const texto=Array.from(e.results).map(v=>v[0].transcript).join(' ').slice(0,500);$('#pergunta').value=texto;perguntaDireita(texto);revelar($('#ans'),texto);$('#vozStatus').textContent='Confira sua pergunta à direita e clique na lupa para consultar.';};
 r.onerror=e=>{if(reconhecimento!==r)return;const mensagens={'not-allowed':'Permissão negada. Libere o microfone nas permissões deste site e tente novamente.','service-not-allowed':'O serviço de ditado não está disponível neste navegador. Você pode digitar a pergunta.','audio-capture':'Nenhum microfone disponível. Confira a conexão e as configurações do sistema.','no-speech':'Não foi detectada fala. Tente novamente.','network':'O serviço de transcrição está indisponível. Confira a conexão ou digite sua pergunta.','aborted':'Ditado cancelado.'};const msg=mensagens[e.error]||'Não foi possível transcrever. Tente novamente ou digite a pergunta.';$('#vozStatus').textContent=msg;registrarAviso(msg);};
 r.onend=()=>{if(reconhecimento!==r)return;reconhecimento=null;document.body.classList.remove('ouvindo');status('Confira sua pergunta');$('#microfone').setAttribute('aria-pressed','false');$('#wave').classList.remove('on');if($('#vozStatus').textContent.startsWith('Ouvindo'))$('#vozStatus').textContent='Ditado encerrado. Confira o texto antes de pesquisar.';$('#pergunta').focus();};
 try{r.start();}catch(e){pararVoz();$('#vozStatus').textContent='Não foi possível iniciar o microfone. Confira a permissão do navegador.';}
}
$('#microfone').onclick=()=>{
 if(reconhecimento){pararVoz();status('Ditado interrompido');$('#vozStatus').textContent='Você pode editar sua pergunta à direita e enviar pela lupa.';return;}
 if(!Reconhecimento){$('#vozStatus').textContent='Seu navegador não oferece ditado compatível. Digite sua pergunta ou tente outro navegador.';registrarAviso('Reconhecimento de voz indisponível neste navegador.');return;}
 if(!consentiuVoz){painel('Perguntar pelo microfone','<p>O ditado usa o serviço de reconhecimento de voz do navegador, que pode enviar áudio para processamento online. Não fale dados pessoais ou senhas.</p><p>O texto aparecerá no campo para revisão antes de pesquisar. O aplicativo não armazena áudio.</p><button class="sm" id="ativarVoz">Continuar e ativar microfone</button>');return;}
 iniciarVoz();
};
document.addEventListener('click',e=>{if(e.target.closest('#ativarVoz')){consentiuVoz=true;iniciarVoz();}});
dialogo.addEventListener('close',()=>$(corpo.classList.contains('modoHistorico')?'#chatPergunta':'#pergunta').focus());
addEventListener('pagehide',pararVoz);

// TELA DE CONVERSAS
const historicoLayout=document.createElement('section');historicoLayout.className='historicoLayout';
historicoLayout.innerHTML=`
 <aside class="historicoSidebar">
  <header><h2>Conversas</h2><button class="sm" id="novaHistorico" aria-label="Nova conversa">+ Nova</button></header>
  <label class="sr" for="filtroHistorico">Buscar no histórico</label>
  <input id="filtroHistorico" placeholder="Buscar conversas…">
  <p class="lab">Nesta sessão</p><div id="listaHistorico"></div>
  <button class="sm" id="limparHistoricoTela">Apagar histórico</button>
  <p class="hint">As mensagens ficam apenas nesta aba.</p>
 </aside>
 <main class="historicoMain" aria-label="Conversa por texto">
  <header><span class="avatarMini" aria-hidden="true">✦</span>
   <div><strong>Orientação cidadã</strong><small><span class="onlineDot"></span>Pronto para ajudar · com fontes oficiais</small></div>
   <button class="sm" id="falarHistorico"><svg class="voiceIcon" aria-hidden="true" width="14" height="16" viewBox="0 0 16 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 7v4M5 4v10M8 1v16M11 4v10M14 7v4"/></svg>Fale por voz</button>
  </header>
  <div id="chatRolagem">
   <div id="historicoVazio"><span class="avatarMini" aria-hidden="true">✦</span><h2>Como posso ajudar?</h2><p>Pergunte sobre documentos, serviços digitais ou apoio comunitário.</p></div>
   <div id="mensagensHistorico" role="log" aria-label="Mensagens da conversa" aria-live="polite" hidden></div>
  </div>
  <div class="chatRodape">
   <div id="sugestoesChat"><button class="sm" data-chat-texto="Como recuperar minha senha do gov.br?">Recuperar conta gov.br</button><button class="sm" data-chat-texto="Onde buscar atendimento do CRAS?">Encontrar o CRAS</button><button class="sm" data-chat-texto="O que é a CIN?">Conhecer a CIN</button></div>
   <form id="chatForm"><label class="sr" for="chatPergunta">Mensagem</label>
    <textarea id="chatPergunta" rows="1" maxlength="500" placeholder="Escreva sua pergunta…" aria-describedby="chatStatus"></textarea>
    <button id="enviarChat" class="send" aria-label="Enviar mensagem"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m21 3-7 18-4-7-7-4 18-7ZM10 14 21 3"/></svg></button>
   </form>
   <p id="chatStatus" class="hint" role="status">Enter envia · Shift + Enter quebra a linha</p>
  </div>
 </main>`;
corpo.append(historicoLayout);
$('.panel .ph').insertAdjacentHTML('afterend','<p id="perguntaDireita" class="balaoPergunta" hidden></p>');
$('#filtroHistorico').oninput=listarHistorico;
$('#novaHistorico').onclick = novaConversa;
$('#falarHistorico').onclick = () => {
 const conversa = historico.find(h => h.chave === selecionada);
 if (conversa?.pendente) { $('#chatStatus').textContent = 'Aguarde a resposta antes de mudar para voz.'; return; }
 novaConsulta();
 if (conversa) { sid = conversa.sid; temaAtual(conversa.tema); }
 $('#pergunta').value = ''; perguntaDireita(''); consulta(); $('#microfone').focus();
};
$('#limparHistoricoTela').onclick = () => {
 ++geracao; $('#win').classList.remove('busy'); historico = []; renderHistorico(); novaConversa();
};
$('#chatForm').onsubmit = e => { e.preventDefault(); enviarChat($('#chatPergunta').value); };
$('#chatPergunta').onkeydown = e => {
 if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); $('#chatForm').requestSubmit(); }
};
document.addEventListener('click', e => {
 const botao = e.target.closest('button'); if (!botao) return;
 if (botao.dataset.chatTexto) enviarChat(botao.dataset.chatTexto);
 if (botao.dataset.chatId) enviarChat(botao.dataset.chatId);
 if (botao.dataset.repetir !== undefined) {
  const conversa = historico.find(h => h.chave === selecionada);
  const mensagem = conversa?.mensagens[Number(botao.dataset.repetir)];
  if (mensagem && !conversa.pendente) enviarChat(mensagem.pergunta, mensagem);
 }
});
$('#bClear').addEventListener('click',()=>perguntaDireita(''));
$('#nova').addEventListener('click',()=>perguntaDireita(''));
// IDENTIDADE VISUAL
$('.orb b').textContent='✦';$('.mini').textContent='✦';
navegar();
