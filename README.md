# PINGTOP

Monitor de ping para Linux com interface de terminal inspirada no btop. Acompanhe até 1.024 alvos, com até 32 pings simultâneos, com latência da última resposta, percentual de perda e histórico visual por alvo.

## Como rodar

Requer Python 3.10+, um terminal com suporte a UTF-8 e o comando `ping` do iputils (pacote `iputils-ping` no Debian/Ubuntu).

```sh
git clone https://github.com/MatheusHSFeitosa/pingtop.git
cd pingtop
./pingtop 127.0.0.1 1.1.1.1 example.com
```

Aceita IPv4, IPv6, nomes de host, faixas IPv4 inclusivas e blocos CIDR IPv4.

```sh
./pingtop 192.168.1.0/24
./pingtop 192.168.1.1-192.168.1.254
```

Você também pode digitar uma faixa ou CIDR pela tecla `a`. No CIDR, o programa usa os endereços de host do bloco, incluindo os dois IPs de um /31 e o IP único de um /32. Alvos repetidos são ignorados. Em listas grandes, as sondagens excedentes aguardam na fila.

 Use `-i 2` para definir um intervalo de dois segundos, ou abra sem argumentos e adicione os alvos na interface.

| Tecla | Ação |
| --- | --- |
| ↑ / ↓ | Selecionar alvo e ver seu histórico |
| a | Adicionar alvo |
| d | Remover alvo selecionado |
| PgUp / PgDn | Navegar por página |
| t | Iniciar ou parar o Tracert do alvo selecionado |
| Tab | Alternar entre a lista de alvos e a de saltos |
| Esc / m | Abrir o menu principal |
| ? | Abrir ou fechar a ajuda |
| q | Sair |

A perda é acumulada desde a adição do alvo. O gráfico exibe até 512 amostras recentes, conforme a largura disponível, ajusta a escala ao maior valor exibido e marca amostras sem latência com `×`. O estado `ERRO` indica falha na execução ou na resolução do alvo e fica fora do cálculo de perda.

## Rota e gráfico

Instale o pacote opcional `traceroute` para usar o Tracert ICMP. Pressione
`t` para sondar continuamente a rota do alvo selecionado, até 24 saltos.
Use `Tab` para alternar o foco e as setas para selecionar um salto. A tabela
mostra o último RTT, a média das amostras recentes e a perda acumulada do
salto. Cada salto tem seu próprio gráfico. A perda intermediária pode
refletir limitação de respostas ICMP no roteador.

O gráfico em Braille identifica o IP sondado e o horário local de início
da última sondagem. Em terminais estreitos, `Tab` troca a lista visível.

A curva fica centralizada horizontalmente enquanto preenche a área disponível. A amostra mais recente fica à direita da sequência e as antigas perdem intensidade.

Projeto independente. Licença MIT.

No menu principal, use as setas e Enter para abrir Opções, Ajuda, Limpar lista ou Sair. Esc volta um nível no menu.
Em Opções, use ←/→ para alternar entre Discreto, Drácula, Nord, Gruvbox e Terminal ou ajustar o intervalo da sessão. As paletas personalizadas usam terminais de 256 cores. Limpar lista pede confirmação antes de remover todos os alvos. Ao lado da curva espelhada, o painel exibe as últimas sondagens do alvo ou salto, com horário, RTT ou falha.
