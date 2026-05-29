/* Tela 1 - Login (RF01) */

const form = document.getElementById("form-login");
const aviso = document.getElementById("aviso");

function mostrarAviso(texto, tipo) {
  aviso.textContent = texto;
  aviso.className = "aviso " + tipo;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const usuario = document.getElementById("usuario").value.trim();
  const senha = document.getElementById("senha").value;

  if (!usuario || !senha) {
    mostrarAviso("Informe o usuário e a senha.", "erro");
    return;
  }

  const { ok, dados } = await API.post("/api/login", { usuario, senha });
  if (ok) {
    window.location.href = "/";
  } else {
    mostrarAviso((dados && dados.erro) || "Não foi possível entrar.", "erro");
  }
});

document.getElementById("esqueci").addEventListener("click", (e) => {
  e.preventDefault();
  mostrarAviso(
    "Um link de recuperação seria enviado ao seu e-mail institucional. " +
    "(Recurso ilustrativo neste protótipo.)",
    "sucesso"
  );
});
