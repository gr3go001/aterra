from app import db 
from sqlalchemy.orm import validates 





class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100) , nullable= False, unique= True)
    telefone = db.Column(db.String(15), nullable= False) # Formato(XX) XXXXX-XXXX
    endereco = db.Column(db.String(200), nullable= True)
    cpf = db.Column(db.String(14), nullable= False, unique= True) # Formato XXX.XXX.XXX-XX
    servico = db.Column(db.String(150), nullable= False) # O que o cliente busca
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)



class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    sala = db.Column(db.String(50), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)
    pago = db.Column(db.Boolean, default=False)