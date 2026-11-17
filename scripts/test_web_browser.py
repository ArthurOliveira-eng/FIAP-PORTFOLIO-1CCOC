"""Verificação opcional no Edge; requer Playwright apenas no desenvolvimento."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1200, 'height': 760})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8000/#consulta')
    page.wait_for_selector('[data-tema]', state='attached')
    page.locator('#q').fill('Como recuperar minha senha do gov.br?')
    page.locator('#q').press('Enter')
    expect(page.locator('#st')).to_have_text('Consulta concluída')
    expect(page.locator('#ans')).to_contain_text('Esqueci minha senha')
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-consulta.png'), full_page=True)
    page.locator('#rTemas').click()
    page.wait_for_selector('#listaTemas button')
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-temas.png'), full_page=True)
    page.locator('[data-abrir-tema="Documentos"]').click()
    expect(page.locator('#st')).to_have_text('Escolha uma orientação')
    page.locator('[data-id="D02"]').first.click()
    expect(page.locator('#st')).to_have_text('Consulta concluída')
    page.get_by_role('button', name='Conversas', exact=True).click()
    page.wait_for_selector('#listaHistorico .conversaItem')
    page.locator('#listaHistorico .conversaItem').first.click()
    expect(page.locator('#perguntaHistorico')).to_have_text('D02')
    expect(page.locator('#respostaHistorico')).to_contain_text('Fonte:')
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-historico.png'), full_page=True)
    page.locator('#falarHistorico').click()
    for label in ['Fontes verificadas', 'Indicadores', 'Configurações', 'Notificações']:
        page.get_by_role('button', name=label, exact=True).click()
        page.wait_for_selector('dialog[open]')
        if label == 'Configurações':
            page.locator('#modelo').select_option('template_a_v1')
        if label == 'Indicadores':
            page.wait_for_selector('dialog table')
        page.locator('#fechar').click()
    page.locator('#bClear').click()
    page.locator('#q').fill('CPF')
    page.locator('#q').press('Enter')
    expect(page.locator('#st')).to_have_text('Preciso de mais detalhes')
    expect(page.locator('#cards .card')).to_have_count(2)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.screenshot(animations='disabled', path=str(ROOT / 'artifacts/web-celular.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.route('**/api/consultar', lambda route: route.abort())
    page.locator('#q').fill('D01')
    page.locator('#q').press('Enter')
    expect(page.locator('#st')).to_have_text('Conexão indisponível')
    expect(page.locator('#cards')).to_contain_text('Não foi possível consultar')
    assert not errors, errors
    browser.close()
    print('Fluxos web, diálogos, celular e falha de conexão aprovados.')
