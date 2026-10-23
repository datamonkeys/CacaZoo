import unittest

from caca_zoo.relatorio import relatorio
from caca_zoo.zooniverse import PROJETOS


class TesteRelatorio(unittest.TestCase):
    def test_escapa(self):
        it = {"id": "1", "nota": 1.0, "motivo": "<b>x</b>", "urls": ['https://x/a.png?b=1&c="2"']}
        h = relatorio({"kn": (PROJETOS["kn"], [it])})
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", h)
        self.assertIn("&amp;c=&quot;2&quot;", h)

    def test_links_e_catalogo(self):
        it = {"id": "77", "nota": 9.0, "motivo": "m", "urls": ["a", "b", "c"], "conhecido": "NADA aqui", "ceu": (1.5, -2.5)}
        h = relatorio({"byw": (PROJETOS["byw"], [it])})
        self.assertIn("classify/workflow/24299/subject/77", h)
        self.assertIn("talk/subjects/77", h)
        self.assertIn("RA 1.5 Dec -2.5", h)
        self.assertEqual(h.count("<img"), 2)  # primeira e última época

    def test_catalogo_sem_posicao_nao_quebra(self):
        it = {"id": "1", "nota": 1.0, "motivo": "", "urls": [], "conhecido": "x"}
        self.assertIn("<b>x</b>", relatorio({"byw": (PROJETOS["byw"], [it])}))


if __name__ == "__main__":
    unittest.main()
