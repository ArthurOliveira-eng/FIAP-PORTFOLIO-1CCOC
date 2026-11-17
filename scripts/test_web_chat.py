"""Valida conversas, navegação e enquadramento no Edge."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def conferir_enquadramento(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.evaluate('document.documentElement.scrollHeight <= innerHeight')
    caixa = page.locator('#chatForm').bounding_box()
    assert caixa and caixa['y'] + caixa['height'] <= page.viewport_size['height']


with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    erros, pedidos = [], []
    page.on('pageerror', lambda e: erros.append(str(e)))
    page.on('request', lambda r: pedidos.append(r.post_data_json) if r.url.endswith('/api/consultar') else None)
    page.goto('http://127.0.0.1:8000')
    expect(page.locator('#chatForm')).to_be_visible()
    expect(page.locator('#stage')).to_be_hidden()
    conferir_enquadramento(page)
    page.locator('#chatPergunta').press('Enter')
    expect(page.locator('#chatStatus')).to_contain_text('Digite uma pergunta')
    assert not pedidos
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-chat-inicio.png'))

    page.locator('#chatPergunta').fill('D01')
    page.locator('#chatPergunta').press('Enter')
    expect(page.locator('#respostaHistorico')).to_contain_text('número único')
    expect(page.locator('#enviarChat')).to_be_enabled()
    page.locator('#chatPergunta').fill('D02')
    page.locator('#enviarChat').click()
    expect(page.locator('#respostaHistorico')).to_contain_text('Fonte:')
    expect(page.locator('.trocaMensagem')).to_have_count(2)
    expect(page.locator('#listaHistorico .conversaItem')).to_have_count(1)
    assert pedidos[0]['sid'] == pedidos[1]['sid']
    assert len(pedidos) == 2
    page.locator('#novaHistorico').click()
    expect(page.locator('#historicoVazio')).to_be_visible()
    page.locator('#chatPergunta').fill('S02')
    page.locator('#chatPergunta').press('Enter')
    expect(page.locator('#respostaHistorico')).to_contain_text('Esqueci minha senha')
    assert pedidos[-1]['sid'] != pedidos[0]['sid']
    page.locator('#listaHistorico .conversaItem').last.click()
    expect(page.locator('.trocaMensagem')).to_have_count(2)
    assert len(pedidos) == 3

    page.locator('#falarHistorico').click()
    expect(page.locator('#stage')).to_be_visible()
    expect(page.locator('#chatForm')).to_be_hidden()
    page.locator('#pergunta').fill('D01')
    page.locator('#pergunta').press('Enter')
    expect(page.locator('#st')).to_have_text('Consulta concluída')
    assert pedidos[-1]['sid'] == pedidos[0]['sid']
    page.locator('#rConversas').click()
    expect(page.locator('.trocaMensagem')).to_have_count(3)
    expect(page.locator('#listaHistorico .conversaItem')).to_have_count(2)
    page.locator('.toast').wait_for(state='hidden')
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-chat-mensagens.png'))

    # Falha de rede permite reenviar sem sair do chat.
    page.route('**/api/consultar', lambda route: route.abort())
    page.locator('#chatPergunta').fill('D03')
    page.locator('#enviarChat').click()
    expect(page.locator('#respostaHistorico')).to_contain_text('servidor local')
    expect(page.get_by_role('button', name='Tentar novamente')).to_be_visible()
    quantidade_mensagens = page.locator('.trocaMensagem').count()
    page.unroute('**/api/consultar')
    page.get_by_role('button', name='Tentar novamente').click()
    expect(page.locator('#respostaHistorico')).to_contain_text('Fonte:')
    expect(page.locator('.trocaMensagem')).to_have_count(quantidade_mensagens)
    expect(page.get_by_role('button', name='Tentar novamente')).to_have_count(0)

    # Uma resposta atrasada não substitui a conversa que está aberta.
    retidas = []
    page.route('**/api/consultar', lambda route: retidas.append(route))
    page.locator('#chatPergunta').fill('D04')
    page.locator('#enviarChat').click()
    expect(page.locator('#enviarChat')).to_be_disabled()
    page.locator('#novaHistorico').click()
    expect(page.locator('#historicoVazio')).to_be_visible()
    assert len(retidas) == 1
    retidas[0].continue_()
    page.unroute('**/api/consultar')
    expect(page.locator('#listaHistorico [aria-busy="true"]')).to_have_count(0)
    expect(page.locator('#historicoVazio')).to_be_visible()
    page.locator('#listaHistorico .conversaItem').last.click()
    expect(page.locator('#perguntaHistorico')).to_have_text('D04')
    expect(page.locator('#respostaHistorico')).to_contain_text('Fonte:')

    for largura, altura in [(1920, 1080), (1366, 768), (1024, 768), (768, 1024), (390, 844)]:
        page.set_viewport_size({'width': largura, 'height': altura})
        conferir_enquadramento(page)
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-chat-celular.png'))
    page.locator('#noite').click()
    expect(page.locator('body')).to_have_class('dark')
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-chat-noturno.png'))
    page.locator('#limparHistoricoTela').click()
    expect(page.locator('#mensagensHistorico')).to_be_hidden()
    expect(page.locator('#listaHistorico .conversaItem')).to_have_count(0)

    # Resposta de voz atrasada não abre uma conversa sobre a tela nova.
    retidas.clear()
    page.route('**/api/consultar', lambda route: retidas.append(route))
    page.locator('#falarHistorico').click()
    page.locator('#pergunta').fill('D01')
    page.locator('#pergunta').press('Enter')
    expect(page.locator('#st')).to_have_text('Buscando na base…')
    page.locator('#rConversas').click()
    page.locator('#novaHistorico').click()
    assert len(retidas) == 1
    retidas[0].continue_()
    page.unroute('**/api/consultar')
    expect(page.locator('#listaHistorico .conversaItem')).to_have_count(1)
    expect(page.locator('#historicoVazio')).to_be_visible()
    assert not erros, erros
    browser.close()
    print('Conversas, sessões, voz, falha de rede e enquadramento aprovados.')
