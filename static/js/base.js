/* Tela 5 - Base de Conhecimento (RF05) */

const lista = document.getElementById("lista");
const vazio = document.getElementById("vazio");
const filtrosCategorias = document.getElementById("categorias");
const busca = document.getElementById("busca");
const ehTecnico = window.PERFIL === "tecnico";

let categoriaAtual = "";
let temporizador;

/* ---------- Categorias (chips) ---------- */
function criarChip(valor, rotulo) {
  const b = document.createElement("button");
  b.className = "filtro" + (valor === categoriaAtual ? " ativo" : "");
  b.dataset.categoria = valor;
  b.textContent = rotulo;
  return b;
}

function montarCategorias(categorias) {
  filtrosCategorias.innerHTML = "";
  filtrosCategorias.appendChild(criarChip("", "Todas as categorias"));
  categorias.forEach((cat) => filtrosCategorias.appendChild(criarChip(cat, cat)));
  const datalist = document.getElementById("lista-categorias");
  if (datalist) {
    datalist.innerHTML = categorias.map((c) => `<option value="${escapar(c)}">`).join("");
  }
}

/* ---------- Artigos ---------- */
function montarArtigos(artigos) {
  lista.innerHTML = "";
  if (!artigos.length) {
    vazio.style.display = "block";
    return;
  }
  vazio.style.display = "none";

  artigos.forEach((a) => {
    const div = document.createElement("div");
    div.className = "artigo";
    div._artigo = a;
    const acoes = ehTecnico ? `
      <div class="artigo-acoes">
        <button class="btn btn-secundario btn-pequeno" data-acao="editar">Editar</button>
        <button class="btn btn-secundario btn-pequeno" data-acao="excluir">Excluir</button>
      </div>` : "";
    div.innerHTML = `
      <div class="cat">${escapar(a.categoria)}</div>
      <h3>${escapar(a.titulo)}</h3>
      <p>${escapar(a.resumo)}</p>
      <div class="conteudo">${escapar(a.conteudo)}</div>
      <button class="ver-mais">Ver solução</button>
      ${acoes}`;
    const verMais = div.querySelector(".ver-mais");
    verMais.addEventListener("click", () => {
      const aberto = div.classList.toggle("aberto");
      verMais.textContent = aberto ? "Ocultar" : "Ver solução";
    });
    lista.appendChild(div);
  });
}

async function carregar() {
  let url = "/api/artigos";
  const params = [];
  if (categoriaAtual) params.push("categoria=" + encodeURIComponent(categoriaAtual));
  const termo = busca.value.trim();
  if (termo) params.push("q=" + encodeURIComponent(termo));
  if (params.length) url += "?" + params.join("&");

  const { ok, dados } = await API.get(url);
  if (!ok) return;
  montarCategorias(dados.categorias);
  montarArtigos(dados.artigos);
}

filtrosCategorias.addEventListener("click", (e) => {
  const botao = e.target.closest(".filtro");
  if (!botao) return;
  categoriaAtual = botao.dataset.categoria;
  document.querySelectorAll("#categorias .filtro").forEach((b) => b.classList.toggle("ativo", b === botao));
  carregar();
});

busca.addEventListener("input", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(carregar, 250);
});

/* ---------- Gestão (somente técnico) ---------- */
if (ehTecnico) {
  const formCard = document.getElementById("form-artigo-card");
  const form = document.getElementById("form-artigo");
  const aviso = document.getElementById("aviso");
  const formTitulo = document.getElementById("form-artigo-titulo");

  const limparErros = () => {
    document.querySelectorAll("#form-artigo .campo.invalido").forEach((c) => c.classList.remove("invalido"));
    document.querySelectorAll("#form-artigo .mensagem-erro").forEach((m) => (m.textContent = ""));
    aviso.className = "aviso";
  };
  const marcarErro = (campo, msg) => {
    const div = document.getElementById("campo-" + campo);
    if (!div) return;
    div.classList.add("invalido");
    const m = div.querySelector(`[data-erro="${campo}"]`);
    if (m) m.textContent = msg;
  };
  const setValor = (id, v) => (document.getElementById(id).value = v || "");

  const abrirForm = (artigo) => {
    limparErros();
    setValor("artigo-id", artigo ? artigo.id : "");
    setValor("artigo-categoria", artigo && artigo.categoria);
    setValor("artigo-titulo", artigo && artigo.titulo);
    setValor("artigo-resumo", artigo && artigo.resumo);
    setValor("artigo-conteudo", artigo && artigo.conteudo);
    formTitulo.textContent = artigo ? `Editar artigo #${artigo.id}` : "Novo artigo";
    formCard.style.display = "block";
    formCard.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const fecharForm = () => (formCard.style.display = "none");

  function validar(d) {
    const erros = {};
    if (d.categoria.length < 2) erros.categoria = "Informe a categoria.";
    if (d.titulo.length < 5) erros.titulo = "O título deve ter ao menos 5 caracteres.";
    if (d.resumo.length < 5) erros.resumo = "O resumo deve ter ao menos 5 caracteres.";
    if (d.conteudo.length < 10) erros.conteudo = "O conteúdo deve ter ao menos 10 caracteres.";
    return erros;
  }

  document.getElementById("btn-novo-artigo").addEventListener("click", () => abrirForm(null));
  document.getElementById("btn-cancelar-artigo").addEventListener("click", fecharForm);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    limparErros();
    const id = document.getElementById("artigo-id").value;
    const dados = {
      categoria: document.getElementById("artigo-categoria").value.trim(),
      titulo: document.getElementById("artigo-titulo").value.trim(),
      resumo: document.getElementById("artigo-resumo").value.trim(),
      conteudo: document.getElementById("artigo-conteudo").value.trim(),
    };
    const erros = validar(dados);
    if (Object.keys(erros).length) {
      Object.entries(erros).forEach(([c, m]) => marcarErro(c, m));
      return;
    }

    const botao = document.getElementById("btn-salvar-artigo");
    botao.disabled = true;
    const resp = id
      ? await API.req("PUT", `/api/artigos/${id}`, dados)
      : await API.post("/api/artigos", dados);
    botao.disabled = false;

    if (resp.ok) {
      fecharForm();
      await carregar();
    } else if (resp.status === 400 && resp.dados && resp.dados.campos) {
      Object.entries(resp.dados.campos).forEach(([c, m]) => marcarErro(c, m));
    } else {
      aviso.textContent = (resp.dados && resp.dados.erro) || "Não foi possível salvar o artigo.";
      aviso.className = "aviso erro";
    }
  });

  lista.addEventListener("click", async (e) => {
    const botao = e.target.closest("button[data-acao]");
    if (!botao) return;
    const artigo = botao.closest(".artigo")._artigo;
    if (botao.dataset.acao === "editar") {
      abrirForm(artigo);
    } else if (botao.dataset.acao === "excluir") {
      if (!confirm(`Excluir o artigo "${artigo.titulo}"?`)) return;
      const resp = await API.req("DELETE", `/api/artigos/${artigo.id}`);
      if (resp.ok) carregar();
    }
  });
}

carregar();
