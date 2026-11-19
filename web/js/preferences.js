import { $, movimentoReduzido } from "./dom.js";
export function iniciarPreferencias() {
  let movimento = "automatico";
  try { movimento = localStorage.getItem("polis-movimento") || movimento; } catch {}
  aplicarMovimento(movimento);
  matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", () => {
    aplicarMovimento(preferenciaMovimento());
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-ativar-movimento]")) aplicarMovimento("completo");
  });

  // PREFERÊNCIA DE TEMA
  const noite = $("#noite");
  let escuro = matchMedia("(prefers-color-scheme: dark)").matches;
  try {
    const salvo = localStorage.getItem("citizen-tema");
    if (salvo) escuro = salvo === "escuro";
  } catch (e) {}
  function aplicarNoite() {
    document.body.classList.toggle("dark", escuro);
    noite.setAttribute("aria-pressed", String(escuro));
    noite.textContent = escuro ? "☀" : "☾";
  }
  aplicarNoite();
  noite.onclick = () => {
    escuro = !escuro;
    aplicarNoite();
    try {
      localStorage.setItem("citizen-tema", escuro ? "escuro" : "claro");
    } catch (e) {}
  };
}

export function preferenciaMovimento() {
  return document.body.classList.contains("movimentoCompleto") ? "completo"
    : document.body.classList.contains("semMovimento") ? "reduzido" : "automatico";
}
export function aplicarMovimento(valor) {
  document.body.classList.toggle("movimentoCompleto", valor === "completo");
  document.body.classList.toggle("semMovimento", valor === "reduzido");
  document.querySelectorAll("[data-ativar-movimento]").forEach((botao) => {
    botao.hidden = !movimentoReduzido();
  });
  try { localStorage.setItem("polis-movimento", valor); } catch {}
}
