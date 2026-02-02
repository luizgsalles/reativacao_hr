#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Reativação de Clientes - VERSÃO FINAL
Consolida automaticamente os arquivos XLS e gera análises completas
"""

import streamlit as st
import pandas as pd
import xlrd
from datetime import datetime
from collections import defaultdict
import re
import io

# Configuração da página
st.set_page_config(
    page_title="Reativação de Clientes",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("👗 Sistema de Reativação de Clientes")
st.markdown("**Consolida dados automaticamente e identifica clientes para reativar**")

# ============================================================================
# FUNÇÕES DE CONSOLIDAÇÃO
# ============================================================================

def processar_vendas_cronologica(file_content):
    """Processa arquivo VENDAS POR ORDEM CRONOLOGICA"""
    book = xlrd.open_workbook(file_contents=file_content)
    sheet = book.sheet_by_index(0)

    vendas = {}
    current_date = None
    vendas_count = 0

    for i in range(9, sheet.nrows):
        row = sheet.row_values(i)

        cell_1 = str(row[1]).strip() if len(row) > 1 else ""
        if "Data da Emiss" in cell_1:
            match = re.search(r'(\d{2}/\d{2}/\d{4})', cell_1)
            if match:
                current_date = datetime.strptime(match.group(1), "%d/%m/%Y")

        cell_1 = row[1] if len(row) > 1 else ""
        cell_4 = row[4] if len(row) > 4 else ""
        cell_11 = row[11] if len(row) > 11 else 0

        if isinstance(cell_1, (int, float)) and cell_1 > 0 and cell_4 and current_date:
            if "cliente não identificado" not in str(cell_4).lower():
                match = re.match(r'(\d+)\s*-\s*(.*)', str(cell_4).strip())
                if match:
                    nota = str(int(cell_1))
                    cliente_id = match.group(1)
                    cliente_nome = match.group(2).strip()

                    vendas[nota] = {
                        'cliente_id': cliente_id,
                        'cliente_nome': cliente_nome,
                        'data': current_date,
                        'valor': float(cell_11) if cell_11 else 0
                    }
                    vendas_count += 1

    return vendas, vendas_count

def processar_produtos_cliente(file_content):
    """Processa arquivo PRODUTOS VENDIDOS POR CLIENTE"""
    book = xlrd.open_workbook(file_contents=file_content)
    sheet = book.sheet_by_index(0)

    clientes_produtos = {}
    clientes_count = 0

    i = 4
    while i < sheet.nrows:
        row = sheet.row_values(i)

        col1 = row[1] if len(row) > 1 else ""
        col3 = row[3] if len(row) > 3 else ""

        if isinstance(col1, str) and " - " in str(col1) and not col3:
            match = re.match(r'(\d+)\s*-\s*(.*)', str(col1).strip())
            if match:
                cliente_id = match.group(1)
                cliente_nome = match.group(2).strip()

                produtos = []
                j = i + 1

                while j < sheet.nrows:
                    prod_row = sheet.row_values(j)
                    prod_col3 = prod_row[3] if len(prod_row) > 3 else ""
                    prod_col9 = prod_row[9] if len(prod_row) > 9 else 0
                    prod_col13 = prod_row[13] if len(prod_row) > 13 else 0

                    if prod_col3 and prod_col9:
                        descricao = str(prod_col3).strip()
                        if descricao.lower() not in ['descricao', '']:
                            produtos.append({
                                'descricao': descricao,
                                'quantidade': int(prod_col9) if prod_col9 else 1,
                                'valor': float(prod_col13) if prod_col13 else 0
                            })
                        j += 1
                    else:
                        break

                if produtos:
                    clientes_produtos[cliente_id] = {
                        'cliente_nome': cliente_nome,
                        'produtos': produtos
                    }
                    clientes_count += 1

                i = j
            else:
                i += 1
        else:
            i += 1

    return clientes_produtos, clientes_count

def consolidar_base(vendas, clientes_produtos):
    """Consolida vendas e produtos"""
    vendas_consolidadas = []

    for nota, venda_info in vendas.items():
        cliente_id = venda_info['cliente_id']

        produtos = []
        if cliente_id in clientes_produtos:
            produtos = clientes_produtos[cliente_id]['produtos']

        vendas_consolidadas.append({
            'data': venda_info['data'],
            'nota': nota,
            'cliente_id': cliente_id,
            'cliente_nome': venda_info['cliente_nome'],
            'produtos': produtos,
            'valor_total': venda_info['valor']
        })

    vendas_consolidadas.sort(key=lambda x: x['data'])
    return vendas_consolidadas

def gerar_ranking(vendas_consolidadas):
    """Gera ranking de clientes para reativação"""
    clientes_resumo = defaultdict(lambda: {
        'cliente_nome': '',
        'ultima_compra': None,
        'total_gasto': 0,
        'num_compras': 0,
        'produtos_comprados': set()
    })

    for venda in vendas_consolidadas:
        cliente_id = venda['cliente_id']

        clientes_resumo[cliente_id]['cliente_nome'] = venda['cliente_nome']

        if venda['data'] > (clientes_resumo[cliente_id]['ultima_compra'] or datetime.min):
            clientes_resumo[cliente_id]['ultima_compra'] = venda['data']

        clientes_resumo[cliente_id]['total_gasto'] += venda['valor_total']
        clientes_resumo[cliente_id]['num_compras'] += 1

        for produto in venda['produtos']:
            clientes_resumo[cliente_id]['produtos_comprados'].add(produto['descricao'])

    # Criar ranking
    data_hoje = datetime.now()
    ranking = []

    for cliente_id, info in clientes_resumo.items():
        dias_sem_comprar = (data_hoje - info['ultima_compra']).days

        ranking.append({
            'Cliente_ID': cliente_id,
            'Cliente_Nome': info['cliente_nome'],
            'Dias_Parado': dias_sem_comprar,
            'Ultima_Compra': info['ultima_compra'],
            'Total_Gasto_LTV': info['total_gasto'],
            'Num_Compras': info['num_compras'],
            'Produtos': list(info['produtos_comprados'])
        })

    ranking.sort(key=lambda x: (-x['Dias_Parado'], -x['Total_Gasto_LTV']))

    return pd.DataFrame(ranking)

# ============================================================================
# SIDEBAR - UPLOAD
# ============================================================================

st.divider()

with st.sidebar:
    st.header("📤 Upload de Arquivos")

    uploaded_files = st.file_uploader(
        "Selecione os arquivos XLS do ERP:",
        type=['xls', 'xlsx'],
        accept_multiple_files=True,
        help="Selecione: VENDAS POR ORDEM CRONOLOGICA e PRODUTOS VENDIDOS POR CLIENTE"
    )

    if uploaded_files:
        st.info(f"✓ {len(uploaded_files)} arquivo(s) carregado(s)")
    else:
        st.warning("Nenhum arquivo selecionado ainda")

# ============================================================================
# PROCESSAR ARQUIVOS
# ============================================================================

if uploaded_files:
    st.info("⏳ Processando arquivos... por favor aguarde")

    progress_bar = st.progress(0)

    try:
        vendas = {}
        clientes_produtos = {}

        for idx, file in enumerate(uploaded_files):
            file_name = file.name.upper()
            progress = (idx + 1) / (len(uploaded_files) + 2)

            if "VENDAS POR ORDEM CRONOLOGICA" in file_name:
                st.write(f"Processando: {file.name}")
                vendas, vendas_count = processar_vendas_cronologica(file.getvalue())
                st.success(f"✓ {vendas_count} vendas lidas")

            elif "PRODUTOS VENDIDOS" in file_name:
                st.write(f"Processando: {file.name}")
                clientes_produtos, clientes_count = processar_produtos_cliente(file.getvalue())
                st.success(f"✓ {clientes_count} clientes com produtos lidos")

            progress_bar.progress(progress)

        if vendas and clientes_produtos:
            st.write("Consolidando base...")
            vendas_consolidadas = consolidar_base(vendas, clientes_produtos)
            ranking_df = gerar_ranking(vendas_consolidadas)

            progress_bar.progress(1.0)
            st.success("✓ Base consolidada com sucesso!")

        else:
            st.error("Erro: Arquivos necessários não encontrados!")
            st.stop()

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        st.stop()

    # ====================================================================
    # SEÇÃO 1: MÉTRICAS
    # ====================================================================
    st.divider()
    st.subheader("📊 Resumo dos Dados")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Vendas", len(vendas))

    with col2:
        st.metric("Clientes Únicos", len(ranking_df))

    with col3:
        total_vendido = ranking_df['Total_Gasto_LTV'].sum()
        st.metric("Total Faturado", f"R$ {total_vendido:,.2f}")

    with col4:
        ticket_medio = total_vendido / len(vendas)
        st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

    # ====================================================================
    # SEÇÃO 2: RANKING
    # ====================================================================
    st.divider()
    st.subheader("🎯 Ranking de Clientes para Reativação")

    col1, col2, col3 = st.columns(3)

    with col1:
        dias_filtro = st.slider(
            "Mínimo de dias parado",
            min_value=0,
            max_value=int(ranking_df['Dias_Parado'].max()),
            value=0,
            step=10
        )

    with col2:
        gasto_filtro = st.slider(
            "Mínimo gasto total (R$)",
            min_value=0,
            max_value=int(ranking_df['Total_Gasto_LTV'].max()),
            value=0,
            step=100
        )

    with col3:
        limite = st.number_input(
            "Mostrar top N clientes",
            min_value=5,
            max_value=len(ranking_df),
            value=20,
            step=5
        )

    ranking_filtrado = ranking_df[
        (ranking_df['Dias_Parado'] >= dias_filtro) &
        (ranking_df['Total_Gasto_LTV'] >= gasto_filtro)
    ].head(limite).copy()

    st.dataframe(
        ranking_filtrado[[
            'Cliente_Nome',
            'Dias_Parado',
            'Ultima_Compra',
            'Total_Gasto_LTV',
            'Num_Compras'
        ]].rename(columns={
            'Cliente_Nome': 'Cliente',
            'Dias_Parado': 'Dias',
            'Ultima_Compra': 'Última Compra',
            'Total_Gasto_LTV': 'LTV (R$)',
            'Num_Compras': 'Compras'
        }).astype({'Última Compra': 'str'}),
        use_container_width=True,
        height=400,
        column_config={
            'LTV (R$)': st.column_config.NumberColumn(format="R$ %.2f"),
            'Dias': st.column_config.NumberColumn(format="%d dias")
        }
    )

    # ====================================================================
    # SEÇÃO 3: GRÁFICOS
    # ====================================================================
    st.divider()
    st.subheader("📈 Análises Visuais")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Top 10 Clientes por LTV**")
        top_ltv = ranking_df.nlargest(10, 'Total_Gasto_LTV')
        st.bar_chart(
            data=top_ltv.set_index('Cliente_Nome')[['Total_Gasto_LTV']],
            use_container_width=True
        )

    with col2:
        st.write("**Distribuição: Dias Parado**")
        hist_data = ranking_df['Dias_Parado'].value_counts().sort_index()
        st.bar_chart(data=hist_data, use_container_width=True)

    # ====================================================================
    # SEÇÃO 4: DETALHES POR CLIENTE
    # ====================================================================
    st.divider()
    st.subheader("🔍 Detalhes Completos por Cliente")

    cliente_selecionado = st.selectbox(
        "Selecione um cliente:",
        options=sorted(ranking_filtrado['Cliente_Nome'].unique())
    )

    if cliente_selecionado:
        info_cliente = ranking_df[ranking_df['Cliente_Nome'] == cliente_selecionado].iloc[0]
        cliente_id = info_cliente['Cliente_ID']

        # Métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("ID", cliente_id)

        with col2:
            st.metric("Dias Parado", f"{int(info_cliente['Dias_Parado'])} dias")

        with col3:
            st.metric("LTV", f"R$ {info_cliente['Total_Gasto_LTV']:.2f}")

        with col4:
            st.metric("Compras", int(info_cliente['Num_Compras']))

        # Produtos
        st.divider()
        st.write("**🛍️ Produtos que Esta Cliente Comprou:**")

        if info_cliente['Produtos']:
            col1, col2 = st.columns([2, 1])

            with col1:
                # Lista de produtos
                produtos_df = pd.DataFrame({
                    'Produto': sorted(info_cliente['Produtos'])
                })
                st.dataframe(produtos_df, use_container_width=True, hide_index=True)

            with col2:
                st.write("**Categorias Preferidas:**")
                estilos = defaultdict(int)

                for produto in info_cliente['Produtos']:
                    produto_upper = str(produto).upper()

                    if 'BLUSA' in produto_upper:
                        estilos['BLUSAS'] += 1
                    elif 'CAMISA' in produto_upper:
                        estilos['CAMISAS'] += 1
                    elif 'CALCA' in produto_upper or 'CALÇA' in produto_upper:
                        estilos['CALÇAS'] += 1
                    elif 'VESTIDO' in produto_upper:
                        estilos['VESTIDOS'] += 1
                    elif 'SHORT' in produto_upper:
                        estilos['SHORTS'] += 1
                    elif 'CONJUNTO' in produto_upper:
                        estilos['CONJUNTOS'] += 1

                for estilo, qtd in sorted(estilos.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• {estilo}: {qtd}")

            # Sugestão de mensagem
            st.divider()
            st.write("**💬 Mensagem de Reativação Sugerida:**")

            todos_produtos = sorted(info_cliente['Produtos'], key=lambda x: (
                'VESTIDO' in x.upper(),
                'BLUSA' in x.upper(),
                'CAMISA' in x.upper()
            ), reverse=True)

            produtos_texto = ' | '.join(todos_produtos)

            msg = f"""
