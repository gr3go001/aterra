async function verificarCliente() {
    const nome = document.getElementById('nome_cliente').value;
    const resposta = await fetch(`/verificar_cliente?nome=${encodeURIComponent(nome)}`);
    const dados = await resposta.json();
    const aviso = document.getElementById('aviso-cliente');
    const botaoAgendar = document.getElementById('botao-agendar');
  
    if (dados.existe) {
      aviso.innerHTML = '<span class="text-success">Cliente encontrado.</span>';
      botaoAgendar.disabled = false;
    } else {
      aviso.innerHTML = '<span class="text-danger">Cliente não cadastrado!</span>';
      botaoAgendar.disabled = true;
    }
  }
  