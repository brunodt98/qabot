"""
QABot — Analyzer
Define os prompts do sistema e a lógica de parsing das respostas da IA.
"""

import json
import re

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Análise de Arquivo
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_ANALYSIS = """
Você é o QABot, um especialista sênior em Garantia de Qualidade de Software (QA).

Sua tarefa é analisar o código fornecido e retornar uma resposta EXCLUSIVAMENTE em JSON válido,
sem nenhum texto antes ou depois do JSON.

O JSON deve seguir EXATAMENTE este schema:
{
  "resumo": "string — diagnóstico geral em 2-3 frases objetivas",
  "score_qualidade": <inteiro 0-100>,
  "classificacao_dificuldade": "Fácil" | "Médio" | "Difícil",
  "justificativa_dificuldade": "string — explique em 1 frase o porquê",
  "problemas": [
    {
      "id": <inteiro sequencial>,
      "tipo": "erro" | "aviso" | "segurança" | "performance" | "estilo",
      "severidade": "crítico" | "alto" | "médio" | "baixo",
      "linha_inicio": <inteiro ou null>,
      "linha_fim": <inteiro ou null>,
      "titulo": "string curta — nome do problema",
      "descricao": "string — o que está errado e por quê é um problema",
      "trecho_original": "string — copie o trecho EXATO do código com o erro (máx 5 linhas)",
      "correcao_sugerida": "string — versão corrigida do mesmo trecho",
      "explicacao_correcao": "string — explique o que mudou e por quê"
    }
  ],
  "pontos_positivos": ["string", "string"],
  "recomendacoes_gerais": ["string", "string"]
}

REGRAS OBRIGATÓRIAS:
- Sempre copie o trecho_original EXATAMENTE como está no código — não invente.
- Se não houver linha definida, use null.
- O score_qualidade deve refletir a gravidade dos problemas encontrados.
- Se não houver problemas, retorne "problemas": [].
- Nunca adicione texto fora do JSON. Apenas o JSON.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Chat QA
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_CHAT = """
Você é o QABot, um especialista em Garantia de Qualidade de Software (QA).
Responda perguntas sobre: testes, boas práticas de código, CI/CD, segurança, 
padrões de projeto, refatoração, cobertura de testes e qualidade de software em geral.
Seja direto, técnico e didático. Use português do Brasil.
Quando mostrar código, use blocos de código com a linguagem correta.
"""


def build_analysis_messages(filename: str, language: str, content: str) -> list[dict]:
    """Monta o payload de mensagens para análise de um arquivo."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYSIS},
        {
            "role": "user",
            "content": (
                f"Analise o arquivo `{filename}` (linguagem: {language}).\n\n"
                f"```{language}\n{content}\n```\n\n"
                f"Retorne apenas o JSON conforme o schema solicitado."
            ),
        },
    ]


def parse_analysis_response(raw: str) -> dict | None:
    """
    Extrai e parseia o JSON da resposta da IA.
    Retorna o dict ou None se falhar.
    """
    # Tenta extrair JSON mesmo que venha com texto ao redor
    try:
        # Tenta direto
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Tenta extrair bloco ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tenta achar o primeiro { ... } no texto
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None


def get_severity_rank(severidade: str) -> int:
    """Retorna rank numérico para ordenar por severidade."""
    return {"crítico": 0, "alto": 1, "médio": 2, "baixo": 3}.get(severidade, 4)
