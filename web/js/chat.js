import { $, esc, textoVisivel, revelar } from "./dom.js";
import { api } from "./api.js";

// CONVERSAS DA ABA
export function criarChat({ abrirTela, modeloAtual, registrarAviso, aoLimpar }) {
  let historico = [],
    selecionada = null;
  function abrirHistorico() {
    abrirTela();
    listarHistorico();
  }
  function listarHistorico() {
    const filtro = $("#filtroHistorico").value.toLocaleLowerCase();
    $("#listaHistorico").innerHTML =
      historico
        .filter((h) => h.pergunta.toLocaleLowerCase().includes(filtro))
        .map(
          (h) =>
            `<button class="conversaItem ${h.chave === selecionada ? "selecionada" : ""}" data-hist="${h.chave}" aria-busy="${Boolean(h.pendente)}"><span class="avatarMini"></span><span><strong>${esc(h.pergunta)}</strong><small>${esc(h.hora || "Nesta sessão")}</small></span></button>`,
        )
        .join("") || '<p class="hint">Nenhuma conversa encontrada.</p>';
  }
  function lerConversa(chave) {
    const h = historico.find((v) => v.chave === chave);
    if (!h) return;
    selecionada = chave;
    abrirHistorico();
    desenharConversa();
  }

  // CONVERSAS POR TEXTO
  function criarConversa(texto, sessao = crypto.randomUUID().replaceAll("-", "")) {
    const conversa = {
      chave: crypto.randomUUID(),
      sid: sessao,
      pergunta: texto,
      tema: "",
      ids: [],
      hora: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      mensagens: [],
      pendente: false,
    };
    historico.unshift(conversa);
    historico = historico.slice(0, 50);
    return conversa;
  }
  function guardarResposta(conversa, mensagem, resposta) {
    mensagem.resposta = resposta;
    conversa.resposta = resposta;
    conversa.ids = resposta.ids;
    conversa.tema = resposta.tema || "";
    renderHistorico();
    listarHistorico();
  }
  function desenharConversa(animar = false) {
    const conversa = historico.find((h) => h.chave === selecionada);
    const mensagens = conversa?.mensagens || [];
    $("#historicoVazio").hidden = mensagens.length > 0;
    $("#mensagensHistorico").hidden = !mensagens.length;
    $("#sugestoesChat").hidden = mensagens.length > 0;
    $("#enviarChat").disabled = Boolean(conversa?.pendente);
    $("#chatStatus").textContent = conversa?.pendente
      ? "Consultando a base…"
      : "Enter envia · Shift + Enter quebra a linha";
    $("#mensagensHistorico").replaceChildren();
    mensagens.forEach((m, i) => {
      const ultimo = i === mensagens.length - 1;
      const bloco = document.createElement("article");
      bloco.className = "trocaMensagem";
      bloco.innerHTML = `<p class="balaoPergunta" ${ultimo ? 'id="perguntaHistorico"' : ""}></p>
   <div class="respostaConversa"><span class="avatarMini" aria-hidden="true"></span><div class="conteudoResposta">
   <pre ${ultimo ? 'id="respostaHistorico"' : ""}></pre><div class="fontesChat"></div></div></div>`;
      bloco.querySelector(".balaoPergunta").textContent = m.pergunta;
      const texto = m.resposta?.texto || m.erro || "Consultando a base…";
      const respostaElemento = bloco.querySelector("pre");
      if (!m.resposta && !m.erro) {
        respostaElemento.classList.add("carregandoResposta");
        respostaElemento.setAttribute("role", "status");
        respostaElemento.innerHTML = '<span class="sr">Preparando resposta…</span><i aria-hidden="true"></i><i aria-hidden="true"></i><i aria-hidden="true"></i>';
      } else {
        revelar(respostaElemento, textoVisivel(texto), animar && ultimo);
      }
      const fontes = bloco.querySelector(".fontesChat");
      if (m.resposta) {
        fontes.innerHTML = m.resposta.registros
          .filter(() => m.resposta.status === "match")
          .map(
            (r) =>
              `<a class="sm" href="${esc(r.fonte)}" target="_blank" rel="noopener noreferrer">Fonte oficial</a>`,
          )
          .join("");
        const opcoes =
          m.resposta.status === "match" ? m.resposta.relacionados : m.resposta.registros;
        fontes.innerHTML += opcoes
          .map(
            (r) =>
              `<button class="sm" data-chat-id="${esc(r.id)}">${esc(r.pergunta)}</button>`,
          )
          .join("");
      } else if (m.erro) {
        fontes.innerHTML = `<button class="sm" data-repetir="${i}">Tentar novamente</button>`;
      }
      $("#mensagensHistorico").append(bloco);
    });
    const rolagem = $("#chatRolagem");
    const ultimaMensagem = $("#mensagensHistorico").lastElementChild;
    if (ultimaMensagem)
      rolagem.scrollTop +=
        ultimaMensagem.getBoundingClientRect().top - rolagem.getBoundingClientRect().top - 16;
  }
  function novaConversa() {
    selecionada = null;
    $("#chatPergunta").value = "";
    $("#filtroHistorico").value = "";
    $("#q").value = "";
    abrirHistorico();
    desenharConversa();
    $("#chatPergunta").focus();
  }
  async function enviarChat(texto, repetida = null, rotulo = texto) {
    texto = texto.trim();
    if (!texto) {
      $("#chatStatus").textContent = "Digite uma pergunta para iniciar a consulta.";
      return;
    }
    let conversa = historico.find((h) => h.chave === selecionada);
    if (conversa?.pendente) return;
    if (!conversa) conversa = criarConversa(rotulo);
    selecionada = conversa.chave;
    const mensagem = repetida || { pergunta: rotulo, consulta: texto };
    if (!repetida) conversa.mensagens.push(mensagem);
    delete mensagem.erro;
    conversa.pendente = true;
    $("#chatPergunta").value = "";
    abrirHistorico();
    desenharConversa();
    try {
      const [resposta] = await Promise.all([api("/api/consultar", {
        sid: conversa.sid,
        texto,
        modelo: modeloAtual(),
        tema: conversa.tema,
      }), new Promise((resolve) => setTimeout(resolve, 450))]);
      if (!historico.includes(conversa)) return;
      guardarResposta(conversa, mensagem, resposta);
      if (resposta.log_erro) registrarAviso(resposta.log_erro);
    } catch (e) {
      mensagem.erro = `${e.message} Confira o servidor local e tente novamente.`;
    } finally {
      conversa.pendente = false;
      listarHistorico();
      renderHistorico();
      if (selecionada === conversa.chave) desenharConversa(true);
    }
  }
  function renderHistorico(filtro = "") {
    $("#conversas").innerHTML =
      historico
        .filter((h) => h.pergunta.toLocaleLowerCase().includes(filtro.toLocaleLowerCase()))
        .map(
          (h) =>
            `<button class="historyItem" data-hist="${h.chave}" aria-busy="${Boolean(h.pendente)}">${esc(h.pergunta)}</button>`,
        )
        .join("") || '<p class="hint">Nenhuma consulta nesta sessão.</p>';
  }
  $("#filtroHistorico").oninput = listarHistorico;
  $("#novaHistorico").onclick = novaConversa;
  $("#limparHistoricoTela").onclick = () => {
    aoLimpar();
    historico = [];
    renderHistorico();
    novaConversa();
  };
  $("#chatForm").onsubmit = (e) => {
    e.preventDefault();
    enviarChat($("#chatPergunta").value);
  };
  $("#chatPergunta").onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      $("#chatForm").requestSubmit();
    }
  };
  document.addEventListener("click", (e) => {
    const botao = e.target.closest("button");
    if (!botao) return;
    if (botao.dataset.chatTexto) enviarChat(botao.dataset.chatTexto);
    if (botao.dataset.chatId) enviarChat(botao.dataset.chatId, null, botao.textContent.trim());
    if (botao.dataset.repetir !== undefined) {
      const conversa = historico.find((h) => h.chave === selecionada);
      const mensagem = conversa?.mensagens[Number(botao.dataset.repetir)];
      if (mensagem && !conversa.pendente) enviarChat(mensagem.consulta || mensagem.pergunta, mensagem);
    }
  });
  $("#buscarConversas").oninput = (e) => renderHistorico(e.target.value);
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-hist]");
    if (b) lerConversa(b.dataset.hist);
  });

  function registrarVoz(sessao, texto, resposta, selecionar) {
    const conversa = historico.find((h) => h.sid === sessao) || criarConversa(texto, sessao);
    const mensagem = { pergunta: texto };
    conversa.mensagens.push(mensagem);
    if (selecionar) selecionada = conversa.chave;
    guardarResposta(conversa, mensagem, resposta);
    if (selecionada === conversa.chave) desenharConversa();
  }
  return {
    enviar: enviarChat,
    desenhar: desenharConversa,
    listar: listarHistorico,
    renderHistorico,
    registrarVoz,
    nova: novaConversa,
    get atual() {
      return historico.find((h) => h.chave === selecionada);
    },
  };
}
