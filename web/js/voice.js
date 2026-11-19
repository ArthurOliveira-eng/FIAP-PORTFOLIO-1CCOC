import { ditadoLocal } from "./ditado-local.js";
import { $, revelar } from "./dom.js";
import { dialogo, painel, registrarAviso } from "./notifications.js";
export function criarVoz({ status, perguntaDireita, pesquisar }) {
  // DITADO PELO NAVEGADOR
  const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;
  let usandoBrave = false;
  if (navigator.brave?.isBrave) {
    navigator.brave.isBrave().then((resultado) => { usandoBrave = resultado; }).catch(() => {});
  }
  let reconhecimento = null,
    consentiuVoz = false;
  let local = null, liberarMedidor = () => {};
  const onda = $("#wave");
  const pontos = [...onda.children];
  const envelopes = pontos.map((_, i) => Math.sin(Math.PI * (i + 1) / (pontos.length + 1)));
  let intensidade = 0;
  function nivel(valor) {
    // Suaviza a entrada real sem interromper a fase do ciclo de cada ponto.
    intensidade += (valor - intensidade) * .25;
    pontos.forEach((ponto, i) => {
      ponto.style.setProperty("--salto", (4 + 14 * Math.sqrt(intensidade) * envelopes[i]).toFixed(1) + "px");
    });
  }
  function limparNivel() {
    intensidade = 0;
    pontos.forEach((ponto) => ponto.style.removeProperty("--salto"));
  }
  async function medirMicrofone(r) {
    let fluxo, audio, timer;
    const liberar = () => {
      clearInterval(timer);
      fluxo?.getTracks().forEach((track) => track.stop());
      if (audio && audio.state !== "closed") audio.close().catch(() => {});
    };
    liberarMedidor = liberar;
    try {
      fluxo = await navigator.mediaDevices.getUserMedia({audio: true});
      if (reconhecimento !== r) return liberar();
      audio = new AudioContext();
      const analisador = audio.createAnalyser();
      analisador.fftSize = 1024;
      audio.createMediaStreamSource(fluxo).connect(analisador);
      await audio.resume();
      if (reconhecimento !== r) return liberar();
      const amostras = new Float32Array(analisador.fftSize);
      timer = setInterval(() => {
        analisador.getFloatTimeDomainData(amostras);
        let energia = 0;
        for (const v of amostras) energia += v * v;
        nivel(Math.min(1, 12 * Math.sqrt(energia / amostras.length)));
      }, 65);
    } catch { liberar(); }
  }
  function pararVoz() {
    liberarMedidor();
    limparNivel();
    local?.cancelar();
    local = null;
    document.body.classList.remove("transcrevendo", "preparandoVoz");
    if (reconhecimento) {
      const atual = reconhecimento;
      reconhecimento = null;
      atual.abort();
    }
    $("#microfone").setAttribute("aria-pressed", "false");
    $("#wave").classList.remove("on");
    document.body.classList.remove("ouvindo", "preparandoVoz");
  }
  function iniciarVoz() {
    dialogo.close();
    document.body.classList.add("preparandoVoz");
    status("Preparando microfone…");
    if (usandoBrave || !Reconhecimento) {
      const mensagem = (texto) => { $("#vozStatus").textContent = texto; };
      local = ditadoLocal({
        ouvindo() {
          document.body.classList.remove("preparandoVoz");
          document.body.classList.add("ouvindo");
          $("#wave").classList.add("on");
          $("#microfone").setAttribute("aria-pressed", "true");
          status("Ouvindo sua pergunta…");
          revelar($("#ans"), "Pode falar.", false);
          mensagem("Faça uma pausa ou toque no microfone para concluir.");
        },
        nivel,
        processando() {
          document.body.classList.remove("ouvindo", "preparandoVoz");
          document.body.classList.add("transcrevendo");
          $("#microfone").setAttribute("aria-pressed", "false");
          status("Transcrevendo…");
          mensagem("Preparando sua pergunta.");
        },
        resultado: pesquisar,
        erro(texto) { pararVoz(); status("Ditado interrompido"); mensagem(texto); },
      });
      local.iniciar();
      return;
    }
    const r = new Reconhecimento();
    let falhou = false, frase = "";
    reconhecimento = r;
    r.lang = "pt-BR";
    r.continuous = false;
    r.interimResults = true;
    r.onstart = () => {
      if (reconhecimento !== r) return;
      medirMicrofone(r);
      document.body.classList.remove("preparandoVoz");
      document.body.classList.add("ouvindo");
      status("Ouvindo sua pergunta…");
      revelar($("#ans"), "Pode falar. Estou ouvindo.", false);
      $("#microfone").setAttribute("aria-pressed", "true");
      $("#vozStatus").textContent =
        "Ouvindo… fale sua pergunta. Toque no microfone para concluir.";
      $("#wave").classList.add("on");
    };
    r.onresult = (e) => {
      if (reconhecimento !== r) return;
      const texto = Array.from(e.results)
        .map((v) => v[0].transcript)
        .join(" ")
        .slice(0, 500);
      frase = texto.trim();
      $("#pergunta").value = texto;
      perguntaDireita(texto);
      revelar($("#ans"), texto, false);
      $("#vozStatus").textContent =
        "Ao terminar, sua pergunta será pesquisada.";
    };
    r.onerror = (e) => {
      if (reconhecimento !== r) return;
      falhou = true;
      status("Não foi possível transcrever");
      const mensagens = {
        "not-allowed":
          "Permissão negada. Libere o microfone nas permissões deste site e tente novamente.",
        "service-not-allowed":
          "O serviço de ditado não está disponível neste navegador. Você pode digitar a pergunta.",
        "audio-capture":
          "Nenhum microfone disponível. Confira a conexão e as configurações do sistema.",
        "no-speech": "Não foi detectada fala. Tente novamente.",
        network: usandoBrave
          ? "O serviço de ditado não está disponível neste Brave. Para testar a transcrição, abra esta mesma página no Google Chrome e permita o microfone. Você também pode continuar digitando aqui."
          : "O navegador não conseguiu acessar o serviço de reconhecimento de voz. Isso não indica necessariamente falha do seu microfone ou do servidor local. Tente novamente ou abra esta mesma página em outro navegador com suporte a ditado.",
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
      liberarMedidor();
      limparNivel();
      document.body.classList.remove("ouvindo", "preparandoVoz");
      $("#microfone").setAttribute("aria-pressed", "false");
      $("#wave").classList.remove("on");
      if (!falhou && frase) pesquisar(frase);
      else if (!falhou) status("Não ouvi uma pergunta. Tente novamente.");
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
      reconhecimento.stop();
      status("Concluindo sua pergunta…");
      return;
    }
    if (local) { local.concluir(); return; }
    if (!consentiuVoz) {
      painel(
        "Perguntar pelo microfone",
        (usandoBrave || !Reconhecimento ? "<p>O áudio será transcrito neste computador em português. Faça uma pausa para concluir.</p>" : '<p>O ditado usa o serviço de reconhecimento de voz do navegador, que pode enviar áudio para processamento online. Não fale dados pessoais ou senhas.</p>') + '<p>Ao terminar de falar, o assistente pesquisa as palavras reconhecidas e mostra a orientação. O aplicativo não armazena áudio.</p><button class="sm" id="ativarVoz">Continuar e ativar microfone</button>',
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
