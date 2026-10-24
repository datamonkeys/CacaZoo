import tempfile
import unittest

import numpy as np

from caca_zoo import detectores
from caca_zoo.imagem import ruido
from tests.ajuda import mancha, quadros_aa, quadros_byw, salvar


class TesteBYW(unittest.TestCase):
    def test_acha_o_mover_e_a_posicao(self):
        with tempfile.TemporaryDirectory() as d:
            nota, _, extra = detectores.nota_byw(quadros_byw(d))
        self.assertGreater(nota, 20)
        x, y = extra["pos"]
        self.assertLess(abs(y - 200), 15)
        self.assertGreater(x, 190)  # aponta para o fim do trajeto
        self.assertEqual(extra["lado"], [400, 400])

    def test_cor_laranja_e_azul(self):
        with tempfile.TemporaryDirectory() as d:
            laranja = detectores.nota_byw(quadros_byw(d, cor=(0.3, 0.6, 1.0)))[2]["cor"]
        with tempfile.TemporaryDirectory() as d:
            azul = detectores.nota_byw(quadros_byw(d, cor=(1.0, 0.8, 0.3)))[2]["cor"]
        self.assertGreater(laranja, 0.3)
        self.assertLess(azul, -0.3)

    def test_campo_parado_tem_nota_baixa(self):
        with tempfile.TemporaryDirectory() as d:
            nota, _, _ = detectores.nota_byw(quadros_byw(d, mover=False))
        self.assertLess(nota, 5)


class TesteAA(unittest.TestCase):
    def test_cauda_tem_nota_maior(self):
        with tempfile.TemporaryDirectory() as d:
            com = detectores.nota_aa(quadros_aa(d, True))[0]
        with tempfile.TemporaryDirectory() as d:
            sem = detectores.nota_aa(quadros_aa(d, False))[0]
        self.assertGreater(com, sem + 1)

    def test_quadro_vazio(self):
        with tempfile.TemporaryDirectory() as d:
            vazio = salvar(d, "v.png", np.full((160, 160, 3), 200.0))
            self.assertEqual(detectores.nota_aa([vazio]), (0.0, "alvo não detectado"))


class TesteKN(unittest.TestCase):
    def test_fonte_nos_paineis(self):
        with tempfile.TemporaryDirectory() as d:
            rng = np.random.default_rng(2)
            img = 100 + rng.normal(0, 3, (432, 900))
            for xc in (152, 748):  # centro dos painéis de ciência e diferença
                img += mancha(432, 900, xc, 189, 120, 2)
            p = salvar(d, "kn.png", img)
            vazio = salvar(d, "kn0.png", 100 + rng.normal(0, 3, (432, 900)))
            self.assertGreater(detectores.nota_kn([p], {})[0], detectores.nota_kn([vazio], {})[0] + 3)


class TesteRuido(unittest.TestCase):
    def test_piso_em_fundo_constante(self):
        self.assertEqual(ruido(np.full((10, 10), 7.0)), 1.0)

    def test_ruido_gaussiano(self):
        a = np.random.default_rng(3).normal(0, 10, (200, 200))
        self.assertAlmostEqual(ruido(a), 10, delta=3)


if __name__ == "__main__":
    unittest.main()
