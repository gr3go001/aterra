from app.models import Agendamento

def verificar_conflito(sala, inicio, fim):
    return Agendamento.query.filter(
        Agendamento.sala == sala,
        Agendamento.data_fim > inicio,
        Agendamento.data_inicio < fim
    ).all()
