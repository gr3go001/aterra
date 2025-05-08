from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from app import db
from app.models import Cliente, Agendamento, Sala, FluxoCaixa
from app.utils import verificar_conflito
from datetime import datetime
from sqlalchemy import func, or_, cast
from sqlalchemy.orm import joinedload
import unicodedata
import pandas as pd
import io
from io import BytesIO
from flask import send_file
import csv

main = Blueprint('main', __name__)

def normalizar(texto):
    if not texto:
        return ""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()


@main.route('/busca')
def busca_agendamentos():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    filtro = f"%{q}%"
    resultados = (
        Agendamento.query
        .join(Cliente, Agendamento.cliente_id == Cliente.id)
        .options(
            joinedload(Agendamento.cliente), 
            joinedload(Agendamento.sala_rel)
        )
        .filter(
            or_(
                Cliente.nome.ilike(filtro),
                Cliente.email.ilike(filtro),
                cast(Agendamento.data_inicio, db.String).ilike(filtro)
            )
        )
        .all()
    )

    lista = [{
        'id': a.id,
        'nome': a.cliente.nome,
        'email': a.cliente.email,
        'sala': a.sala_rel.nome,
        'data_inicio': a.data_inicio.isoformat(),
        'data_fim': a.data_fim.isoformat(),
        'valor_total': a.valor_total,
        'entrada': a.entrada,
        'saldo': a.saldo,
        'pago': a.pago
    } for a in resultados]

    return jsonify(lista)



@main.route('/', methods=['GET'])
def index():
    agendamentos = Agendamento.query.options(joinedload(Agendamento.sala_rel)).order_by(Agendamento.data_inicio.desc()).all()
    return render_template('index.html', agendamentos=agendamentos)


@main.route('/editar_agendamento/<int:id>', methods=['GET', 'POST'])
def editar_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)
    salas = Sala.query.order_by(Sala.nome).all()

    if request.method == 'POST':
        sala_id = request.form.get('sala_id')
        agendamento.sala_id = sala_id
        agendamento.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%dT%H:%M')
        agendamento.data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%dT%H:%M')
        agendamento.valor_total = float(request.form['valor_total'])
        agendamento.entrada = float(request.form['entrada'])

        data_pag_entrada = request.form.get('data_pagamento_entrada')
        data_pag_final = request.form.get('data_pagamento_final')

        agendamento.data_pagamento_entrada = datetime.strptime(data_pag_entrada, '%Y-%m-%d').date() if data_pag_entrada else None
        agendamento.data_pagamento_final = datetime.strptime(data_pag_final, '%Y-%m-%d').date() if data_pag_final else None

        agendamento.metodo_pagamento_entrada = request.form.get('metodo_pagamento_entrada')
        agendamento.metodo_pagamento_final = request.form.get('metodo_pagamento_final')

        valor_final_pago = agendamento.valor_total - agendamento.entrada
        agendamento.saldo = 0.0 if agendamento.data_pagamento_final else valor_final_pago
        agendamento.pago = agendamento.saldo == 0

        db.session.commit()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('main.index'))

    return render_template('editar_agendamento.html', agendamento=agendamento, salas=salas)

@main.route('/autocomplete_clientes')
def autocomplete_clientes():
    termo = request.args.get('termo', '')
    clientes = Cliente.query.filter(Cliente.nome.ilike(f'%{termo}%')).limit(10).all()
    return jsonify([{'id': c.id, 'nome': c.nome} for c in clientes])

@main.route('/excluir_agendamento/<int:id>', methods=['GET'])
def excluir_agendamento(id):
    agendamento = Agendamento.query.get_or_404(id)
    db.session.delete(agendamento)
    db.session.commit()
    flash('Agendamento excluído com sucesso!', 'info')
    return redirect(url_for('main.index'))

@main.route('/verificar_cliente')
def verificar_cliente():
    nome = request.args.get('nome', '').strip()
    nome_normalizado = normalizar(nome)
    cliente = Cliente.query.filter(func.lower(Cliente.nome) == nome_normalizado).first()
    return jsonify({'existe': cliente is not None})

@main.route('/cadastrar_cliente_rapido', methods=['POST'])
def cadastrar_cliente_rapido():
    nome = request.form.get('nome_cliente')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    endereco = request.form.get('endereco')
    cpf = request.form.get('cpf')
    servico = request.form.get('servico')

    if nome:
        cliente_existente = Cliente.query.filter(func.lower(Cliente.nome) == normalizar(nome)).first()
        if not cliente_existente:
            novo_cliente = Cliente(
                nome=nome,
                email=email,
                telefone=telefone,
                endereco=endereco,
                cpf=cpf,
                servico=servico
            )
            db.session.add(novo_cliente)
            db.session.commit()
            return jsonify({'sucesso': True, 'cliente_id': novo_cliente.id, 'nome': novo_cliente.nome})
    return jsonify({'sucesso': False})

