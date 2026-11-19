// Cada sessão possui seus recursos. Cancelar também invalida permissões e respostas tardias.
export function ditadoLocal({ dispositivo, ouvindo, nivel, processando, resultado, erro }) {
  let stream, contexto, captura, timer, cancelado = false, terminou = false;
  const blocos = [];
  let duracaoFala = 0;
  const pedido = new AbortController();
  function liberar() {
    clearTimeout(timer);
    if (captura) {
      captura.port.onmessage = null;
      captura.disconnect();
    }
    stream?.getTracks().forEach((track) => track.stop());
    if (contexto && contexto.state !== "closed") contexto.close().catch(() => {});
  }
  async function concluir() {
    if (terminou || cancelado || !captura) return;
    terminou = true;
    liberar();
    processando();
    try {
      if (!blocos.length) throw Error("Gravação muito curta. Tente novamente.");
      if (duracaoFala < 200) throw Error("O áudio ficou muito baixo. Confira o microfone selecionado e tente novamente.");
      const r = await fetch("/api/ditado", { method: "POST", body: new Blob(blocos, {type: "application/octet-stream"}), signal: pedido.signal });
      const dados = await r.json();
      if (!r.ok || !dados.texto) throw Error(dados.erro || "Não entendi a pergunta. Tente falar novamente.");
      if (!cancelado) resultado(dados.texto);
    } catch (e) { if (!cancelado) erro(e.message); }
  }
  async function iniciar() {
    try {
      contexto = new AudioContext({sampleRate: 16000});
      await contexto.resume();
      if (cancelado) return;
      stream = await navigator.mediaDevices.getUserMedia({ audio: {deviceId: dispositivo ? {exact: dispositivo} : undefined, channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true} });
      if (cancelado) return liberar();
      await contexto.audioWorklet.addModule("/js/pcm.js");
      if (cancelado) return;
      captura = new AudioWorkletNode(contexto, "captura-pcm");
      contexto.createMediaStreamSource(stream).connect(captura);
      captura.connect(contexto.destination); // A saída do processador permanece silenciosa.
      let ultimoSom = 0;
      captura.port.onmessage = ({data}) => {
        if (terminou || cancelado) return;
        blocos.push(data.pcm);
        nivel(Math.min(1, data.rms * 12));
        if (data.rms > 0.004) {
          ultimoSom = performance.now();
          duracaoFala += 64;
        }
        if (blocos.length >= 463 || (duracaoFala > 300 && ultimoSom && performance.now() - ultimoSom > 2200)) concluir();
      };
      ouvindo();
      timer = setTimeout(concluir, 29000);
    } catch (e) {
      liberar();
      if (!cancelado) erro(e.name === "NotAllowedError" ? "Permita o microfone nas configurações deste site." : "Confira o dispositivo de entrada e tente novamente.");
    }
  }
  return { iniciar, concluir, cancelar() { cancelado = true; pedido.abort(); liberar(); } };
}
