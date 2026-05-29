/* Utilitarios compartilhados pelas telas do ChamaTI. */

const API = {
  async req(metodo, url, corpo) {
    const opcoes = { method: metodo, headers: {} };
    if (corpo !== undefined) {
      opcoes.headers["Content-Type"] = "application/json";
      opcoes.body = JSON.stringify(corpo);
    }
    const resp = await fetch(url, opcoes);
    let dados = null;
    try { dados = await resp.json(); } catch (e) { dados = null; }
    return { ok: resp.ok, status: resp.status, dados };
  },
  get(url) { return this.req("GET", url); },
  post(url, corpo) { return this.req("POST", url, corpo); },
  patch(url, corpo) { return this.req("PATCH", url, corpo); },
  /* Envio multipart (com arquivo): o navegador define o Content-Type. */
  async postForm(url, formData) {
    const resp = await fetch(url, { method: "POST", body: formData });
    let dados = null;
    try { dados = await resp.json(); } catch (e) { dados = null; }
    return { ok: resp.ok, status: resp.status, dados };
  },
};

/* Marcador de anexo reutilizado em listas e cartoes. */
function tagAnexo() {
  return '<span class="tag-anexo" title="Possui anexo">&#128206; anexo</span>';
}

/* Mapeia o status para a classe de badge (codificacao de cores do sistema). */
function classeStatus(status) {
  switch (status) {
    case "Aberto": return "status-aberto";
    case "Em análise": return "status-analise";
    case "Concluído": return "status-concluido";
    default: return "status-aberto";
  }
}

function badgeStatus(status) {
  return `<span class="badge ${classeStatus(status)}">${escapar(status)}</span>`;
}

function classeUrgencia(urgencia) {
  switch (urgencia) {
    case "Alta": return "urg-alta";
    case "Media": return "urg-media";
    case "Baixa": return "urg-baixa";
    default: return "";
  }
}

/* ISO -> dd/mm/aaaa hh:mm */
function formatarData(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/* Evita injecao de HTML ao inserir texto vindo da API. */
function escapar(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

/* Botao "Sair" presente na barra de navegacao. */
document.addEventListener("DOMContentLoaded", () => {
  const btnSair = document.getElementById("btn-sair");
  if (btnSair) {
    btnSair.addEventListener("click", async () => {
      await API.post("/api/logout");
      window.location.href = "/login";
    });
  }
});
