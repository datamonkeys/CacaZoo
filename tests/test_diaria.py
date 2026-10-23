import os
import tempfile
import time
import unittest
from unittest import mock

from caca_zoo import diaria, rede

ITENS = {
    "byw": [
        {"id": "1", "nota": 12.0, "conhecido": "NADA no CatWISE/Gaia se movendo aqui"},
        {"id": "2", "nota": 6.5, "conhecido": "NADA no CatWISE/Gaia se movendo aqui"},
        {"id": "3", "nota": 30.0, "conhecido": "já catalogado: X"},
    ]
}


class TesteDiaria(unittest.TestCase):
    def rodar(self, d, etapas):
        with (
            mock.patch.object(diaria, "PASTA", d),
            mock.patch.object(diaria, "VISTOS", os.path.join(d, "v.json")),
            mock.patch.object(diaria.registro, "configurar"),
            mock.patch.object(diaria, "limpar_cache"),
            mock.patch.object(diaria, "etapa", side_effect=etapas),
            mock.patch.object(diaria, "avisar") as av,
        ):
            codigo = diaria.main([])
        return codigo, av

    def test_avisa_uma_vez_e_so_acima_do_corte(self):
        with tempfile.TemporaryDirectory() as d:
            rede.gravar_json(os.path.join(d, "resultados.json"), ITENS)
            _, av1 = self.rodar(d, [True, True])
            _, av2 = self.rodar(d, [True, True])
        self.assertEqual(av1.call_count, 1)
        self.assertIn("#1", av1.call_args[0][1])
        av2.assert_not_called()

    def test_falha_do_aa_kn_avisa_mas_continua(self):
        with tempfile.TemporaryDirectory() as d:
            codigo, av = self.rodar(d, [True, False])
        self.assertEqual(codigo, 0)
        self.assertIn("falhou", av.call_args_list[0][0][1])

    def test_falha_do_byw_para(self):
        with tempfile.TemporaryDirectory() as d:
            codigo, av = self.rodar(d, [False])
        self.assertEqual(codigo, 1)
        av.assert_called_once()

    def test_limpa_so_imagens_antigas(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(diaria, "CACHE", d):
            velho, novo, outro = (os.path.join(d, n) for n in ("a.png", "b.png", "kn_treino.json"))
            for p in (velho, novo, outro):
                open(p, "w").close()
            antigo = time.time() - 5 * 86400
            os.utime(velho, (antigo, antigo))
            os.utime(outro, (antigo, antigo))
            diaria.limpar_cache(3)
            self.assertEqual(sorted(os.listdir(d)), ["b.png", "kn_treino.json"])

    def test_help_nao_roda_a_varredura(self):
        with mock.patch.object(diaria, "etapa") as etapa, mock.patch("sys.stdout"), self.assertRaises(SystemExit):
            diaria.main(["--help"])
        etapa.assert_not_called()

    def test_fora_do_macos_nao_chama_osascript(self):
        with mock.patch.object(diaria.sys, "platform", "linux"), mock.patch.object(diaria.subprocess, "run") as run:
            diaria.avisar("t", "x")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
