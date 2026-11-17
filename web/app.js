// Estado temporário da aba; nenhuma consulta é persistida no navegador.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let sid = crypto.randomUUID().replaceAll('-', ''), tema = '', modelo = '', historico = [], avisos = [], base = [], estado;
let geracao = 0, ultima = null;
const corpo = $('.body');
const dialogo = document.createElement('dialog');
dialogo.innerHTML = '<header><h2 id="dialogTitle"></h2><button class="sm" id="fechar">Fechar</button></header><div id="dialogBody"></div>';
dialogo.setAttribute('aria-labelledby', 'dialogTitle'); document.body.append(dialogo);
$('#fechar').onclick = () => dialogo.close();
function painel(titulo, html) { $('#dialogTitle').textContent = titulo; $('#dialogBody').innerHTML = html; if (!dialogo.open) dialogo.showModal(); }
function registrarAviso(texto) { if (!avisos.includes(texto)) avisos.push(texto); $('.dot').hidden = !avisos.length; }
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
function consulta() { location.hash = 'consulta'; corpo.hidden = false; $('#temasView').hidden = true; $('h1').textContent = 'Consultar orientações'; }
function temas() { location.hash = 'temas'; corpo.hidden = true; $('#temasView').hidden = false; $('h1').textContent = 'Menu de temas'; atualizarTemas(); }
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
  $('#ans').textContent = encontrado ? r.registros[0].resumo : r.mensagem;
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
  const versao = ++geracao;
  consulta(); $('#win').classList.add('busy'); status('Buscando na base…');
  try {
    const r = await api('/api/consultar',{sid,texto,modelo,tema,reiniciar});
    if (versao !== geracao) return;
    mostrar(r);
    if (texto.trim() && !reiniciar) { historico.unshift({chave:crypto.randomUUID(),pergunta:texto,ids:r.ids,resposta:r}); historico = historico.slice(0,50); renderHistorico(); }
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
$('#form').onsubmit=e=>{e.preventDefault(); perguntar($('#q').value);};
$('#temaForm').onsubmit=e=>{e.preventDefault(); perguntar($('#temaPergunta').value);};
$('#bClear').onclick=novaConsulta; $('#nova').onclick=novaConsulta;
$('#bEdit').onclick=()=>{$('#q').focus();$('#q').select();};
$('#bBack').onclick=()=>{temaAtual('');temas();};
$('#rTemas').onclick=temas; $('#rConsulta').onclick=consulta; $('#abrirConsulta').onclick=consulta;
$('#agoraNao').onclick=()=>$('#temaPergunta').focus();
$('#ajudaTemas').onclick=()=>painel('Ajuda','<p>Escolha um tema, faça uma pergunta ou abra uma orientação pelo ID. Use “Todos os temas” para pesquisar em toda a base. Os assuntos relacionados permitem continuar a consulta.</p>');
$('#buscarConversas').oninput=e=>renderHistorico(e.target.value);
const botoes=$$('.rail button');
function $$(s){return [...document.querySelectorAll(s)];}
botoes[1].onclick=()=>painel('Fontes verificadas',base.map(r=>`<article class="card"><strong>${esc(r.pergunta)}</strong><p>Revisão: ${data(r.data)}${r.defasado?' · Atualização necessária':''}</p><a href="${esc(r.fonte)}" target="_blank" rel="noopener noreferrer">Consultar fonte oficial</a></article>`).join(''));
botoes[3].onclick=()=>{temaAtual('Apoio comunitário');perguntar('');};
botoes[4].onclick=()=>painel('Histórico desta sessão',`<button class="sm" id="apagarHistorico">Apagar histórico</button>${historico.map(h=>`<article class="card"><button class="sm" data-hist="${h.chave}">${esc(h.pergunta)}</button></article>`).join('') || '<p>Nenhuma consulta.</p>'}`);
botoes[5].onclick=indicadores;
botoes[6].onclick=()=>painel('Configurações',`<label for="modelo">Modelo de resposta</label><select id="modelo">${(estado?.modelos || []).map(m=>`<option ${m===modelo?'selected':''}>${esc(m)}</option>`).join('')}</select><label><input type="checkbox" id="movimento" ${document.body.classList.contains('semMovimento')?'checked':''}> Reduzir animações</label><p>Histórico apenas na memória desta aba. Telemetria ${estado?.log?'ativada com metadados minimizados':'desativada'}.</p>`);
$('.round').onclick=()=>painel('Notificações',avisos.length?avisos.map(a=>`<p>${esc(a)}</p>`).join(''):'<p>Nenhum aviso no momento.</p>');
document.addEventListener('change',e=>{if(e.target.id==='modelo') modelo=e.target.value;if(e.target.id==='movimento') document.body.classList.toggle('semMovimento',e.target.checked);});
document.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.id){dialogo.close();perguntar(b.dataset.id);}
 if(b.dataset.pergunta)perguntar(b.dataset.pergunta);
 if(b.dataset.tema!==undefined){temaAtual(b.dataset.tema);perguntar('');}
 if(b.dataset.abrirTema){temaAtual(b.dataset.abrirTema);perguntar('');}
 if(b.dataset.hist){const h=historico.find(h=>h.chave===b.dataset.hist);if(h){dialogo.close();consulta();mostrar(h.resposta);}}
 if(b.id==='apagarHistorico'){historico=[];renderHistorico();dialogo.close();}
});
addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('#q').focus();}});
addEventListener('hashchange',()=>location.hash==='#temas'?temas():consulta());
async function iniciar(){try{[estado,base]=await Promise.all([api('/api/estado'),api('/api/base')]);modelo=estado.modelo;$('#q').maxLength=estado.max;$('#nTemas').textContent=estado.temas.length;$('#fl').innerHTML=['',...estado.temas.map(t=>t.nome)].map(t=>`<button class="f" data-tema="${esc(t)}" aria-pressed="${!t}">${esc(t||'Todos os temas')}</button>`).join('');base.filter(r=>r.defasado).forEach(r=>registrarAviso(`${r.id}: fonte revisada há mais de ${estado.dias} dias.`));atualizarTemas();if(location.hash==='#temas')temas();}catch(e){status('Servidor indisponível');$('#ans').textContent='Não foi possível carregar a base. Verifique o servidor local e recarregue a página.';registrarAviso(e.message);}}
iniciar();
