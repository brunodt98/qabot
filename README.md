# 🛡️ QABot — Assistente de Qualidade de Software com IA

> Projeto Integrador — FATEC Cotia · Ciência de Dados  
> Empresa parceira: **Outtech Services IT**  
> Baseado no **Framework de QA com Inteligência Artificial**

---

## 📋 Sobre o Projeto

O **QABot** é uma ferramenta de análise estática de código com IA que:

- 🔍 **Escaneia pastas de projetos** locais automaticamente
- 🐛 **Identifica erros** com localização exata no código (linha, trecho)
- 📊 **Classifica dificuldade** do código (Fácil / Médio / Difícil)
- 💯 **Atribui score de qualidade** (0–100)
- 💡 **Sugere correções específicas** com exemplos de código
- 🔒 **Detecta vulnerabilidades** de segurança
- 💬 **Chat interativo** sobre QA, boas práticas e testes

Suporta dois backends de IA **100% gratuitos**:
- **Groq** (online) — LLaMA 3, Mixtral
- **Ollama** (offline/local) — LLaMA 3, Mistral e outros

---

## 🗂️ Estrutura do Projeto

```
qabot/
├── app.py                  # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── .gitignore
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── ai_client.py        # Integração com Groq e Ollama
│   ├── analyzer.py         # Lógica de análise e prompts
│   └── file_scanner.py     # Varredura de arquivos e pastas
│
├── ui/
│   ├── __init__.py
│   ├── sidebar.py          # Configurações na barra lateral
│   ├── tab_project.py      # Aba: Analisar Projeto
│   ├── tab_code.py         # Aba: Analisar Código
│   └── tab_chat.py         # Aba: Chat QA
│
└── utils/
    ├── __init__.py
    └── helpers.py          # Funções utilitárias e renderização
```

---

## 🚀 Como Usar

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/qabot.git
cd qabot
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute a aplicação
```bash
streamlit run app.py
```

### 4. Configure o backend de IA

**Opção A — Groq (recomendado, gratuito online):**
1. Crie conta em [console.groq.com](https://console.groq.com)
2. Gere uma API Key (sem cartão de crédito)
3. Cole a chave na barra lateral do QABot

**Opção B — Ollama (gratuito, 100% local):**
1. Instale o [Ollama](https://ollama.com)
2. Execute: `ollama pull llama3`
3. Selecione "Ollama" na barra lateral

---

## 🧪 Testando com o KNIME

Para testar o QABot com um projeto real:

```bash
git clone https://github.com/knime/knimepy.git
```

No QABot, informe o caminho da pasta clonada e inicie a análise.

---

## 📚 Referências

- [Framework de QA com IA — Outtech Services IT](https://outtech.com.br)
- [Groq API](https://console.groq.com)
- [Ollama](https://ollama.com)
- [Streamlit Docs](https://docs.streamlit.io)
- [KNIME Python Integration](https://github.com/knime/knimepy)

---

## 👥 Equipe

Desenvolvido por alunos do curso de **Ciência de Dados — FATEC Cotia**  
Orientado pelo professor do Projeto Integrador IV/V
