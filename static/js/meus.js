/* Tela 3 - Acompanhamento de Chamados (RF03) */

const corpo = document.getElementById("corpo-tabela");
const vazio = document.getElementById("vazio");
let statusAtual = "";

async function carregar() {
  let url = "/api/chamados?meus=1";
  if (statusAtual) url += "&status=" + encodeURIComponent(statusAtual);

  const { ok, dados } = await API.get(url);
  corpo.innerHTML = "";

  if (!ok || !dados.chamados.length) {
    vazio.style.display = "block";
    return;
  }
  vazio.style.display = "none";

  // Mais recentes primeiro.
  const lista = dados.chamados.slice().sort((a, b) => b.id - a.id);
  lista.forEach((c) => {
    const tr = document.createElement("tr");
    tr.className = "clicavel";
    const anexo = c.tem_anexo ? " " + tagAnexo() : "";
    tr.innerHTML = `
      <td class="num">#${c.id}</td>
      <td><a class="link-assunto" href="/chamados/${c.id}">${escapar(c.assunto)}</a>${anexo}</td>
      <td>${escapar(c.categoria)}</td>
      <td>${badgeStatus(c.status)}</td>
      <td>${formatarData(c.atualizado_em)}</td>`;
    // Clique em qualquer parte da linha abre o detalhe.
    tr.addEventListener("click", (ev) => {
      if (ev.target.closest("a")) return;
      window.location.href = "/chamados/" + c.id;
    });
    corpo.appendChild(tr);
  });
}

document.getElementById("filtros").addEventListener("click", (e) => {
  const botao = e.target.closest(".filtro");
  if (!botao) return;
  document.querySelectorAll(".filtro").forEach((b) => b.classList.remove("ativo"));
  botao.classList.add("ativo");
  statusAtual = botao.dataset.status;
  carregar();
});

carregar();
