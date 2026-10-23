import os
import tempfile
import unittest
from unittest import mock

from caca_zoo import rede


class TesteArquivos(unittest.TestCase):
    def test_gravar_atomico_e_ler_corrompido(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            rede.gravar_json(p, {"a": 1})
            self.assertEqual(rede.ler_json(p, None), {"a": 1})
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".tmp")], [])
            with open(p, "w") as f:
                f.write("{quebr")
            self.assertEqual(rede.ler_json(p, "padrão"), "padrão")

    def test_baixar_usa_cache(self):
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch.object(rede, "CACHE", d),
            mock.patch.object(rede, "abrir", return_value=b"png") as abrir,
        ):
            p1 = rede.baixar("https://x/y/img.png")
            p2 = rede.baixar("https://x/y/img.png")
            with open(p1, "rb") as f:
                self.assertEqual(f.read(), b"png")
        self.assertEqual(p1, p2)
        abrir.assert_called_once()


class TesteHttp(unittest.TestCase):
    def test_tenta_de_novo_com_espera_crescente(self):
        ok = mock.MagicMock()
        ok.__enter__.return_value.read.return_value = b'{"a": 1}'
        with (
            mock.patch("urllib.request.urlopen", side_effect=[OSError(), OSError(), ok]),
            mock.patch.object(rede.time, "sleep") as dorme,
        ):
            self.assertEqual(rede.get_json("https://x"), {"a": 1})
        self.assertEqual([c.args[0] for c in dorme.call_args_list], [1, 2])

    def test_zero_tentativas_e_erro(self):
        with self.assertRaises(ValueError):
            rede.abrir("https://x", 1, tentativas=0)

    def test_user_agent_identifica_o_projeto(self):
        self.assertIn("github.com/louisperner/CacaZoo", rede.HDR["User-Agent"])


if __name__ == "__main__":
    unittest.main()
