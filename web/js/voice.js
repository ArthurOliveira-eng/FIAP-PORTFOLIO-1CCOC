import { $, revelar } from "./dom.js";
import { dialogo, painel, registrarAviso } from "./notifications.js";
export function criarVoz({ status, perguntaDireita }) {
  // DITADO PELO NAVEGADOR
  const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;
  let reconhecimento = null,
    consentiuVoz = false;
  function pararVoz() {
    if (reconhecimento) {
      const atual = reconhecimento;
      reconhecimento = null;
      atual.abort();
    }
    $("#microfone").setAttribute("aria-pressed", "false");
    $("#wave").classList.remove("on");
    document.body.classList.remove("ouvindo");
  }
  function iniciarVoz() {
    dialogo.close();
    if (!Reconhecimento) {
      $("#vozStatus").textContent =
        "Ditado indisponível neste navegador. Use um navegador compatível ou digite a pergunta.";
      return;
    }
    const r = new Reconhecimento();
    reconhecimento = r;
    r.lang = "pt-BR";
    r.continuous = false;
    r.interimResults = true;
    r.onstart = () => {
      if (reconhecimento !== r) return;
      document.body.classList.add("ouvindo");
      status("Ouvindo sua pergunta…");
      revelar($("#ans"), "Pode falar. Estou ouvindo.", false);
      $("#microfone").setAttribute("aria-pressed", "true");
      $("#vozStatus").textContent =
        "Ouvindo… fale sua pergunta. Clique no microfone para cancelar.";
      $("#wave").classList.add("on");
    };
    r.onresult = (e) => {
      if (reconhecimento !== r) return;
      const texto = Array.from(e.results)
        .map((v) => v[0].transcript)
        .join(" ")
        .slice(0, 500);
      $("#pergunta").value = texto;
      perguntaDireita(texto);
      revelar($("#ans"), texto);
      $("#vozStatus").textContent =
        "Confira sua pergunta à direita e clique na lupa para consultar.";
    };
    r.onerror = (e) => {
      if (reconhecimento !== r) return;
      const mensagens = {
        "not-allowed":
          "Permissão negada. Libere o microfone nas permissões deste site e tente novamente.",
        "service-not-allowed":
          "O serviço de ditado não está disponível neste navegador. Você pode digitar a pergunta.",
        "audio-capture":
          "Nenhum microfone disponível. Confira a conexão e as configurações do sistema.",
        "no-speech": "Não foi detectada fala. Tente novamente.",
        network:
          "O serviço de transcrição está indisponível. Confira a conexão ou digite sua pergunta.",
        aborted: "Ditado cancelado.",
      };
      const msg =
        mensagens[e.error] || "Não foi possível transcrever. Tente novamente ou digite a pergunta.";
      $("#vozStatus").textContent = msg;
      registrarAviso(msg);
    };
    r.onend = () => {
      if (reconhecimento !== r) return;
      reconhecimento = null;
      document.body.classList.remove("ouvindo");
      status("Confira sua pergunta");
      $("#microfone").setAttribute("aria-pressed", "false");
      $("#wave").classList.remove("on");
      if ($("#vozStatus").textContent.startsWith("Ouvindo"))
        $("#vozStatus").textContent = "Ditado encerrado. Confira o texto antes de pesquisar.";
      $("#pergunta").focus();
    };
    try {
      r.start();
    } catch (e) {
      pararVoz();
      $("#vozStatus").textContent =
        "Não foi possível iniciar o microfone. Confira a permissão do navegador.";
    }
  }
  $("#microfone").onclick = () => {
    if (reconhecimento) {
      pararVoz();
      status("Ditado interrompido");
      $("#vozStatus").textContent = "Você pode editar sua pergunta à direita e enviar pela lupa.";
      return;
    }
    if (!Reconhecimento) {
      $("#vozStatus").textContent =
        "Seu navegador não oferece ditado compatível. Digite sua pergunta ou tente outro navegador.";
      registrarAviso("Reconhecimento de voz indisponível neste navegador.");
      return;
    }
    if (!consentiuVoz) {
      painel(
        "Perguntar pelo microfone",
        '<p>O ditado usa o serviço de reconhecimento de voz do navegador, que pode enviar áudio para processamento online. Não fale dados pessoais ou senhas.</p><p>O texto aparecerá no campo para revisão antes de pesquisar. O aplicativo não armazena áudio.</p><button class="sm" id="ativarVoz">Continuar e ativar microfone</button>',
      );
      return;
    }
    iniciarVoz();
  };
  document.addEventListener("click", (e) => {
    if (e.target.closest("#ativarVoz")) {
      consentiuVoz = true;
      iniciarVoz();
    }
  });
  addEventListener("pagehide", pararVoz);
  return { parar: pararVoz };
}
