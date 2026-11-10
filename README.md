# PINGTOP

Monitor de ping para Linux com interface de terminal inspirada no [btop](https://github.com/aristocratos/btop). Acompanhe a latência, a perda e o histórico de até 1.024 alvos, com até 32 pings simultâneos.

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
| `f` ou `/` | Filtrar por IP ou hostname enquanto digita |
| r | Inverter a ordem dos alvos |
| s | Alternar entre Todos, Com resposta e Sem resposta |
| Delete | Limpar filtro de texto |
| p | Pausar ou retomar o ping contínuo de todos os alvos |
| t | Iniciar ou parar o Tracert do alvo selecionado |
| Tab | Alternar entre a lista de alvos e a de saltos |
| Esc / m | Abrir o menu principal |
| ? | Abrir ou fechar a ajuda |
| q | Sair |

## IPv4, IPv6 e URLs

```sh
pingtop -4 https://example.com/
pingtop -6 https://example.com/
pingtop -4 -6 https://example.com/
```

O PINGTOP sonda o hostname da URL por ICMP. Com `-4` ou `-6`, cada
hostname é resolvido ao carregar e entra no painel com o primeiro IP de
cada família solicitada que estiver disponível. As duas opções juntas
geram dois alvos quando houver endereços das duas famílias. As mesmas
opções se aplicam aos alvos adicionados com `a` durante a sessão.

## Monitoramento

O ping começa automaticamente. A coluna de perda acumula as sondagens desde
a adição do alvo. Quando há espaço, a porcentagem vem acompanhada de um
medidor de quadrados em Alvos monitorados e no Tracert. O estado `ERRO` indica falha na execução ou na resolução do
alvo e fica fora do cálculo de perda.

- O histórico mostra as respostas mais recentes primeiro e usa colunas de
  horário, sequência, TTL e RTT quando há espaço.
  As linhas mais antigas perdem intensidade, e os marcadores de falha
  preservam a cor de alerta.
- O gráfico desenha duas amostras por célula. O modo Micro usa glifos Braille
  com pixels finos. A forma dos pontos depende da fonte ou do terminal. Em
  Opções, selecione Quadrantes para usar blocos de cantos retos.
  A leitura mais recente fica à direita. A escala acompanha os RTTs visíveis
  e as metades espelhadas diferenciam o traçado por cor.
- Em painéis largos, o quadro lateral exibe o último RTT, o mínimo, a média
  e o máximo das amostras visíveis. O medidor acompanha o último RTT e esvazia
  quando a sonda fica sem resposta.

Enter confirma o filtro de texto e Esc restaura o filtro anterior. Os alvos
ocultos continuam sendo sondados. Sem resposta mostra alvos cujo último ping
expirou.

## Tracert

Instale o pacote opcional `traceroute` para usar o Tracert ICMP. Pressione
`t` para sondar continuamente a rota do alvo selecionado, até 24 saltos.
Use `Tab` para alternar o foco e as setas para selecionar um salto. A tabela
mostra o número do salto, o nome ou IP três RTTs por ciclo em milissegundos e a perda acumulada das sondagens por salto.
`*` indica uma tentativa sem resposta. Cada salto tem seu próprio gráfico.

## Terminal e aparência

Em uma janela de pelo menos 96 colunas por 20 linhas, os painéis de detalhes,
alvos, histórico/gráfico e Tracert aparecem juntos. A interface compacta
usa pelo menos 48 colunas por 16 linhas e alterna as listas com `Tab`.

No menu principal, use as setas e Enter para abrir Opções, Ajuda, Limpar lista
ou Sair. Esc volta um nível. Em Opções, use ←/→ para ajustar o intervalo ou
alternar entre Discreto, Drácula, Nord, Gruvbox e Terminal. As paletas
personalizadas usam terminais de 256 cores. Em **Fundo do tema**, use Sim
para aplicar o fundo da paleta ou Não para usar o fundo do terminal. Essa
opção começa em Sim a cada sessão. Limpar lista pede confirmação.

## Testes

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Projeto independente. Licença MIT.

## Windows (prévia)

Baixe `pingtop.exe` na página da versão de teste para Windows x64. Abra o
Windows Terminal na pasta do arquivo e rode:

```powershell
.\pingtop.exe 8.8.8.8
```

A prévia usa o `ping.exe` e o `tracert.exe` nativos. O Tracert usa IPs
numéricos para evitar atrasos com DNS reverso. A aparência dos glifos e o
suporte ao fundo do terminal dependem do console. A interface interativa
ainda precisa ser validada no Windows Terminal.
