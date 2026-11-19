"""Verifica movimento entre quadros, nível captado e encerramento dos estados de voz."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

URL = os.getenv("POLIS_URL", "http://127.0.0.1:8000")
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1366, "height": 900}, reduced_motion="no-preference")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # Uma fonte de áudio controlada percorre o mesmo AnalyserNode da captura nativa.
    page.add_init_script("""
      navigator.mediaDevices.getUserMedia = async () => {
        const context = new AudioContext();
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        gain.gain.value = .001;
        oscillator.connect(gain).connect(context.createMediaStreamDestination());
        const destination = context.createMediaStreamDestination();
        gain.connect(destination);
        oscillator.start();
        await context.resume();
        window.audioTeste = {context, gain, stream: destination.stream};
        return destination.stream;
      };
      window.SpeechRecognition = class {
        constructor() { window.ditadoTeste = this; }
        start() { this.onstart(); }
        stop() { this.onend(); }
        abort() { this.onend(); }
      };
    """)
    page.goto(URL + "/#consulta")
    page.wait_for_selector("[data-tema]", state="attached")
    page.locator("#microfone").click()
    page.locator("#ativarVoz").click()
    expect(page.locator("#microfone")).to_have_attribute("aria-pressed", "true")
    page.wait_for_function("window.audioTeste")
    def transform(selector, pseudo=None):
        return page.locator(selector).first.evaluate("(e,p) => getComputedStyle(e,p).transform", pseudo)
    def moves(selector, pseudo=None):
        before = transform(selector, pseudo)
        page.wait_for_timeout(210)
        assert transform(selector, pseudo) != before, selector
    moves(".orb")
    moves(".haloOrbe", "::before")
    moves("#wave i")
    page.wait_for_timeout(250)
    quiet = page.locator("#wave i").nth(9).evaluate("e => parseFloat(e.style.getPropertyValue('--salto'))")
    page.evaluate("audioTeste.gain.gain.value = .1")
    page.wait_for_timeout(700)
    loud = page.locator("#wave i").nth(9).evaluate("e => parseFloat(e.style.getPropertyValue('--salto'))")
    assert loud > quiet + 2, (quiet, loud)
    page.screenshot(path=str(Path(os.environ["TEMP"]) / "polis-motion-voz.png"))
    page.evaluate("ditadoTeste.onresult({results:[[{transcript:'Como recuperar minha senha do gov.br?'}]]})")
    page.locator("#microfone").click()
    expect(page.locator("#st")).to_have_text("Consulta concluída")
    expect(page.locator("#ans")).to_contain_text("Esqueci minha senha")
    assert page.evaluate("audioTeste.stream.getTracks().every(t => t.readyState === 'ended')")
    page.locator("#rConversas").click()
    page.locator("#novaHistorico").click()
    held = []
    page.route("**/api/consultar", lambda route: held.append(route))
    page.locator("#chatPergunta").fill("Como emitir a CIN?")
    page.locator("#enviarChat").click()
    expect(page.locator(".duplaConsulta i")).to_have_count(2)
    moves(".duplaConsulta i")
    assert transform(".duplaConsulta i:first-child") != transform(".duplaConsulta i:last-child")
    page.screenshot(path=str(Path(os.environ["TEMP"]) / "polis-motion-busca.png"))
    held[0].continue_()
    page.unroute("**/api/consultar")
    expect(page.locator(".ondaResposta")).to_be_visible()
    moves(".ondaResposta i")
    expect(page.locator(".ondaResposta")).to_have_count(0, timeout=10000)
    expect(page.locator(".duplaConsulta")).to_have_count(0)
    for dark in [True, False]:
        page.evaluate("dark => document.body.classList.toggle('dark', dark)", dark)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.emulate_media(reduced_motion="reduce")
    page.locator("#falarHistorico").click()
    page.locator("#microfone").click()
    assert page.locator("#wave i").first.evaluate("e => getComputedStyle(e).animationName") == "none"
    page.locator("#stage [data-ativar-movimento]").click()
    moves("#wave i")
    assert page.evaluate("document.body.classList.contains('movimentoCompleto')")
    page.reload()
    assert page.evaluate("document.body.classList.contains('movimentoCompleto')")
    assert page.locator(".orb").evaluate("e => getComputedStyle(e).animationName") != "none"
    page.locator("#rConversas").click()
    assert not page.evaluate("document.body.classList.contains('ouvindo')")
    assert not errors, errors
    browser.close()
    print("Orbe, halos, ondas, nível de áudio, conclusão, mensagens, celular e movimento reduzido aprovados.")
