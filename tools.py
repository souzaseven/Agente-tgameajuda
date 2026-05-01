import json
from pathlib import Path
from config import KB_PATH
import os

# Caminho da pasta de conhecimento e perguntas sem resposta
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
PERGUNTAS_NAO_RESPONDIDAS = Path(__file__).parent / "perguntas_sem_resposta.txt"

TOOL_DEFINITIONS = [
    {
        "name": "analisar_ticket",
        "description": (
            "Analisa o histórico de um chamado de suporte. Identifica o problema central, "
            "as ações já tomadas, a próxima ação recomendada e o risco de violação de SLA. "
            "Use quando o agente fornecer dados ou histórico de um ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id_ticket": {
                    "type": "string",
                    "description": "Número ou ID do ticket no Movidesk"
                },
                "titulo": {
                    "type": "string",
                    "description": "Título ou assunto do chamado"
                },
                "prioridade": {
                    "type": "string",
                    "enum": ["P1", "P2", "P3", "P4"],
                    "description": "Prioridade atual do ticket"
                },
                "historico": {
                    "type": "string",
                    "description": "Histórico completo de interações, atualizações e ações do chamado"
                },
                "tempo_aberto_horas": {
                    "type": "number",
                    "description": "Há quantas horas o ticket está aberto"
                }
            },
            "required": ["historico"]
        }
    },
    {
        "name": "redigir_resposta",
        "description": (
            "Redige ou revisa comunicações: respostas a clientes, e-mails, comunicados internos, "
            "atas de reunião, notificações de SLA. Adapta o tom conforme o contexto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["resposta_cliente", "email_interno", "comunicado", "ata", "notificacao_sla", "outro"],
                    "description": "Tipo de comunicação a ser redigida"
                },
                "tom": {
                    "type": "string",
                    "enum": ["formal", "amigavel", "tecnico", "urgente"],
                    "description": "Tom desejado para a comunicação"
                },
                "contexto": {
                    "type": "string",
                    "description": "Contexto, informações relevantes e o que precisa ser comunicado"
                },
                "destinatario": {
                    "type": "string",
                    "description": "Para quem é a comunicação (ex: cliente, equipe de infra, gestor)"
                },
                "instrucoes_adicionais": {
                    "type": "string",
                    "description": "Instruções específicas, pontos obrigatórios ou restrições para o texto"
                }
            },
            "required": ["tipo", "contexto"]
        }
    },
    {
        "name": "priorizar_fila",
        "description": (
            "Analisa uma lista de tickets e retorna a ordem de atendimento recomendada, "
            "considerando urgência, impacto, risco de SLA e criticidade do negócio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tickets": {
                    "type": "array",
                    "description": "Lista de tickets para priorizar",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "titulo": {"type": "string"},
                            "prioridade": {"type": "string"},
                            "tempo_aberto_horas": {"type": "number"},
                            "descricao": {"type": "string"}
                        },
                        "required": ["id", "titulo"]
                    }
                },
                "contexto_adicional": {
                    "type": "string",
                    "description": "Informações extras relevantes para a priorização (ex: incidente em curso, recursos limitados)"
                }
            },
            "required": ["tickets"]
        }
    },
    {
        "name": "analisar_metricas",
        "description": (
            "Interpreta indicadores de atendimento (TMA, TME, CSAT, FCR, volume de tickets). "
            "Identifica gargalos, tendências e sugere ações de melhoria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "periodo": {
                    "type": "string",
                    "description": "Período de referência das métricas (ex: 'semana passada', 'abril/2025', 'Q1 2025')"
                },
                "metricas": {
                    "type": "object",
                    "description": "Dicionário com os indicadores e seus valores",
                    "properties": {
                        "tma_horas": {"type": "number", "description": "Tempo Médio de Atendimento em horas"},
                        "tme_horas": {"type": "number", "description": "Tempo Médio de Espera em horas"},
                        "csat": {"type": "number", "description": "Customer Satisfaction Score (0-10 ou 0-100)"},
                        "fcr_percentual": {"type": "number", "description": "First Call Resolution em percentual"},
                        "volume_total": {"type": "integer", "description": "Total de tickets no período"},
                        "volume_p1": {"type": "integer"},
                        "volume_p2": {"type": "integer"},
                        "volume_p3": {"type": "integer"},
                        "volume_p4": {"type": "integer"},
                        "sla_cumprido_percentual": {"type": "number", "description": "Percentual de tickets dentro do SLA"}
                    }
                },
                "contexto": {
                    "type": "string",
                    "description": "Contexto adicional sobre o período (ex: mudanças de sistema, férias da equipe, incidentes)"
                }
            },
            "required": ["metricas"]
        }
    },
    {
        "name": "buscar_base_conhecimento",
        "description": (
            "Busca na base de conhecimento interna por procedures, FAQs e soluções conhecidas. "
            "Use antes de tentar resolver qualquer problema técnico ou de processo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Termo, problema ou assunto a buscar na base de conhecimento"
                },
                "categoria": {
                    "type": "string",
                    "enum": ["Acesso", "ERP", "Atendimento", "Infraestrutura", "Movidesk", "SLA", "Métricas", "Financeiro", "Segurança"],
                    "description": "Categoria para filtrar a busca (opcional)"
                }
            },
            "required": ["consulta"]
        }
    }
]


