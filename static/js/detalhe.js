/* Tela de detalhe do chamado (RF03/RF04) */

// Formata as datas renderizadas pelo servidor (elementos com data-data).
document.querySelectorAll("[data-data]").forEach((el) => {
  el.textContent = formatarData(el.getAttribute("data-data"));
});

const aviso = document.getElementById("aviso");

function avisar(texto, tipo) {
  if (!aviso) return;
  aviso.textContent = texto;
  aviso.className = "aviso " + tipo;
}

/* Botoes conforme a etapa do fluxo (apenas para o tecnico). */
function acoesPara(status) {
  if (status === "Aberto") {
    return [{ rotulo: "Assumir", acao: "assumir", classe: "btn-primario" }];
  }
  if (status === "Em análise") {
    return [
      { rotulo: "Concluir", acao: "status", status: "Concluído", classe: "btn-primario" },
      { rotulo: "Voltar p/ aberto", acao: "status", status: "Aberto", classe: "btn-secundario" },
    ];
  }
  return [{ rotulo: "Reabrir", acao: "status", status: "Em análise", classe: "btn-secundario" }];
}

async function executarAcao(botao, cfg) {
  botao.disabled = true;
  let resultado;
  if (cfg.acao === "assumir") {
    resultado = await API.post(`/api/chamados/${window.CHAMADO.id}/assumir`);
  } else {
    resultado = await API.patch(`/api/chamados/${window.CHAMADO.id}/status`, { status: cfg.status });
  }
  if (resultado.ok) {
    avisar("Chamado atualizado.", "sucesso");
    setTimeout(() => window.location.reload(), 500);
  } else {
    avisar((resultado.dados && resultado.dados.erro) || "Não foi possível atualizar.", "erro");
    botao.disabled = false;
  }
}

const container = document.getElementById("acoes-tecnico");
if (container && window.PERFIL === "tecnico") {
  acoesPara(window.CHAMADO.status).forEach((cfg) => {
    const botao = document.createElement("button");
    botao.className = "btn " + cfg.classe;
    botao.textContent = cfg.rotulo;
    botao.addEventListener("click", () => executarAcao(botao, cfg));
    container.appendChild(botao);
  });
}