# CONTINUARÁ NA PRÓXIMA ATUALIZAÇÃO...
@main.route('/agendar', methods=['GET', 'POST'])
def agendar():
    salas = Sala.query.order_by(Sala.nome).all()
    cliente_cadastrado = False
    nome_cliente = ''

    if request.method == 'POST':
        sala_id = request.form.get('sala_id')
        acao = request.form.get('acao')
        nome_cliente = request.form.get('nome_cliente')
        cliente_id = request.form.get('cliente_id')
        observacoes = request.form.get('observacoes')

        if acao == 'cadastrar':
            novo_cliente = Cliente(
                nome=nome_cliente,
                email=request.form['email'],
                telefone=request.form['telefone'],
                endereco=request.form['endereco'],
                cpf=request.form['cpf'],
                servico=request.form['servico']
                )
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            cliente_cadastrado = True

        elif acao == 'agendar':
            if not cliente_id:
                flash('Você precisa selecionar um cliente válido.', 'danger')
                return render_template('agendar.html', salas=salas, cliente_cadastrado=False, nome_cliente=nome_cliente)

            cliente = Cliente.query.get(cliente_id)
            sala = Sala.query.get(sala_id)

            if not cliente or not sala:
                flash('Cliente ou sala inválidos.', 'danger')
                return render_template('agendar.html', salas=salas, cliente_cadastrado=False, nome_cliente=nome_cliente)

            data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%dT%H:%M')
            data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%dT%H:%M')

            conflitos = verificar_conflito(sala.id, data_inicio, data_fim)
            if conflitos:
                flash('Conflito de agendamento detectado.', 'danger')
                return render_template('agendar.html', salas=salas, cliente_cadastrado=True, nome_cliente=nome_cliente)

            agendamento = Agendamento(
                cliente_id=cliente.id,
                sala_id=sala.id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                valor_total=float(request.form['valor_total']),
                entrada=float(request.form['entrada']),
                saldo=max(0, float(request.form['valor_total']) - float(request.form['entrada'])),
                data_pagamento_entrada=datetime.strptime(request.form.get('data_pagamento_entrada'), '%Y-%m-%d').date() if request.form.get('data_pagamento_entrada') else None,
                metodo_pagamento_entrada=request.form.get('metodo_pagamento_entrada'),
                metodo_pagamento_final=None,
                data_pagamento_final=None,
                pago=(float(request.form['valor_total']) - float(request.form['entrada']) == 0),
                observacoes=observacoes
            )


            db.session.add(agendamento)
            db.session.commit()
            flash('Agendamento realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))

    return render_template('agendar.html', salas=salas, cliente_cadastrado=cliente_cadastrado, nome_cliente=nome_cliente)

@main.route('/relatorio_salas', methods=['GET', 'POST'])
def relatorio_salas():
    resultados = []
    labels = []
    valores = []

    meses = [{'nome': 'Janeiro', 'valor': '01'}, {'nome': 'Fevereiro', 'valor': '02'}, {'nome': 'Março', 'valor': '03'},
             {'nome': 'Abril', 'valor': '04'}, {'nome': 'Maio', 'valor': '05'}, {'nome': 'Junho', 'valor': '06'},
             {'nome': 'Julho', 'valor': '07'}, {'nome': 'Agosto', 'valor': '08'}, {'nome': 'Setembro', 'valor': '09'},
             {'nome': 'Outubro', 'valor': '10'}, {'nome': 'Novembro', 'valor': '11'}, {'nome': 'Dezembro', 'valor': '12'}]

    mes_selecionado = request.form.get('mes')
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')

    query = db.session.query(
        Sala.nome.label('sala_nome'),
        func.count(Agendamento.id).label('quantidade'),
        func.sum(Agendamento.valor_total).label('total'),
        func.avg(Agendamento.valor_total).label('media')
    ).join(Sala, Sala.id == Agendamento.sala_id).group_by(Sala.nome)

    if mes_selecionado:
        ano_atual = datetime.now().year
        data_inicio = datetime.strptime(f'{ano_atual}-{mes_selecionado}-01', '%Y-%m-%d')
        if mes_selecionado == '12':
            data_fim = datetime.strptime(f'{ano_atual + 1}-01-01', '%Y-%m-%d')
        else:
            data_fim = datetime.strptime(f'{ano_atual}-{int(mes_selecionado) + 1:02d}-01', '%Y-%m-%d')

    elif data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        except ValueError:
            data_inicio = data_fim = None

    if data_inicio and data_fim:
        query = query.filter(Agendamento.data_inicio >= data_inicio, Agendamento.data_inicio < data_fim)

    resultados_query = query.all()

    for r in resultados_query:
        resultados.append({
            'nome': r.sala_nome,
            'quantidade': r.quantidade,
            'total': float(r.total or 0),
            'media': float(r.media or 0)
        })
        labels.append(r.sala_nome)
        valores.append(float(r.total or 0))

    return render_template('relatorio_salas.html', resultados=resultados, meses=meses, mes_selecionado=mes_selecionado,
                           data_inicio=data_inicio.strftime('%Y-%m-%d') if isinstance(data_inicio, datetime) else '',
                           data_fim=data_fim.strftime('%Y-%m-%d') if isinstance(data_fim, datetime) else '',
                           labels=labels, valores=valores)

@main.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        email = request.form['email']
        email_existente = Cliente.query.filter_by(email=email).first()

        if email_existente:
            flash("Este e-mail já está cadastrado para outro cliente.", "danger")
            return redirect(url_for('main.cadastrar_cliente'))

        cliente = Cliente(
            nome=request.form['nome'],
            email=email,
            telefone=request.form['telefone'],
            endereco=request.form['endereco'],
            cpf=request.form['cpf'],
            servico=request.form['servico']
        )
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for('main.index'))

    return render_template('cadastrar_cliente.html')

