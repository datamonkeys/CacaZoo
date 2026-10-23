import os
import tempfile
import unittest
from unittest import mock

from caca_zoo import cli, rede


class TesteRodada(unittest.TestCase):
    def test_reusar_sem_projeto_salvo_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d:
            rede.gravar_json(os.path.join(d, "resultados.json"), {"kn": []})
            cli.rodar(40, ["aa"], reusar=True, pasta=d)
            self.assertIn("kn", rede.ler_json(os.path.join(d, "resultados.json"), {}))

    def test_reusar_reavalia_o_que_foi_salvo(self):
        salvo = {"aa": [{"id": "9", "meta": {}, "urls": ["https://x/1.png"], "nota": 0, "motivo": ""}]}
        novo = {"id": "9", "urls": ["https://x/1.png"], "nota": 3.5, "motivo": "reavaliado", "meta": {}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cli, "_seguro", return_value=novo) as seg:
            rede.gravar_json(os.path.join(d, "resultados.json"), salvo)
            cli.rodar(40, ["aa"], reusar=True, pasta=d)
            r = rede.ler_json(os.path.join(d, "resultados.json"), {})
            self.assertTrue(os.path.exists(os.path.join(d, "report.html")))
        self.assertEqual(seg.call_args[0][1]["locations"], [{"image/png": "https://x/1.png"}])
        self.assertEqual(r["aa"][0]["nota"], 3.5)

    def test_byw_passa_pela_checagem_de_catalogo(self):
        it = {"id": "1", "urls": ["a"], "nota": 9.0, "motivo": "", "meta": {}}
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch.object(cli, "fila", return_value=[{"id": "1"}]),
            mock.patch.object(cli, "_seguro", return_value=it),
            mock.patch.object(cli, "checar_conhecidos") as ch,
        ):
            cli.rodar(1, ["byw"], reusar=False, pasta=d)
        ch.assert_called_once()

    def test_argumentos(self):
        with mock.patch.object(cli, "rodar") as r, mock.patch.object(cli.registro, "configurar"), mock.patch("builtins.print"):
            self.assertEqual(cli.main(["--n", "5", "--projeto", "aa", "--projeto", "kn"]), 0)
        r.assert_called_once_with(5, ["aa", "kn"], False)

    def test_launcher_existe(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(raiz, "caca.py")))


if __name__ == "__main__":
    unittest.main()
