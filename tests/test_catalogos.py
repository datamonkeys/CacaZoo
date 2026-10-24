import unittest
from unittest import mock

from caca_zoo import catalogos

META = {"RA": "150.0", "DEC": "0.0", "FOV": "118.25 x 101.75 arcseconds"}


def checar(cw, ga, **it):
    item = {"nota": 9.0, "motivo": "", "meta": META, "pos": [10, 10], **it}
    with (
        mock.patch.object(catalogos, "catwise_movendo", return_value=cw) as m_cw,
        mock.patch.object(catalogos, "gaia_movendo", return_value=ga),
        mock.patch.object(catalogos.time, "sleep"),
    ):
        catalogos.checar_conhecidos([item])
    return item, m_cw


class TesteCeu(unittest.TestCase):
    def test_centro_e_o_alvo(self):
        ra, dec = catalogos.ceu_byw(META, 473, 410, 946, 820)
        self.assertAlmostEqual(ra, 150.0, places=6)
        self.assertAlmostEqual(dec, 0.0, places=6)

    def test_leste_a_esquerda_norte_em_cima(self):
        ra, dec = catalogos.ceu_byw(META, 0, 0, 946, 820)
        self.assertAlmostEqual((ra - 150.0) * 3600, 118.25 / 2, places=3)
        self.assertAlmostEqual(dec * 3600, 101.75 / 2, places=3)

    def test_fov_quadrado(self):
        ra, dec = catalogos.ceu_byw({"RA": "10", "DEC": "0", "FOV": "100"}, 0, 0, 100, 100)
        self.assertAlmostEqual(dec * 3600, 50, places=3)


class TesteChecagem(unittest.TestCase):
    def test_usa_posicao_guardada(self):
        item, m_cw = checar([], [("Gaia DR3 1", 0.3)], pos=[473, 410], lado=[946, 820])
        self.assertAlmostEqual(m_cw.call_args[0][0], 150.0, places=6)
        self.assertTrue(item["conhecido"].startswith("já catalogado: Gaia DR3 1"))

    def test_os_dois_fora_do_ar(self):
        self.assertEqual(checar(None, None)[0]["conhecido"], "catálogo não respondeu")

    def test_um_catalogo_fora_do_ar_nao_vira_descoberta(self):
        for cw, ga in ((None, []), ([], None)):
            self.assertEqual(checar(cw, ga)[0]["conhecido"], "catálogo não respondeu")

    def test_um_fora_mas_outro_acha_mover(self):
        self.assertTrue(checar(None, [("Gaia DR3 7", 0.2)])[0]["conhecido"].startswith("já catalogado"))

    def test_os_dois_vazios_e_possivel_descoberta(self):
        self.assertTrue(checar([], [])[0]["conhecido"].startswith("NADA"))

    def test_ignora_nota_baixa_e_sem_posicao(self):
        item, m_cw = checar([], [], nota=2.0)
        m_cw.assert_not_called()
        self.assertNotIn("conhecido", item)


class TesteCatalogosParse(unittest.TestCase):
    def test_catwise_filtra_por_significancia(self):
        tsv = (
            "#\nName\tpmRA\tpmDE\te_pmRA\te_pmDE\tW1\tW2\n----\n"
            "J1\t0.5\t0.0\t0.01\t0.01\t15.0\t13.8\nJ2\t0.06\t0.0\t0.05\t0.05\t14\t14\n"
        )
        with mock.patch.object(catalogos, "abrir", return_value=tsv.encode()):
            self.assertEqual(catalogos.catwise_movendo(1, 2), [("J1", 0.5, 1.2)])

    def test_gaia_converte_mas_por_ano(self):
        tsv = "Source\tpmRA\tpmDE\n123\t300\t400\n456\t10\t0\n"
        with mock.patch.object(catalogos, "abrir", return_value=tsv.encode()):
            self.assertEqual(catalogos.gaia_movendo(1, 2), [("Gaia DR3 123", 0.5)])

    def test_fora_do_ar_devolve_none(self):
        with mock.patch.object(catalogos, "abrir", side_effect=OSError()):
            self.assertIsNone(catalogos.catwise_movendo(1, 2))
            self.assertIsNone(catalogos.gaia_movendo(1, 2))


if __name__ == "__main__":
    unittest.main()
