"""Contratos HTTP e isolamento da interface web local."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from src.web import Servico, criar_manipulador
from src.config import KNOWLEDGE_PATH, DEFAULT_TEMPLATE
from src.knowledge_base import KnowledgeBase


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servico = Servico(KnowledgeBase.load(KNOWLEDGE_PATH), DEFAULT_TEMPLATE, None)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), criar_manipulador(cls.servico))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def consultar(self, **dados):
        pedido = {'sid': 'sessaoTeste123', 'texto': '', **dados}
        req = Request(self.url + '/api/consultar', data=json.dumps(pedido).encode(),
                      headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=5) as resposta:
            return json.load(resposta)

    def test_consulta_filtro_e_reinicio(self):
        self.assertEqual(self.consultar(texto='D02', reiniciar=True)['ids'], ['D02'])
        self.assertIn('S05', self.consultar(texto='relacionados')['ids'])
        self.assertEqual(self.consultar(tema='Documentos', texto='Como recuperar minha senha do gov.br?')['status'], 'no_match')
        self.assertEqual(self.consultar(tema='', texto='Como recuperar minha senha do gov.br?')['ids'], ['S02'])
        self.assertEqual(self.consultar(reiniciar=True, texto='relacionados')['status'], 'invalid_option')

    def test_sessoes_e_modelos(self):
        self.consultar(sid='sessaoPrimeira', tema='Documentos')
        r = self.consultar(sid='sessaoSegunda', texto='Como recuperar minha senha do gov.br?', modelo='template_a_v1')
        self.assertEqual(r['ids'], ['S02'])
        self.assertIsNone(r['tema'])
        self.assertIn('Fonte:', r['texto'])

    def test_ambiguidades_e_erros(self):
        self.assertEqual(self.consultar(tema='', texto='CPF')['status'], 'ambiguous')
        self.assertEqual(self.consultar(texto='x'*501)['status'], 'invalid_input')
        for dados in ({'sid':'!'}, {'modelo':'inexistente'}, {'tema':'inexistente'}):
            with self.subTest(dados=dados), self.assertRaises(HTTPError) as erro:
                self.consultar(**dados)
            self.assertEqual(erro.exception.code, 400)
        req = Request(self.url+'/api/consultar',data=b'[]')
        with self.assertRaises(HTTPError) as erro:
            urlopen(req,timeout=5)
        self.assertEqual(erro.exception.code,400)

    def test_recursos_e_base(self):
        for rota in ('/', '/app.js', '/style.css', '/inter.woff2', '/api/estado', '/api/base', '/api/indicadores'):
            with self.subTest(rota=rota), urlopen(self.url+rota,timeout=5) as resposta:
                self.assertEqual(resposta.status,200)
                self.assertTrue(resposta.read())
        with self.assertRaises(HTTPError) as erro:
            urlopen(self.url+'/../data/knowledge_base.json',timeout=5)
        self.assertEqual(erro.exception.code,404)