Oi {cliente_selecionado.split()[0]}! 👋

Sentimos sua falta! Já faz {int(info_cliente['Dias_Parado'])} DIAS que não nos vemos...

Você é especial pra gente! 💕

Sabe aqueles produtos que você ADORA?
✨ {produtos_texto}

Chegou tudo NOVO e LINDO! Volte logo!

[LINK DA LOJA]
            """

            st.info(msg)

        else:
            st.warning("Sem produtos registrados para esta cliente")

    # ====================================================================
    # SEÇÃO 5: DOWNLOADS
    # ====================================================================
    st.divider()
    st.subheader("💾 Downloads")

    col1, col2 = st.columns(2)

    with col1:
        ranking_csv = ranking_df.to_csv(sep=';', index=False, encoding='utf-8')
        st.download_button(
            label="📥 Ranking (CSV)",
            data=ranking_csv.encode('utf-8'),
            file_name="ranking_reativacao.csv",
            mime="text/csv"
        )

    with col2:
        st.write("Pronto para usar em seus disparos de reativação!")

else:
    st.info("""
    ### Como usar:

    1. **Exporte do ERP** os seguintes relatórios:
       - VENDAS POR ORDEM CRONOLOGICA
       - PRODUTOS VENDIDOS POR CLIENTE DURANTE PERIODO

    2. **Faça upload** dos arquivos XLS acima

    3. **O dashboard processará** automaticamente e mostrará:
       - Ranking de clientes para reativar
       - Produtos específicos que cada uma gosta
       - Sugestões de mensagens
       - Dados prontos para download

    Começe agora! ☝️
    """)

st.divider()
st.markdown("""
---
**Sistema de Reativação de Clientes - Versão Final**

Desenvolvido com ❤️ para lojas de roupas
""")
