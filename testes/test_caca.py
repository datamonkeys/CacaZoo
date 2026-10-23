"""Testes offline do CacaZoo (imagens sintéticas, APIs simuladas).
python3 -m unittest discover -s testes -p "test_*.py" """
import json, os, sys, tempfile, unittest
from unittest import mock

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca
import diaria


def salvar(d, nome, arr):
    p = os.path.join(d, nome)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(p)
    return p


def mancha(h, w, x, y, amp, sig):
    yy, xx = np.mgrid[:h, :w]
    return amp * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sig ** 2))


class TesteBYW(unittest.TestCase):
    def quadros(self, d, mover=True):
        rng = np.random.default_rng(0)
        h = w = 400
        fixa = mancha(h, w, 100, 300, 120, 10)  # estrela parada
        out = []
        for k in range(12):
            x = 150 + 6 * k if mover else 150
            escuro = fixa + mancha(h, w, x, 200, 120, 10) + rng.normal(0, 2, (h, w))
            out.append(salvar(d, f"q{k}.png", np.repeat((255 - escuro)[..., None], 3, 2)))
        return out

    def test_acha_o_mover_e_a_posicao(self):
        with tempfile.TemporaryDirectory() as d:
            nota, motivo, extra = caca.nota_byw(self.quadros(d))
        self.assertGreater(nota, 20)
        x, y = extra["pos"]
        self.assertLess(abs(y - 200), 15)
        self.assertGreater(x, 190)  # aponta para o fim do trajeto
        self.assertEqual(extra["lado"], [400, 400])

    def test_campo_parado_tem_nota_baixa(self):
        with tempfile.TemporaryDirectory() as d:
            nota, _, _ = caca.nota_byw(self.quadros(d, mover=False))
        self.assertLess(nota, 5)


class TesteAA(unittest.TestCase):
    def quadros(self, d, cauda):
        rng = np.random.default_rng(1)
        h = w = 160
        out = []
        for k in range(5):
            luz = mancha(h, w, 80, 80, 150, 3) + rng.normal(0, 3, (h, w))
            if cauda:
                for i in range(1, 25):  # cauda para a direita, perdendo brilho
                    luz += mancha(h, w, 80 + i, 80, 60 * np.exp(-i / 10), 2 + 0.1 * i)
            out.append(salvar(d, f"a{k}.png", np.repeat((200 - luz)[..., None], 3, 2)))
        return out

    def test_cauda_tem_nota_maior(self):
        with tempfile.TemporaryDirectory() as d:
            com = caca.nota_aa(self.quadros(d, True))[0]
        with tempfile.TemporaryDirectory() as d:
            sem = caca.nota_aa(self.quadros(d, False))[0]
        self.assertGreater(com, sem + 1)


class TesteKN(unittest.TestCase):
    def test_fonte_nos_paineis(self):
        with tempfile.TemporaryDirectory() as d:
            rng = np.random.default_rng(2)
            img = 100 + rng.normal(0, 3, (432, 900))
            for xc in (152, 748):  # centro dos painéis de ciência e diferença
                img += mancha(432, 900, xc, 189, 120, 2)
            p = salvar(d, "kn.png", img)
            vazio = salvar(d, "kn0.png", 100 + rng.normal(0, 3, (432, 900)))
            self.assertGreater(caca.nota_kn([p], {})[0], caca.nota_kn([vazio], {})[0] + 3)


class TesteCeu(unittest.TestCase):
    META = {"RA": "150.0", "DEC": "0.0", "FOV": "118.25 x 101.75 arcseconds"}

    def test_centro_e_o_alvo(self):
        ra, dec = caca.ceu_byw(self.META, 473, 410, 946, 820)
        self.assertAlmostEqual(ra, 150.0, places=6)
        self.assertAlmostEqual(dec, 0.0, places=6)

    def test_leste_a_esquerda_norte_em_cima(self):
        ra, dec = caca.ceu_byw(self.META, 0, 0, 946, 820)
        self.assertAlmostEqual((ra - 150.0) * 3600, 118.25 / 2, places=3)
        self.assertAlmostEqual(dec * 3600, 101.75 / 2, places=3)

    def test_checagem_usa_posicao_guardada(self):
        it = {"nota": 9.0, "motivo": "texto qualquer", "meta": self.META, "pos": [473, 410], "lado": [946, 820]}
        with mock.patch.object(caca, "catwise_movendo", return_value=[]) as cw, \
             mock.patch.object(caca, "gaia_movendo", return_value=[("Gaia DR3 1", 0.3)]), \
             mock.patch.object(caca.time, "sleep"):
            caca.checar_conhecidos([it])
        ra, dec = cw.call_args[0]
        self.assertAlmostEqual(ra, 150.0, places=6)
        self.assertTrue(it["conhecido"].startswith("já catalogado: Gaia DR3 1"))

    def test_catalogo_fora_do_ar(self):
        it = {"nota": 9.0, "motivo": "", "meta": self.META, "pos": [10, 10]}
        with mock.patch.object(caca, "catwise_movendo", return_value=None), \
             mock.patch.object(caca, "gaia_movendo", return_value=None), \
             mock.patch.object(caca.time, "sleep"):
            caca.checar_conhecidos([it])
        self.assertEqual(it["conhecido"], "catálogo não respondeu")


    def test_um_catalogo_fora_do_ar_nao_vira_descoberta(self):
        for cw, ga in ((None, []), ([], None)):
            it = {"nota": 9.0, "motivo": "", "meta": self.META, "pos": [10, 10]}
            with mock.patch.object(caca, "catwise_movendo", return_value=cw), \
                 mock.patch.object(caca, "gaia_movendo", return_value=ga), \
                 mock.patch.object(caca.time, "sleep"):
                caca.checar_conhecidos([it])
            self.assertEqual(it["conhecido"], "catálogo não respondeu")

    def test_um_catalogo_fora_mas_outro_acha_mover(self):
        it = {"nota": 9.0, "motivo": "", "meta": self.META, "pos": [10, 10]}
        with mock.patch.object(caca, "catwise_movendo", return_value=None), \
             mock.patch.object(caca, "gaia_movendo", return_value=[("Gaia DR3 7", 0.2)]), \
             mock.patch.object(caca.time, "sleep"):
            caca.checar_conhecidos([it])
        self.assertTrue(it["conhecido"].startswith("já catalogado"))

    def test_os_dois_vazios_e_possivel_descoberta(self):
        it = {"nota": 9.0, "motivo": "", "meta": self.META, "pos": [10, 10]}
        with mock.patch.object(caca, "catwise_movendo", return_value=[]), \
             mock.patch.object(caca, "gaia_movendo", return_value=[]), \
             mock.patch.object(caca.time, "sleep"):
            caca.checar_conhecidos([it])
        self.assertTrue(it["conhecido"].startswith("NADA"))


