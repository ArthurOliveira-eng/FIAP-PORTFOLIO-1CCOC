const $ = (s) => document.querySelector(s);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
const movimentoReduzido = () =>
  document.body.classList.contains("semMovimento") ||
  (!document.body.classList.contains("movimentoCompleto") &&
    matchMedia("(prefers-reduced-motion: reduce)").matches);
// ANIMAÇÃO DO TEXTO
function revelar(elemento, texto, animar = true) {
  if (!animar || movimentoReduzido()) {
    elemento.textContent = texto;
    return;
  }
  const palavras = texto.match(/\S+\s*|\s+/g) || [];
  const intervalo = Math.min(65, 5200 / palavras.length);
  const fragmento = document.createDocumentFragment();
  palavras.forEach((palavra, i) => {
    const span = document.createElement("span");
    span.textContent = palavra;
    span.className = "palavra";
    span.style.animationDelay = `${i * intervalo}ms`;
    fragmento.append(span);
  });
  elemento.replaceChildren(fragmento);
}

function textoVisivel(texto = "") {
  return texto.replace(/^([ \t]*)[A-Z]\d{2,} - /gm, "$1")
    .replaceAll("um ID de registro", "uma orientação")
    .replaceAll("o ID de um registro relacionado", "um assunto relacionado");
}

export { $, esc, revelar, textoVisivel, movimentoReduzido };


// A linha acompanha o pedido e resume os registros realmente devolvidos pela API.
export function andamento(elemento, pergunta, resposta) {
  elemento.className = "linhaConsulta";
  elemento.replaceChildren();
  elemento.setAttribute("role", "status");
  if (resposta) {
    const itens = resposta.registros;
    elemento.textContent = resposta.status === "match"
      ? `Orientação encontrada · ${itens[0].pergunta}`
      : itens.length ? `${itens.length} opções para explorar` : "Busca concluída";
    return;
  }
  const dots = document.createElement("span");
  dots.className = "duplaConsulta";
  dots.setAttribute("aria-hidden", "true");
  dots.append(document.createElement("i"), document.createElement("i"));
  const fase = document.createElement("span");
  fase.textContent = "Recebendo sua pergunta…";
  elemento.append(dots, fase);
  setTimeout(() => {
    if (fase.isConnected) fase.textContent = pergunta ? `Buscando orientações para “${pergunta}”…` : "Buscando orientações do tema…";
  }, 280);
}
