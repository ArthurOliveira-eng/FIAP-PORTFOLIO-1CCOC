import { $ } from "./dom.js";
export function iniciarPreferencias() {
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