class TesteArquivos(unittest.TestCase):
    def test_gravar_atomico_e_ler_corrompido(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            caca.gravar_json(p, {"a": 1})
            self.assertEqual(caca.ler_json(p, None), {"a": 1})
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".tmp")], [])
            with open(p, "w") as f:
                f.write("{quebr")
            self.assertEqual(caca.ler_json(p, "padrão"), "padrão")

    def test_relatorio_escapa(self):
        proj = caca.PROJETOS["kn"]
        it = {"id": "1", "nota": 1.0, "motivo": "<b>x</b>", "urls": ['https://x/a.png?b=1&c="2"']}
        h = caca.relatorio({"kn": (proj, [it])})
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", h)
        self.assertIn("&amp;c=&quot;2&quot;", h)

    def test_reusar_reavalia_o_que_foi_salvo(self):
        salvo = {"aa": [{"id": "9", "meta": {}, "urls": ["https://x/1.png"], "nota": 0, "motivo": ""}]}
        novo = {"id": "9", "urls": ["https://x/1.png"], "nota": 3.5, "motivo": "reavaliado", "meta": {}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(caca, "AQUI", d), \
             mock.patch.object(caca, "_seguro", return_value=novo) as seg, \
             mock.patch.object(sys, "argv", ["caca.py", "--reusar", "--projeto", "aa"]):
            caca.gravar_json(os.path.join(d, "resultados.json"), salvo)
            caca.main()
            r = caca.ler_json(os.path.join(d, "resultados.json"), {})
        self.assertEqual(seg.call_args[0][1]["locations"], [{"image/png": "https://x/1.png"}])
        self.assertEqual(r["aa"][0]["nota"], 3.5)

    def test_reusar_sem_projeto_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(caca, "AQUI", d), \
             mock.patch.object(sys, "argv", ["caca.py", "--reusar", "--projeto", "aa"]):
            caca.gravar_json(os.path.join(d, "resultados.json"), {"kn": []})
            caca.main()
            self.assertIn("kn", caca.ler_json(os.path.join(d, "resultados.json"), {}))


class TesteDiaria(unittest.TestCase):
    def test_avisa_uma_vez_e_so_acima_do_corte(self):
        itens = {"byw": [
            {"id": "1", "nota": 12.0, "conhecido": "NADA no CatWISE/Gaia se movendo aqui"},
            {"id": "2", "nota": 6.5, "conhecido": "NADA no CatWISE/Gaia se movendo aqui"},
            {"id": "3", "nota": 30.0, "conhecido": "já catalogado: X"}]}
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(diaria, "AQUI", d), mock.patch.object(diaria, "VISTOS", os.path.join(d, "v.json")), \
             mock.patch.object(diaria, "LOG", os.path.join(d, "l.log")), mock.patch.object(diaria, "rodar", return_value=True), \
             mock.patch.object(diaria, "limpar_cache"), mock.patch.object(diaria, "avisar") as av:
            caca.gravar_json(os.path.join(d, "resultados.json"), itens)
            diaria.main()
            diaria.main()
        self.assertEqual(av.call_count, 1)
        self.assertIn("#1", av.call_args[0][1])

    def test_falha_do_aa_kn_avisa(self):
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(diaria, "AQUI", d), mock.patch.object(diaria, "VISTOS", os.path.join(d, "v.json")), \
             mock.patch.object(diaria, "LOG", os.path.join(d, "l.log")), \
             mock.patch.object(diaria, "rodar", side_effect=[True, False]), \
             mock.patch.object(diaria, "limpar_cache"), mock.patch.object(diaria, "avisar") as av:
            diaria.main()
        self.assertIn("falhou", av.call_args_list[0][0][1])


if __name__ == "__main__":
    unittest.main()
