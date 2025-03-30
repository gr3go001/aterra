from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import Cliente, Agendamento
from app.utils import verificar_conflito
from datetime import datetime

main = Blueprint('main', __name__)



@main.route('/' , methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@main.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        sala = request.form['sala']
        data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%dT%H:%M' )
        data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%dT%H:%M')
        pago = request.form.get('pago') == 'on'

        from app.utils import verificar_conflito
        conflitos = verificar_conflito(sala, data_inicio, data_fim)

        if conflitos:
            return "Conflito de agendamento! Por favor, escolha outro horário.", 400

        agendamento = Agendamento(cliente_id=cliente_id, sala=sala, data_inicio=data_inicio, data_fim=data_fim, pago=pago)
        db.session.add(agendamento)
        db.session.commit()
        return redirect(url_for('main.index'))
    
    clientes = Cliente.query.all()
    return render_template('agendar.html', clientes=clientes)

@main.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cliente = Cliente(nome=nome, email=email)
        db.session.add(cliente)
        db.session.commit()
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
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('editar_cliente.html', cliente=cliente)

@main.route('/relatorio', methods=['GET', 'POST'])
def relatorio():
    agendamentos = []
    if request.method == 'POST':
        inicio = datetime.strptime(request.form['inicio'], '%Y-%m-%d')
        fim = datetime.strptime(request.form['fim'], '%Y-%m-%d')
        agendamentos = Agendamento.query.filter(
            Agendamento.data_inicio >= inicio,
            Agendamento.data_fim <= fim
        ).all()
    return render_template('relatorio.html', agendamentos=agendamentos)