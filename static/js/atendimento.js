/* Tela 4 - Gestao e Atendimento (RF04) */

const aviso = document.getElementById("aviso");
const COLUNAS = {
  "Aberto": "col-aberto",
  "Em análise": "col-analise",
  "Concluído": "col-concluido",
};
const CONTADORES = {
  "Aberto": "cont-aberto",
  "Em análise": "cont-analise",
  "Concluído": "cont-concluido",
};

function avisar(texto, tipo) {
  aviso.textContent = texto;
  aviso.className = "aviso " + tipo;
  if (tipo === "sucesso") setTimeout(() => (aviso.className = "aviso"), 2500);
}

async function carregarIndicadores() {
  const { ok, dados } = await API.get("/api/indicadores");
  if (!ok) return;
  document.getElementById("ind-pendentes").textContent = dados.pendentes;
  document.getElementById("ind-analise").textContent = dados.em_analise;
  document.getElementById("ind-concluidos").textContent = dados.concluidos;
  document.getElementById("ind-tempo").textContent = dados.tempo_medio;
}

/* Botoes de acao conforme a etapa do fluxo (controle e liberdade do usuario). */
function acoesPara(c) {
  if (c.status === "Aberto") {
    return `<button class="btn btn-primario btn-pequeno" data-acao="assumir" data-id="${c.id}">Assumir</button>`;
  }
  if (c.status === "Em análise") {
    return `
      <button class="btn btn-primario btn-pequeno" data-acao="status" data-status="Concluído" data-id="${c.id}">Concluir</button>
      <button class="btn btn-secundario btn-pequeno" data-acao="status" data-status="Aberto" data-id="${c.id}">Voltar p/ aberto</button>`;
  }
  return `<button class="btn btn-secundario btn-pequeno" data-acao="status" data-status="Em análise" data-id="${c.id}">Reabrir</button>`;
}

function cartao(c) {
  const resp = c.responsavel_nome ? escapar(c.responsavel_nome) : "—";
  return `
    <div class="card-chamado">
      <div class="topo">
        <span class="num">#${c.id}</span>
        <span class="urgencia ${classeUrgencia(c.urgencia)}">${escapar(c.urgencia)}</span>
      </div>
      <div class="assunto">${escapar(c.assunto)}</div>
      <div class="meta">${escapar(c.categoria)} · Responsável: ${resp}</div>
      <div class="acoes">${acoesPara(c)}</div>
    </div>`;
}

async function carregarQuadro() {
  const { ok, dados } = await API.get("/api/chamados");
  if (!ok) return;

  Object.values(COLUNAS).forEach((id) => (document.getElementById(id).innerHTML = ""));
  const contagem = { "Aberto": 0, "Em análise": 0, "Concluído": 0 };

  dados.chamados.slice().sort((a, b) => b.id - a.id).forEach((c) => {
    const col = document.getElementById(COLUNAS[c.status]);
    if (!col) return;
    col.insertAdjacentHTML("beforeend", cartao(c));
    contagem[c.status]++;
  });

  Object.entries(CONTADORES).forEach(([st, id]) => {
    document.getElementById(id).textContent = contagem[st];
  });
}

async function atualizarTudo() {
  await Promise.all([carregarIndicadores(), carregarQuadro()]);
}

document.querySelector(".kanban").addEventListener("click", async (e) => {
  const botao = e.target.closest("button[data-acao]");
  if (!botao) return;
  const id = botao.dataset.id;
  botao.disabled = true;

  let resultado;
  if (botao.dataset.acao === "assumir") {
    resultado = await API.post(`/api/chamados/${id}/assumir`);
  } else {
    resultado = await API.patch(`/api/chamados/${id}/status`, { status: botao.dataset.status });
  }

  if (resultado.ok) {
    avisar(resultado.dados.mensagem || "Atualizado.", "sucesso");
    await atualizarTudo();
  } else {
    avisar((resultado.dados && resultado.dados.erro) || "Não foi possível atualizar.", "erro");
    botao.disabled = false;
  }
});

atualizarTudo();
