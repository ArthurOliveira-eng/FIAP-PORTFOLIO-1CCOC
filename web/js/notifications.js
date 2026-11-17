import { $, esc } from "./dom.js";
const dialogo = $("#dialogo");
let avisos = [];
$("#fechar").onclick = () => dialogo.close();
function painel(titulo, html) {
  $("#dialogTitle").textContent = titulo;
  $("#dialogBody").innerHTML = html;
  if (!dialogo.open) dialogo.showModal();
}
let naoLidas = 0,
  toastTimer;
const toast = $("#toast");
function registrarAviso(texto) {
  avisos.unshift({ texto, hora: new Date().toLocaleTimeString("pt-BR") });
  avisos = avisos.slice(0, 50);
  naoLidas++;
  $(".dot").hidden = false;
  $(".dot").textContent = String(Math.min(naoLidas, 99));
  toast.textContent = texto;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.hidden = true), 5000);
}
$("#notificacoes").onclick = () => {
  painel(
    "Notificações",
    avisos.length
      ? '<p>Eventos desta aba, sem notificações externas.</p><button class="sm" id="limparAvisos">Limpar notificações</button>' +
          avisos
            .map(
              (a) =>
                `<article class="card"><small>${esc(a.hora)}</small><p>${esc(a.texto)}</p></article>`,
            )
            .join("")
      : "<p>Nenhum aviso no momento.</p>",
  );
  naoLidas = 0;
  $(".dot").hidden = true;
};
document.addEventListener("click", (e) => {
  if (e.target.closest("#limparAvisos")) {
    avisos = [];
    naoLidas = 0;
    $(".dot").hidden = true;
    dialogo.close();
  }
});
export { dialogo, painel, registrarAviso };
