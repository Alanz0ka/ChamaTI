/* Tela 5 - Base de Conhecimento (RF05) */

const lista = document.getElementById("lista");
const vazio = document.getElementById("vazio");
const filtrosCategorias = document.getElementById("categorias");
const busca = document.getElementById("busca");

let categoriaAtual = "";
let categoriasCarregadas = false;
let temporizador;

function montarCategorias(categorias) {
  categorias.forEach((cat) => {
    const botao = document.createElement("button");
    botao.className = "filtro";
    botao.dataset.categoria = cat;
    botao.textContent = cat;
    filtrosCategorias.appendChild(botao);
  });
  categoriasCarregadas = true;
}

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
    div.innerHTML = `
      <div class="cat">${escapar(a.categoria)}</div>
      <h3>${escapar(a.titulo)}</h3>
      <p>${escapar(a.resumo)}</p>
      <div class="conteudo">${escapar(a.conteudo)}</div>
      <button class="ver-mais">Ver solução</button>`;
    const botao = div.querySelector(".ver-mais");
    botao.addEventListener("click", () => {
      const aberto = div.classList.toggle("aberto");
      botao.textContent = aberto ? "Ocultar" : "Ver solução";
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
  if (!categoriasCarregadas) montarCategorias(dados.categorias);
  montarArtigos(dados.artigos);
}

filtrosCategorias.addEventListener("click", (e) => {
  const botao = e.target.closest(".filtro");
  if (!botao) return;
  document.querySelectorAll("#categorias .filtro").forEach((b) => b.classList.remove("ativo"));
  botao.classList.add("ativo");
  categoriaAtual = botao.dataset.categoria;
  carregar();
});

busca.addEventListener("input", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(carregar, 250);
});

carregar();
