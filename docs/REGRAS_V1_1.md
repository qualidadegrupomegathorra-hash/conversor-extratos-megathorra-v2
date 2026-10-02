# Regras de segurança de estado — v1.1

A versão 1.1 adiciona proteções contra reaproveitamento acidental de uma conversão anterior:

1. Ao trocar o banco, o upload anterior é invalidado e um novo upload é obrigatório.
2. O botão **Nova conversão** também invalida o ciclo anterior.
3. O arquivo de saída só é liberado quando banco, nome do arquivo, conteúdo (SHA-256) e ciclo de conversão correspondem ao processamento atual.
4. O `meta.bank` retornado pelo parser precisa ser igual ao banco selecionado; caso contrário a exportação é bloqueada.
5. Antes do download, a tela exibe claramente banco, arquivo de origem, agência, conta, dígito e nome do CSV que será gerado.

Essas regras não alteram os layouts financeiros já existentes nem as regras de conversão do Santander validado.
