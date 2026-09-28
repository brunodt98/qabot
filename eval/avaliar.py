# -*- coding: utf-8 -*-
"""
Avalia o QABot contra arquivos com defeitos plantados.

Roda a mesma analise que a interface usa (core.analyzer.analisar_conteudo)
sobre cada arquivo de eval/casos/ e compara o resultado com eval/gabarito.json.

Mede quatro coisas:

  1. Deteccao      — o defeito plantado foi encontrado?
  2. Faixa de score — o score caiu na faixa que o prompt manda?
  3. Dificuldade    — a classificacao bateu com a esperada?
  4. Falso positivo — no arquivo limpo, apontou problema grave que nao existe?

IMPORTANTE: o modelo nao e' deterministico. Duas execucoes sobre os mesmos
arquivos podem dar numeros diferentes. O resultado e' uma fotografia de UMA
execucao, com o modelo e a data registrados no JSON de saida — nao e' uma
garantia de desempenho.

Uso:
    python eval/avaliar.py --api-key SUA_CHAVE_GROQ
    python eval/avaliar.py --api-key SUA_CHAVE_GROQ --model llama3-70b-8192
    python eval/avaliar.py --backend Ollama --model llama3
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.ai_client import build_groq_client  # noqa: E402
from core.analyzer import analisar_conteudo  # noqa: E402
from core.file_scanner import get_language_from_ext  # noqa: E402

DIR_CASOS = Path(__file__).parent / "casos"
GABARITO = Path(__file__).parent / "gabarito.json"
SAIDA = Path(__file__).parent / "resultado_avaliacao.json"

ORDEM_SEVERIDADE = ["baixo", "médio", "alto", "crítico"]


def carregar_gabarito() -> dict:
    return json.loads(GABARITO.read_text(encoding="utf-8"))


def texto_dos_problemas(problemas: list[dict]) -> str:
    """Junta titulo e descricao de todos os problemas, em minusculas."""
    partes = []
    for p in problemas:
        partes.append(p.get("titulo", ""))
        partes.append(p.get("descricao", ""))
    return " ".join(partes).lower()


def defeito_foi_detectado(defeito: dict, problemas: list[dict]) -> bool:
    """Considera detectado se qualquer palavra-chave aparece no relatorio."""
    alvo = texto_dos_problemas(problemas)
    return any(palavra.lower() in alvo for palavra in defeito["palavras_chave"])


def severidade_maxima(problemas: list[dict]) -> str | None:
    """Devolve a severidade mais grave reportada, ou None se nao houver."""
    encontradas = [
        p.get("severidade", "baixo").lower()
        for p in problemas
        if p.get("severidade", "baixo").lower() in ORDEM_SEVERIDADE
    ]
    if not encontradas:
        return None
    return max(encontradas, key=ORDEM_SEVERIDADE.index)


def avaliar_caso(caso: dict, ai_cfg: dict) -> dict:
    """Analisa um arquivo e compara o resultado com o que era esperado."""
    caminho = DIR_CASOS / caso["arquivo"]
    conteudo = caminho.read_text(encoding="utf-8")
    linguagem = get_language_from_ext(caminho.suffix)

    res = analisar_conteudo(ai_cfg, caminho.name, linguagem, conteudo)

    if not res.ok:
        return {
            "id": caso["id"],
            "arquivo": caso["arquivo"],
            "erro": res.erro,
            "segundos": round(res.segundos, 2),
            "tokens": res.tokens_total,
        }

    dados = res.dados
    problemas = dados["problemas"]
    score = dados["score_qualidade"]
    dificuldade = dados["classificacao_dificuldade"]

    minimo, maximo = caso["faixa_score"]

    deteccoes = [
        {
            "defeito": d["nome"],
            "detectado": defeito_foi_detectado(d, problemas),
        }
        for d in caso["defeitos_plantados"]
    ]

    grave = severidade_maxima(problemas)

    # No arquivo sem defeito plantado, qualquer apontamento critico ou alto
    # e' falso positivo: nao ha o que encontrar ali.
    falso_positivo = (
        not caso["defeitos_plantados"]
        and grave in ("crítico", "alto")
    )

    return {
        "id": caso["id"],
        "arquivo": caso["arquivo"],
        "score_obtido": score,
        "faixa_esperada": caso["faixa_score"],
        "score_na_faixa": minimo <= score <= maximo,
        "dificuldade_obtida": dificuldade,
        "dificuldade_esperada": caso["dificuldade_esperada"],
        "dificuldade_correta": dificuldade == caso["dificuldade_esperada"],
        "deteccoes": deteccoes,
        "problemas_reportados": len(problemas),
        "severidade_maxima": grave,
        "falso_positivo": falso_positivo,
        "tentativas": res.tentativas,
        "segundos": round(res.segundos, 2),
        "tokens": res.tokens_total,
    }


def imprimir_tabela(resultados: list[dict]) -> None:
    print()
    print(f"{'ID':<5}{'ARQUIVO':<30}{'SCORE':<14}{'DIFICULDADE':<22}{'DEFEITOS':<12}")
    print("-" * 90)

    for r in resultados:
        if "erro" in r:
            print(f"{r['id']:<5}{r['arquivo']:<30}{'ERRO':<14}{r['erro'][:40]}")
            continue

        faixa = f"{r['score_obtido']:>3} {'ok' if r['score_na_faixa'] else 'fora'}"
        dif = f"{r['dificuldade_obtida']:<8} {'ok' if r['dificuldade_correta'] else '!= ' + r['dificuldade_esperada']}"

        total = len(r["deteccoes"])
        achados = sum(1 for d in r["deteccoes"] if d["detectado"])
        defeitos = f"{achados}/{total}" if total else ("FP!" if r["falso_positivo"] else "limpo ok")

        print(f"{r['id']:<5}{r['arquivo']:<30}{faixa:<14}{dif:<22}{defeitos:<12}")


def resumir(resultados: list[dict]) -> dict:
    validos = [r for r in resultados if "erro" not in r]

    if not validos:
        return {"erro": "Nenhum caso pode ser avaliado."}

    defeitos_total = sum(len(r["deteccoes"]) for r in validos)
    defeitos_achados = sum(
        1 for r in validos for d in r["deteccoes"] if d["detectado"]
    )

    com_defeito = [r for r in validos if r["deteccoes"]]
    sem_defeito = [r for r in validos if not r["deteccoes"]]

    return {
        "casos_avaliados": len(validos),
        "casos_com_erro": len(resultados) - len(validos),
        "defeitos_plantados": defeitos_total,
        "defeitos_detectados": defeitos_achados,
        "taxa_deteccao": round(defeitos_achados / defeitos_total, 3) if defeitos_total else None,
        "score_na_faixa": sum(1 for r in validos if r["score_na_faixa"]),
        "dificuldade_correta": sum(1 for r in validos if r["dificuldade_correta"]),
        "falsos_positivos": sum(1 for r in sem_defeito if r["falso_positivo"]),
        "arquivos_limpos_avaliados": len(sem_defeito),
        "arquivos_com_defeito_avaliados": len(com_defeito),
        "segundos_total": round(sum(r["segundos"] for r in validos), 1),
        "tokens_total": sum(r["tokens"] for r in validos),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o QABot contra defeitos plantados.")
    parser.add_argument("--backend", default="Groq", choices=["Groq", "Ollama"])
    parser.add_argument("--api-key", default=None, help="Chave da Groq (obrigatoria para o backend Groq)")
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args()

    if args.backend == "Groq" and not args.api_key:
        print("ERRO: informe --api-key para usar o backend Groq.")
        sys.exit(1)

    ai_cfg = {
        "backend": args.backend,
        "client": build_groq_client(args.api_key) if args.backend == "Groq" else None,
        "model": args.model,
        "ollama_url": args.ollama_url,
    }

    gabarito = carregar_gabarito()
    casos = gabarito["casos"]

    print(f"Avaliando {len(casos)} casos com {args.backend} / {args.model}...")

    resultados = [avaliar_caso(caso, ai_cfg) for caso in casos]

    imprimir_tabela(resultados)

    resumo = resumir(resultados)

    print()
    print("=" * 90)
    for chave, valor in resumo.items():
        print(f"{chave.replace('_', ' ').capitalize():<34}{valor}")
    print("=" * 90)
    print()
    print("O modelo nao e' deterministico: estes numeros valem para esta execucao.")

    SAIDA.write_text(
        json.dumps(
            {
                "executado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "backend": args.backend,
                "modelo": args.model,
                "resumo": resumo,
                "resultados": resultados,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Resultado completo salvo em: {SAIDA}")


if __name__ == "__main__":
    main()