@main.route('/cliente/<int:id>')
def visualizar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    agendamentos = Agendamento.query.filter_by(cliente_id=id).order_by(Agendamento.data_inicio.desc()).all()
    return render_template('visualizar_cliente.html', cliente=cliente, agendamentos=agendamentos)

@main.route('/pesquisar_cliente')
def pesquisar_cliente():
    termo = request.args.get('termo', '')
    resultados = Cliente.query.filter(
        (Cliente.nome.ilike(f'%{termo}%')) |
        (Cliente.email.ilike(f'%{termo}%'))
    ).all()
    return render_template('pesquisar_cliente.html', resultados=resultados, termo=termo)

@main.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.email = request.form['email']
        cliente.telefone = request.form['telefone']
        cliente.endereco = request.form['endereco']
        cliente.cpf = request.form['cpf']
        cliente.servico = request.form['servico']
        db.session.commit()
        flash("Cliente atualizado com sucesso!", "info")
        return redirect(url_for('main.index'))
    return render_template('editar_cliente.html', cliente=cliente)

@main.route('/buscar_clientes')
def buscar_clientes():
    termo = request.args.get('termo', '')
    clientes = Cliente.query.filter(
        (Cliente.nome.ilike(f'%{termo}%')) 
        (Cliente.email.ilike(f'%{termo}%'))
    ).all()
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'email': c.email,
        'telefone': c.telefone,
        'endereco': c.endereco,
        'cpf': c.cpf,
        'servico': c.servico
    } for c in clientes])


@main.route('/excluir_cliente/<int:id>')
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    for agendamento in cliente.agendamentos:
        db.session.delete(agendamento)

    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente excluído com sucesso!", "danger")
    return redirect(url_for('main.index'))

@main.route('/relatorio', methods=['GET', 'POST'])
def relatorio():
    agendamentos = []
    if request.method == 'POST':
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        if data_inicio and data_fim:
            agendamentos = Agendamento.query.join(Cliente).filter(
                Agendamento.data_inicio >= data_inicio,
                Agendamento.data_inicio <= data_fim
            ).order_by(Agendamento.data_inicio.asc()).all()
            flash("Filtrando agendamentos entre as datas.", "info")
    return render_template('relatorio.html', agendamentos=agendamentos)



