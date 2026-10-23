"""Dados de entrada dos scripts de validação."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

# conjunto "gen3_feedback_training" do Kilonova Seekers: 51 objetos rotulados pela equipe
SET_TREINO_KN = 134144


def resultados(projeto, minimo=10):
    """Objetos de uma rodada anterior do caca.py (as validações usam imagens reais)."""
    itens = caca.ler_json(os.path.join(caca.AQUI, "resultados.json"), {}).get(projeto, [])
    if len(itens) < minimo:
        sys.exit(f"precisa de uma rodada antes: python3 caca.py --n 40 --projeto {projeto}")
    return itens


def treino_kn():
    """Objetos de treino rotulados do Kilonova Seekers; baixa na primeira vez."""
    caminho = os.path.join(caca.CACHE, "kn_treino.json")
    subs = caca.ler_json(caminho, None)
    if subs is None:
        os.makedirs(caca.CACHE, exist_ok=True)
        subs = caca.get_json(f"{caca.API}/subjects?subject_set_id={SET_TREINO_KN}&page_size=100")["subjects"]
        caca.gravar_json(caminho, subs)
    return subs
