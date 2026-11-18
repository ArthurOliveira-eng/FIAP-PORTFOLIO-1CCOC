import { $, esc, textoVisivel, revelar } from "./js/dom.js";
import { api } from "./js/api.js";
import { dialogo, painel, registrarAviso } from "./js/notifications.js";
import { criarChat } from "./js/chat.js";
import { criarVoz } from "./js/voice.js";
import { iniciarPreferencias } from "./js/preferences.js";

let sid = crypto.randomUUID().replaceAll("-", ""),
  tema = "",
  modelo = "",
  base = [],
  estado;
let geracao = 0;
const voz = criarVoz({ status, perguntaDireita });
const pararVoz = voz.parar;
const chat = criarChat({
  abrirTela: abrirHistorico,
  modeloAtual: () => modelo,
  registrarAviso,
  aoLimpar: () => {
    ++geracao;
    $("#win").classList.remove("busy");
  },
});
iniciarPreferencias();

// ESTADO TEMPORÁRIO DA ABA
function perguntaDireita(texto) {
  $("#perguntaDireita").hidden = !texto.trim();
  $("#perguntaDireita").textContent = texto;
}
const corpo = $(".body");
function status(texto) {
  $("#st").textContent = texto;
}
function temaAtual(t) {
  tema = t || "";
  document
    .querySelectorAll("[data-tema]")
    .forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tema === tema)));
}
const data = (d) => (d ? d.split("-").reverse().join("/") : "Não informada");
function cartao(r, relacionado = false) {
  return `<article class="card"><strong>${esc(r.pergunta)}</strong><small>${esc(r.tema)}</small><div class="row"><span class="chip ${relacionado ? "g" : ""}">${relacionado ? "Relacionado" : r.defasado ? "Revisão necessária" : "Fonte oficial"}</span><button class="sm" data-id="${esc(r.id)}">Abrir orientação</button></div></article>`;
}
function marcarSecao(id, titulo) {
  document.querySelectorAll(".rail button").forEach((b) => b.removeAttribute("aria-current"));
  $(id).setAttribute("aria-current", "page");
  $("h1").textContent = titulo;
  document.title = `${titulo} · Orientação cidadã`;
}
function consulta() {
  location.hash = "consulta";
  corpo.classList.remove("modoHistorico");
  corpo.hidden = false;
  $("#temasView").hidden = true;
  marcarSecao("#rConsulta", "Fale por voz");
}
function temas() {
  pararVoz();
  location.hash = "temas";
  corpo.classList.remove("modoHistorico");
  corpo.hidden = true;
  $("#temasView").hidden = false;
  marcarSecao("#rTemas", "Explore os temas");
  atualizarTemas();
}
function abrirHistorico() {
  pararVoz();
  location.hash = "conversas";
  corpo.hidden = false;
  corpo.classList.add("modoHistorico");
  $("#temasView").hidden = true;
  marcarSecao("#rConversas", "Vamos conversar");
  chat.listar();
}
function atualizarTemas() {
  if (!estado) return;
  $("#listaTemas").innerHTML = estado.temas
    .map(
      (t, i) =>
        `<button class="themeCard" data-abrir-tema="${esc(t.nome)}"><span class="themeIcon">${["▤", "◈", "♧"][i] || "○"}</span><strong>${esc(t.nome)}</strong><span class="chip">${t.total} ${t.total === 1 ? "orientação" : "orientações"}</span><b>Abrir →</b></button>`,
    )
    .join("");
  $("#resumoTemas").textContent =
    `A base tem ${estado.total} orientações em ${estado.temas.length} temas. Escolha um para filtrar a consulta.`;
  $("#temaAplicado").textContent = tema
    ? `✓ Tema “${tema}” aplicado · use “voltar” para remover o filtro`
    : "Todos os temas disponíveis para consulta.";
  chat.renderHistorico();
}
function mostrar(r) {
  temaAtual(r.tema);
  const encontrado = r.status === "match";
  status(
    encontrado
      ? "Consulta concluída"
      : ["browse", "menu", "related"].includes(r.status)
        ? "Escolha uma orientação"
        : r.status === "ambiguous"
          ? "Preciso de mais detalhes"
          : r.status === "quit"
            ? "Sessão encerrada"
            : "Confira a orientação abaixo",
  );
  $("#ps").textContent = encontrado
    ? `Resposta consultada · ${r.latencia_ms} ms`
    : "Consulta à base local";
  $("#ans").className = "q" + (encontrado ? "" : " idle");
  revelar($("#ans"), encontrado ? r.registros[0].resumo : textoVisivel(r.mensagem));
  $("#cards").innerHTML =
    (encontrado
      ? r.registros
          .map(
            (v) =>
              `<article class="card"><strong>${esc(v.pergunta)}</strong><small>${esc(v.tema)}</small><div class="row"><span class="chip">${v.defasado ? "Revisão necessária" : "Fonte oficial"}</span><a class="sm" href="${esc(v.fonte)}" target="_blank" rel="noopener noreferrer">Ver fonte</a></div></article>`,
          )
          .join("")
      : r.registros.map((v) => cartao(v)).join("")) +
    r.relacionados.map((v) => cartao(v, true)).join("");
  if (!$("#cards").innerHTML)
    $("#cards").innerHTML = '<div class="empty">Nenhuma orientação para mostrar.</div>';
  const reg = encontrado && r.registros[0];
  $("#box").innerHTML = reg
    ? `<div class="warn"><h2>Aviso de confirmação</h2><p>${esc(reg.aviso)}</p><div class="ok">Fonte consultada em ${data(reg.data)}</div></div><div class="lim"><h2>Limitações</h2><p>${esc(estado.limitacao)}</p>${reg.defasado ? "<p>Registro com mais de 180 dias. Confira a fonte atual.</p>" : ""}</div>`
    : "";
  $("#box").parentElement.insertBefore($("#box"), $("#cards").nextSibling);
  $("#respostaCompleta").textContent = textoVisivel(r.texto);
  $("#textoCompleto").hidden = false;
  if (r.log_erro) registrarAviso(r.log_erro);
}
async function perguntar(texto, reiniciar = false) {
  pararVoz();
  const pergunta = base.find((item) => item.id === texto)?.pergunta || texto;
  $("#pergunta").value = pergunta;
  $("#q").value = pergunta;
  perguntaDireita(pergunta);
  const versao = ++geracao;
  consulta();
  $("#win").classList.add("busy");
  status("Buscando na base…");
  try {
    const r = await api("/api/consultar", {
      sid,
      texto,
      modelo,
      tema,
      reiniciar,
    });
    if (versao !== geracao) return;
    mostrar(r);
    registrarAviso(
      r.status === "match"
        ? "Consulta concluída. A orientação e a fonte estão disponíveis."
        : textoVisivel(r.mensagem),
    );
    if (texto.trim() && !reiniciar) {
      chat.registrarVoz(sid, pergunta, r, location.hash === "#consulta");
    }
  } catch (e) {
    if (versao !== geracao) return;
    status("Conexão indisponível");
    $("#ans").textContent =
      `${e.message} Verifique se o servidor local está em execução e tente novamente.`;
    $("#cards").innerHTML = '<div class="empty">Não foi possível consultar a base.</div>';
    $("#box").innerHTML = "";
    $("#textoCompleto").hidden = true;
    registrarAviso(e.message);
  } finally {
    if (versao === geracao) $("#win").classList.remove("busy");
  }
}
function novaConsulta() {
  pararVoz();
  ++geracao;
  sid = crypto.randomUUID().replaceAll("-", "");
  temaAtual("");
  $("#q").value = "";
  $("#pergunta").value = "";
  perguntaDireita("");
  $("#ps").textContent = "Aguardando pergunta";
  $("#vozStatus").textContent = "Toque no microfone para falar ou escreva sua pergunta à direita.";
  $("#cards").innerHTML =
    '<div class="empty">As orientações aparecem aqui quando você consulta.</div>';
  $("#box").innerHTML = "";
  $("#textoCompleto").hidden = true;
  $("#ans").textContent = "Pergunte sobre documentos, serviços digitais ou apoio comunitário.";
  status("Pronto para consultar");
  $("#win").classList.remove("busy");
  consulta();
  $("#pergunta").focus();
}
async function indicadores() {
  painel("Indicadores", "<p>Carregando relatórios…</p>");
  try {
    const r = await api("/api/indicadores");
    painel(
      "Indicadores",
      r.avaliacao
        ? `<p>Ambiente: ${esc(r.avaliacao.environment)} · Execução: ${esc(r.avaliacao.executed_at)}</p><table><thead><tr><th>Modelo</th><th>Corretas</th><th>Tempo médio</th></tr></thead><tbody>${Object.entries(
            r.avaliacao.metrics_by_template || {},
          )
            .map(
              ([k, v]) =>
                `<tr><td>${esc(k)}</td><td>${v.correct}/${v.total}</td><td>${v.average_query_time_ms} ms</td></tr>`,
            )
            .join(
              "",
            )}</tbody></table><p>${esc(r.avaliacao.methodology)}</p>${r.usabilidade ? `<h3>Roteiros de uso</h3><p>Conclusão: ${(r.usabilidade.task_completion_rate * 100).toFixed(0)}% · Participantes humanos: ${r.usabilidade.human_participants}</p><p>${esc(r.usabilidade.limitations)}</p>` : ""}`
        : "<p>Nenhum relatório de avaliação disponível. Execute a avaliação local para gerar os indicadores.</p>",
    );
  } catch (e) {
    painel("Indicadores", `<p>${esc(e.message)}</p>`);
  }
}
$("#form").onsubmit = (e) => {
  e.preventDefault();
  corpo.classList.contains("modoHistorico") ? chat.enviar($("#q").value) : perguntar($("#q").value);
};
$("#temaForm").onsubmit = (e) => {
  e.preventDefault();
  perguntar($("#temaPergunta").value);
};
$("#bClear").onclick = novaConsulta;
$("#nova").onclick = novaConsulta;
$("#bEdit").onclick = () => {
  pararVoz();
  status("Edite sua pergunta à direita");
  $("#pergunta").scrollIntoView({ block: "nearest" });
  $("#pergunta").focus();
  $("#pergunta").select();
};
$("#bBack").onclick = () => {
  temaAtual("");
  temas();
};
$("#rTemas").onclick = temas;
$("#rConsulta").onclick = consulta;
$("#abrirConsulta").onclick = consulta;
$("#agoraNao").onclick = () => $("#temaPergunta").focus();
$("#ajudaTemas").onclick = () =>
  painel(
    "Ajuda",
    "<p>Escolha um tema, faça uma pergunta ou abra uma orientação pelo título. Use “Todos os temas” para pesquisar em toda a base. Os assuntos relacionados permitem continuar a consulta.</p>",
  );
