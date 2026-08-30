#!/usr/bin/env python3
"""
Gera data/dados.js a partir dos data/*.json.

RODE ISTO SEMPRE QUE TROCAR QUALQUER ARQUIVO EM data/.

Por que existe: fetch() não funciona com file:// — abrindo o app com
duplo clique, o navegador bloqueia a leitura dos .json. As páginas
carregam window.DADOS por <script src>, e este script mantém os dois
em sincronia.

A armadilha que ele evita: se o ETL substituir os .json e ninguém
regenerar o dados.js, o app segue mostrando o dado antigo sem
apresentar erro nenhum.

    python3 build_dados.py
"""

import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS = ["unidades", "convocacoes", "indicadores", "copy", "ui_copy"]

# Chaves que as telas leem. Se o ETL renomear alguma, o app quebra em
# silêncio — então falhamos aqui, alto, em vez de lá, calado.
OBRIGATORIAS = {
    "convocacoes": ["token", "aluno_anon", "unidade_id", "prazo_em",
                    "estado", "excecao", "aberta_em", "contato"],
    "unidades": ["id", "nome", "cre", "bairro", "microarea"],
}


def carregar(nome):
    caminho = os.path.join(RAIZ, "data", "%s.json" % nome)
    if not os.path.exists(caminho):
        sys.exit("ERRO: falta data/%s.json" % nome)
    with io.open(caminho, encoding="utf-8") as f:
        try:
            return json.load(f)
        except ValueError as e:
            sys.exit("ERRO: data/%s.json não é JSON válido: %s" % (nome, e))


def conferir(nome, valor):
    if nome not in OBRIGATORIAS or not isinstance(valor, list) or not valor:
        return
    faltando = [c for c in OBRIGATORIAS[nome] if c not in valor[0]]
    if faltando:
        sys.exit("ERRO: data/%s.json perdeu as chaves %s.\n"
                 "      As telas dependem delas. Veja 02-projeto/CONTRATO-DADOS.md."
                 % (nome, ", ".join(faltando)))


def main():
    dados = {}
    for nome in ARQUIVOS:
        valor = carregar(nome)
        conferir(nome, valor)
        dados[nome] = valor

    destino = os.path.join(RAIZ, "data", "dados.js")
    with io.open(destino, "w", encoding="utf-8") as out:
        out.write("/* GERADO POR build_dados.py — não edite à mão.\n")
        out.write("   Regerar:  python3 build_dados.py  */\n")
        out.write("window.DADOS = ")
        out.write(json.dumps(dados, ensure_ascii=False, indent=1))
        out.write(";\n")

    print("data/dados.js atualizado")
    for nome in ARQUIVOS:
        v = dados[nome]
        print("  %-14s %s" % (nome, "%d registros" % len(v) if isinstance(v, list) else "objeto"))

    convs = dados.get("convocacoes") or []
    excecoes = sorted({c.get("excecao") for c in convs if c.get("excecao")})
    print("\n  exceções presentes: %s" % (", ".join(excecoes) or "nenhuma"))
    faltantes = {"nao_abriu", "abriu_sem_resposta", "pediu_data", "recusou",
                 "vencendo_hoje", "pronta_para_convocar"} - set(excecoes)
    if faltantes:
        print("  AVISO: sem exemplo de %s — o painel não vai mostrar esse caso."
              % ", ".join(sorted(faltantes)))


if __name__ == "__main__":
    main()
