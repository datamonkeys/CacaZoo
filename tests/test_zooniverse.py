import unittest
from unittest import mock

from caca_zoo import zooniverse


class TesteFila(unittest.TestCase):
    def test_sem_repetir_e_sem_treino(self):
        pagina = {"subjects": [{"id": "1"}, {"id": "1"}, {"id": "2", "metadata": {"#training_subject": True}}, {"id": "3"}]}
        with mock.patch.object(zooniverse, "get_json", return_value=pagina), mock.patch.object(zooniverse.time, "sleep"):
            self.assertEqual([s["id"] for s in zooniverse.fila(1, 2)], ["1", "3"])

    def test_objeto_quebrado_vira_none(self):
        with mock.patch.object(zooniverse, "avaliar", side_effect=ValueError("x")):
            self.assertIsNone(zooniverse._seguro("aa", {"id": "9"}))


if __name__ == "__main__":
    unittest.main()