def execute_tool(name: str, tool_input: dict) -> str:
    handlers = {
        "analisar_ticket": _analisar_ticket,
        "redigir_resposta": _redigir_resposta,
        "priorizar_fila": _priorizar_fila,
        "analisar_metricas": _analisar_metricas,
        "buscar_base_conhecimento": _buscar_base_conhecimento,
    }
    handler = handlers.get(name)
    if not handler:
        return json.dumps({"erro": f"Ferramenta '{name}' não encontrada."})
    try:
        return handler(tool_input)
    except Exception as e:
        return json.dumps({"erro": f"Falha ao executar '{name}': {str(e)}"})


def _analisar_ticket(params: dict) -> str:
    sla_map = {"P1": 4, "P2": 8, "P3": 24, "P4": 48}
    prioridade = params.get("prioridade", "P3")
    tempo = params.get("tempo_aberto_horas", 0)
    sla_limite = sla_map.get(prioridade, 24)
    percentual_sla = round((tempo / sla_limite) * 100, 1) if sla_limite else 0

    resultado = {
        "id_ticket": params.get("id_ticket", "N/A"),
        "titulo": params.get("titulo", "N/A"),
        "prioridade": prioridade,
        "tempo_aberto_horas": tempo,
        "sla_limite_horas": sla_limite,
        "percentual_sla_consumido": percentual_sla,
        "historico": params.get("historico", ""),
        "instrucao": (
            "Com base nesses dados, analise o histórico e forneça: "
            "1) Diagnóstico do problema central, "
            "2) Resumo das ações já realizadas, "
            "3) Próxima ação recomendada, "
            "4) Avaliação do risco de SLA (o ticket consumiu "
            f"{percentual_sla}% do tempo limite para {prioridade}). "
            "Seja direto e prático."
        )
    }
    return json.dumps(resultado, ensure_ascii=False)


