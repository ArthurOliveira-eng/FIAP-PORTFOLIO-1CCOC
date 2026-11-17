// REQUISIÇÕES AO SERVIDOR LOCAL
export async function api(url, pedido) {
  const controle = new AbortController();
  const limite = setTimeout(() => controle.abort(), 15000);
  try {
    const resposta = await fetch(url, {
      signal: controle.signal,
      ...(pedido
        ? {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pedido),
          }
        : {}),
    });
    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.erro || dados.mensagem || "Não foi possível concluir a consulta.");
    }
    return dados;
  } catch (erro) {
    if (erro.name === "AbortError") throw new Error("A consulta demorou demais. Tente novamente.");
    if (erro instanceof TypeError) throw new Error("Não foi possível conectar ao servidor local.");
    if (erro instanceof SyntaxError) throw new Error("O servidor retornou uma resposta inválida.");
    throw erro;
  } finally {
    clearTimeout(limite);
  }
}
