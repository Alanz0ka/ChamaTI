/* Tela de gestão de usuários (somente técnico) */

const form = document.getElementById("form-usuario");
const aviso = document.getElementById("aviso");
const corpo = document.getElementById("corpo-usuarios");
const PERFIL_LABEL = { colaborador: "Colaborador", tecnico: "Técnico" };

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

function validar(d) {
  const erros = {};
  if (d.nome.length < 2) erros.nome = "Informe o nome completo.";
  if (!d.email.includes("@") || d.email.length < 5) erros.email = "Informe um e-mail válido.";
  if (d.senha.length < 6) erros.senha = "A senha deve ter ao menos 6 caracteres.";
  if (!d.perfil) erros.perfil = "Selecione um perfil.";
  return erros;
}

async function carregar() {
  const { ok, dados } = await API.get("/api/usuarios");
  corpo.innerHTML = "";
  if (!ok) return;
  dados.usuarios.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapar(u.nome)}</td>
      <td>${escapar(u.email)}</td>
      <td>${escapar(PERFIL_LABEL[u.perfil] || u.perfil)}</td>`;
    corpo.appendChild(tr);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  limparErros();

  const dados = {
    nome: document.getElementById("nome").value.trim(),
    email: document.getElementById("email").value.trim(),
    senha: document.getElementById("senha").value,
    perfil: document.getElementById("perfil").value,
  };

  const erros = validar(dados);
  if (Object.keys(erros).length) {
    Object.entries(erros).forEach(([c, m]) => marcarErro(c, m));
    return;
  }

  const botao = document.getElementById("btn-criar");
  botao.disabled = true;
  const { ok, status, dados: resp } = await API.post("/api/usuarios", dados);
  botao.disabled = false;

  if (ok) {
    aviso.textContent = `Usuário ${resp.usuario.nome} (${PERFIL_LABEL[resp.usuario.perfil]}) criado com sucesso.`;
    aviso.className = "aviso sucesso";
    form.reset();
    carregar();
  } else if (status === 400 && resp && resp.campos) {
    Object.entries(resp.campos).forEach(([c, m]) => marcarErro(c, m));
  } else {
    aviso.textContent = (resp && resp.erro) || "Não foi possível criar o usuário.";
    aviso.className = "aviso erro";
  }
});

carregar();