$("#rFontes").onclick = () =>
  painel(
    "Fontes verificadas",
    base
      .map(
        (r) =>
          `<article class="card"><strong>${esc(r.pergunta)}</strong><p>Revisão: ${data(r.data)}${r.defasado ? " · Atualização necessária" : ""}</p><a href="${esc(r.fonte)}" target="_blank" rel="noopener noreferrer">Consultar fonte oficial</a></article>`,
      )
      .join(""),
  );
$("#rApoio").onclick = () => {
  temaAtual("Apoio comunitário");
  perguntar("");
};
$("#rConversas").onclick = abrirHistorico;
$("#rIndicadores").onclick = indicadores;
$("#rConfiguracoes").onclick = () =>
  painel(
    "Configurações",
    `<label for="modelo">Modelo de resposta</label><select id="modelo">${(estado?.modelos || []).map((m) => `<option ${m === modelo ? "selected" : ""}>${esc(m)}</option>`).join("")}</select><label><input type="checkbox" id="movimento" ${document.body.classList.contains("semMovimento") ? "checked" : ""}> Reduzir animações</label><p>Histórico apenas na memória desta aba. Telemetria ${estado?.log ? "ativada com metadados minimizados" : "desativada"}.</p>`,
  );
document.addEventListener("change", (e) => {
  if (e.target.id === "modelo") modelo = e.target.value;
  if (e.target.id === "movimento") document.body.classList.toggle("semMovimento", e.target.checked);
});
document.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.id) {
    dialogo.close();
    perguntar(b.dataset.id);
  }
  if (b.dataset.pergunta) perguntar(b.dataset.pergunta);
  if (b.dataset.tema !== undefined) {
    temaAtual(b.dataset.tema);
    perguntar("");
  }
  if (b.dataset.abrirTema) {
    temaAtual(b.dataset.abrirTema);
    perguntar("");
  }
});
addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    $("#q").focus();
  }
});
function navegar() {
  if (location.hash === "#temas") temas();
  else if (location.hash === "#consulta") consulta();
  else {
    abrirHistorico();
    chat.desenhar();
  }
}
addEventListener("hashchange", navegar);
async function iniciar() {
  try {
    [estado, base] = await Promise.all([api("/api/estado"), api("/api/base")]);
    modelo = estado.modelo;
    $("#q").maxLength = estado.max;
    $("#nTemas").textContent = estado.temas.length;
    $("#fl").innerHTML = ["", ...estado.temas.map((t) => t.nome)]
      .map(
        (t) =>
          `<button class="f" data-tema="${esc(t)}" aria-pressed="${!t}">${esc(t || "Todos os temas")}</button>`,
      )
      .join("");
    base
      .filter((r) => r.defasado)
      .forEach((r) => registrarAviso(`${r.pergunta} — fonte revisada há mais de ${estado.dias} dias.`));
    atualizarTemas();
    if (location.hash === "#temas") temas();
  } catch (e) {
    status("Servidor indisponível");
    $("#ans").textContent =
      "Não foi possível carregar a base. Verifique o servidor local e recarregue a página.";
    registrarAviso(e.message);
  }
}
iniciar();

// ENVIO DAS CONSULTAS
$("#perguntaForm").onsubmit = (e) => {
  e.preventDefault();
  perguntar($("#pergunta").value);
};
$("#falarHistorico").onclick = () => {
  const conversa = chat.atual;
  if (conversa?.pendente) {
    $("#chatStatus").textContent = "Aguarde a resposta antes de mudar para voz.";
    return;
  }
  novaConsulta();
  if (conversa) {
    sid = conversa.sid;
    temaAtual(conversa.tema);
  }
  $("#pergunta").value = "";
  perguntaDireita("");
  consulta();
  $("#microfone").focus();
};
dialogo.addEventListener("close", () =>
  $(corpo.classList.contains("modoHistorico") ? "#chatPergunta" : "#pergunta").focus(),
);
navegar();
