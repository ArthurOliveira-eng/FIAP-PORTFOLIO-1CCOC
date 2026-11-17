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
  elemento.replaceChildren();
  texto.split(/(\s+)/).forEach((palavra, i) => {
    const span = document.createElement("span");
    span.textContent = palavra;
    if (palavra.trim() && animar && !movimentoReduzido()) {
      span.className = "palavra";
      span.style.animationDelay = `${Math.min(i * 22, 1000)}ms`;
    }
    elemento.append(span);
  });
}

export { $, esc, revelar };
