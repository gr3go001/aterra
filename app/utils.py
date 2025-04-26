from app.models import Agendamento

def verificar_conflito(sala_id, data_inicio, data_fim):
    conflitos = Agendamento.query.filter(
        Agendamento.sala_id == sala_id,
        Agendamento.data_inicio < data_fim,
        Agendamento.data_fim > data_inicio
    ).all()
    return conflitos
