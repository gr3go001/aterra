from app import db 
from sqlalchemy.orm import relationship
from datetime import datetime
from app import db





class Cliente(db.Model):
    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100) , nullable= False, unique= True)
    telefone = db.Column(db.String(15), nullable= False) # Formato(XX) XXXXX-XXXX
    endereco = db.Column(db.String(200), nullable= True)
    cpf = db.Column(db.String(14), nullable= False, unique= True) # Formato XXX.XXX.XXX-XX
    servico = db.Column(db.String(150), nullable= False) # O que o cliente busca

    agendamentos = relationship('Agendamento', back_populates='cliente', cascade='all, delete-orphan')




class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id') )
    cliente = db.relationship('Cliente', back_populates='agendamentos')

    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    sala_rel = db.relationship('Sala', back_populates='agendamentos')

    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)

    valor_total = db.Column(db.Float, nullable=False)
    entrada = db.Column(db.Float, nullable=False)
    saldo = db.Column(db.Float, nullable=False)

    data_pagamento_entrada = db.Column(db.Date)
    metodo_pagamento_entrada = db.Column(db.String(20))

    data_pagamento_final = db.Column(db.Date)
    metodo_pagamento_final = db.Column(db.String(20))

    pago = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text, nullable=True)


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

    agendamentos = db.relationship('Agendamento', back_populates='sala_rel')


class FluxoCaixa(db.Model):
    __tablename__ = 'fluxo_caixa'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(10), nullable=False)  # entrada ou saida
    categoria = db.Column(db.String(100))
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))

    origem_agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamento.id'), nullable=True)
    agendamento = db.relationship('Agendamento', backref='movimentacoes')

    observacoes = db.Column(db.Text)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
