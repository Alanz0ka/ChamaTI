/* Tela 2 - Abertura de Chamado (RF02) */

const form = document.getElementById("form-chamado");
const aviso = document.getElementById("aviso");
const TAM_MAX = 5 * 1024 * 1024; // 5 MB

/* Preenche os selects com as opcoes oficiais do back-end (prevencao de erros). */
async function carregarOpcoes() {
  const { ok, dados } = await API.get("/api/opcoes");
  if (!ok) return;
  const cat = document.getElementById("categoria");
  const urg = document.getElementById("urgencia");
  dados.categorias.forEach((c) => cat.add(new Option(c, c)));
  dados.urgencias.forEach((u) => urg.add(new Option(u, u)));
}

function limparErros() {
  document.querySelectorAll(".campo.invalido").forEach((c) => c.classList.remove("invalido"));
  document.querySelectorAll(".mensagem-erro").forEach((m) => (m.textContent = ""));
  aviso.className = "aviso";
}

function marcarErro(campo, mensagem) {
  const div = document.getElementById("campo-" + campo);
  if (!div) return;
  div.classList.add("invalido");
  const msg = div.querySelector(`[data-erro="${campo}"]`);
  if (msg) msg.textContent = mensagem;
}

/* Validacao no cliente espelhando as regras do back-end. */
function validar(dados) {
  const erros = {};
  if (!dados.categoria) erros.categoria = "Selecione uma categoria.";
  if (!dados.urgencia) erros.urgencia = "Selecione a urgência.";
  if (dados.assunto.length < 5) erros.assunto = "O assunto deve ter ao menos 5 caracteres.";
  if (dados.descricao.length < 10) erros.descricao = "A descrição deve ter ao menos 10 caracteres.";
  return erros;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  limparErros();

  const dados = {
    categoria: document.getElementById("categoria").value,
    urgencia: document.getElementById("urgencia").value,
    assunto: document.getElementById("assunto").value.trim(),
    descricao: document.getElementById("descricao").value.trim(),
  };

  const erros = validar(dados);
  if (Object.keys(erros).length) {
    Object.entries(erros).forEach(([c, m]) => marcarErro(c, m));
    return;
  }

  const botao = document.getElementById("btn-enviar");
  botao.disabled = true;
  const { ok, status, dados: resp } = await API.post("/api/chamados", dados);
  botao.disabled = false;

  if (ok) {
    aviso.textContent = `Chamado #${resp.chamado.id} aberto com sucesso! Redirecionando para "Meus chamados"...`;
    aviso.className = "aviso sucesso";
    form.reset();
    document.getElementById("anexo-info").textContent = "Formatos aceitos: PNG, JPG, PDF · até 5 MB";
    setTimeout(() => (window.location.href = "/meus-chamados"), 1400);
  } else if (status === 400 && resp && resp.campos) {
    Object.entries(resp.campos).forEach(([c, m]) => marcarErro(c, m));
  } else {
    aviso.textContent = (resp && resp.erro) || "Não foi possível abrir o chamado.";
    aviso.className = "aviso erro";
  }
});

document.getElementById("btn-cancelar").addEventListener("click", () => {
  window.location.href = "/meus-chamados";
});

/* Area de anexo (ilustrativa). */
const areaAnexo = document.getElementById("area-anexo");
const inputAnexo = document.getElementById("anexo");
const anexoInfo = document.getElementById("anexo-info");

areaAnexo.addEventListener("click", () => inputAnexo.click());
inputAnexo.addEventListener("change", () => {
  const arquivo = inputAnexo.files[0];
  if (!arquivo) return;
  if (arquivo.size > TAM_MAX) {
    anexoInfo.textContent = "Arquivo acima de 5 MB. Escolha um arquivo menor.";
    inputAnexo.value = "";
    return;
  }
  anexoInfo.textContent = `Selecionado: ${arquivo.name}`;
});

carregarOpcoes();