def _buscar_base_conhecimento(params: dict) -> str:
    consulta = params.get("consulta", "").lower()
    categoria_filtro = params.get("categoria", "").strip()
    termos = [t for t in consulta.split() if len(t) > 2]
    resultados = []

    # Busca nos arquivos .txt da pasta knowledge
    if KNOWLEDGE_DIR.exists():
        for arquivo in KNOWLEDGE_DIR.glob("*.txt"):
            with open(arquivo, encoding="utf-8") as f:
                conteudo = f.read()
            texto = conteudo.lower()
            score = sum(1 for t in termos if t in texto)
            if score > 0:
                urls = [linha for linha in conteudo.splitlines() if linha.strip().startswith("http")]
                resultados.append({
                    "arquivo": arquivo.name,
                    "trecho": conteudo[:300] + ("..." if len(conteudo) > 300 else ""),
                    "urls": urls,
                    "relevancia": score
                })

    # Se não encontrou nada, registra a consulta para o admin
    if not resultados:
        try:
            with open(PERGUNTAS_NAO_RESPONDIDAS, "a", encoding="utf-8") as f:
                f.write(consulta + "\n")
        except Exception:
            pass

    resultados.sort(key=lambda x: x["relevancia"], reverse=True)
    top_resultados = resultados[:5]

    saida = {
        "consulta": params.get("consulta"),
        "categoria_filtro": categoria_filtro or "todas",
        "total_encontrado": len(resultados),
        "resultados": top_resultados,
        "instrucao": (
            "Use esses resultados da base de conhecimento para embasar sua resposta. "
            "Se encontrou arquivos relevantes, apresente o trecho e as URLs. "
            "Se nenhum resultado relevante, informe claramente e sugira onde buscar."
        )
    }
    return json.dumps(saida, ensure_ascii=False)
        "contexto": params.get("contexto", ""),
        "instrucao": (
            "Interprete essas métricas de atendimento. Identifique: "
            "1) Pontos positivos, "
            "2) Gargalos ou indicadores preocupantes (os alertas já foram calculados), "
            "3) Possíveis causas dos desvios, "
            "4) Ações concretas de melhoria. "
            "Use os benchmarks como referência. Seja analítico e propositivo."
        )
    }
    return json.dumps(resultado, ensure_ascii=False)


def _buscar_base_conhecimento(params: dict) -> str:
    consulta = params.get("consulta", "").lower()
    categoria_filtro = params.get("categoria", "").strip()

    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except FileNotFoundError:
        return json.dumps({"erro": "Base de conhecimento não encontrada.", "resultados": []})

    termos = [t for t in consulta.split() if len(t) > 2]
    resultados = []

    for proc in kb.get("procedures", []):
        if categoria_filtro and proc.get("categoria", "") != categoria_filtro:
            continue
        texto = (proc.get("titulo", "") + " " + proc.get("categoria", "") + " " +
                 " ".join(proc.get("passos", []))).lower()
        score = sum(1 for t in termos if t in texto)
        if score > 0:
            resultados.append({
                "tipo": "procedure",
                "id": proc.get("id"),
                "titulo": proc.get("titulo"),
                "categoria": proc.get("categoria"),
                "passos": proc.get("passos"),
                "relevancia": score
            })

    for faq in kb.get("faqs", []):
        if categoria_filtro and faq.get("categoria", "") != categoria_filtro:
            continue
        texto = (faq.get("pergunta", "") + " " + faq.get("resposta", "") +
                 " " + faq.get("categoria", "")).lower()
        score = sum(1 for t in termos if t in texto)
        if score > 0:
            resultados.append({
                "tipo": "faq",
                "pergunta": faq.get("pergunta"),
                "resposta": faq.get("resposta"),
                "categoria": faq.get("categoria"),
                "relevancia": score
            })

    resultados.sort(key=lambda x: x["relevancia"], reverse=True)
    top_resultados = resultados[:5]

    saida = {
        "consulta": params.get("consulta"),
        "categoria_filtro": categoria_filtro or "todas",
        "total_encontrado": len(resultados),
        "resultados": top_resultados,
        "instrucao": (
            "Use esses resultados da base de conhecimento para embasar sua resposta. "
            "Se encontrou procedures relevantes, apresente os passos de forma clara. "
            "Se encontrou FAQs, adapte a resposta ao contexto do agente. "
            "Se nenhum resultado relevante, informe claramente e sugira onde buscar."
            if top_resultados else
            "Nenhum resultado encontrado na base de conhecimento para essa consulta. "
            "Informe ao agente que não há procedure ou FAQ cadastrada para esse tema "
            "e sugira escalar para o especialista adequado."
        )
    }
    return json.dumps(saida, ensure_ascii=False)