@main.route('/exportar_excel')
def exportar_excel():
    # 1) Busca os agendamentos no banco
    ags = Agendamento.query.order_by(Agendamento.data_inicio).all()

    # 2) Monta uma lista de dicionários
    data = []
    for a in ags:
        data.append({
            'Cliente':        a.cliente.nome,
            'Sala':           a.sala_rel.nome,
            'Início':         a.data_inicio.strftime('%d/%m/%Y %H:%M'),
            'Fim':            a.data_fim.strftime('%d/%m/%Y %H:%M'),
            'Valor Total':    f"{a.valor_total:.2f}",
            'Entrada':        f"{a.entrada:.2f}",
            'Saldo':          f"{a.saldo:.2f}",
            'Pago':           'Sim' if a.pago else 'Não',
            'Data Pagamento': a.data_pagamento_entrada.strftime('%d/%m/%Y') if a.data_pagamento_entrada else '',
            'Observações':    a.observacoes or ''
        })

    # 3) Cria o DataFrame
    df = pd.DataFrame(data)

    # 4) Escreve no Excel usando BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Agendamentos')
        ws = writer.sheets['Agendamentos']

        # 4.1) Cabeçalho em negrito
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)

        # 4.2) Auto-ajusta largura das colunas
        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            ws.column_dimensions[col[0].column_letter].width = max_len + 2

        # 4.3) Fit to width e orientação paisagem
        ws.page_setup.fitToWidth = 1
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_margins.left   = 0.5
        ws.page_margins.right  = 0.5
        ws.page_margins.top    = 0.5
        ws.page_margins.bottom = 0.5

    # 5) Volta ao início do buffer e envia o arquivo
    output.seek(0)
    return send_file(
        output,
        download_name='agendamentos.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@main.route('/fluxo_caixa', methods=['GET', 'POST'])
def fluxo_caixa():
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo')
            valor = request.form.get('valor')
            categoria = request.form.get('categoria')
            forma_pagamento = request.form.get('forma_pagamento')
            descricao = request.form.get('descricao')
            origem_agendamento_id = request.form.get('origem_agendamento_id') or None
            observacoes = request.form.get('observacoes')
            data = request.form.get('data') or datetime.today().date()

            nova_movimentacao = FluxoCaixa(
                tipo=tipo,
                valor=valor,
                categoria=categoria,
                forma_pagamento=forma_pagamento,
                descricao=descricao,
                origem_agendamento_id=origem_agendamento_id,
                observacoes=observacoes,
                data=data
            )

            db.session.add(nova_movimentacao)
            db.session.commit()
            flash("Movimentação registrada com sucesso!", "success")
            return redirect('/fluxo_caixa')
        except Exception as e:
            print("Erro ao salvar no banco:", e)
            flash(f"Erro ao registrar movimentação: {str(e)}", "danger")
            

    agendamentos = Agendamento.query.order_by(Agendamento.data_inicio.desc()).all()
    return render_template('fluxo_caixa.html', agendamentos=agendamentos)

@main.route('/dashboard_fluxo_caixa')
def dashboard_fluxo_caixa():
    from app.models import FluxoCaixa

    # Coleta todos os dados do fluxo
    movimentacoes = FluxoCaixa.query.order_by(FluxoCaixa.data).all()

    total_entradas = sum(m.valor for m in movimentacoes if m.tipo == 'entrada')
    total_saidas = sum(m.valor for m in movimentacoes if m.tipo == 'saida')
    saldo = total_entradas - total_saidas

    # Dados por mês (YYYY-MM)
    from collections import defaultdict
    import calendar

    dados_por_mes = defaultdict(lambda: {'entrada': 0, 'saida': 0})

    for m in movimentacoes:
        chave = m.data.strftime('%Y-%m')
        dados_por_mes[chave][m.tipo] += float(m.valor)

    meses_labels = []
    entradas_valores = []
    saidas_valores = []

    for chave in sorted(dados_por_mes.keys()):
        ano, mes = chave.split('-')
        nome_mes = f"{calendar.month_abbr[int(mes)]}/{ano[-2:]}"
        meses_labels.append(nome_mes)
        entradas_valores.append(dados_por_mes[chave]['entrada'])
        saidas_valores.append(dados_por_mes[chave]['saida'])

    # Gráfico de pizza por forma de pagamento (só para entradas)
    from collections import Counter

    formas_pagamento = Counter(
        m.forma_pagamento for m in movimentacoes if m.tipo == 'entrada' and m.forma_pagamento
    )

    return render_template(
        'dashboard_fluxo_caixa.html',
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo=saldo,
        meses_labels=meses_labels,
        entradas_valores=entradas_valores,
        saidas_valores=saidas_valores,
        formas_pagamento=dict(formas_pagamento),
        movimentacoes=movimentacoes
    )

@main.route('/criar_salas')
def criar_salas():
    from app.models import Sala
    if Sala.query.count() == 0:
        salas = [
            Sala(nome="Sala Azul"),
            Sala(nome="Sala Verde"),
            Sala(nome="Sala Terapia 1")
        ]
        db.session.add_all(salas)
        db.session.commit()
        return "✅ Salas criadas com sucesso!"
    return "ℹ️ As salas já existem."
