const $ = (s) => document.querySelector(s);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
const movimentoReduzido = () =>
  matchMedia("(prefers-reduced-motion: reduce)").matches ||
  document.body.classList.contains("semMovimento");
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

export { $, esc, revelar, textoVisivel };
