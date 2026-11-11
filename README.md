# PINGTOP

Monitor de ping para Linux com interface de terminal inspirada no [btop](https://github.com/aristocratos/btop). Acompanhe a latência, a perda e o histórico de até 1.024 alvos, com até 32 pings simultâneos.

## Instalar no Linux

Requer Python 3.10+, um terminal com suporte a UTF-8 e o comando `ping` do iputils (pacote `iputils-ping` no Debian/Ubuntu).

No Ubuntu, Debian ou Pop!_OS, instale as ferramentas necessárias.

```sh
sudo apt update
sudo apt install git python3 iputils-ping iproute2 traceroute dnsutils snmp
```

Clone o projeto e abra o painel.

```sh
git clone https://github.com/MatheusHSFeitosa/pingtop.git
cd pingtop
./pingtop 127.0.0.1 1.1.1.1 example.com
```

### Usar o comando `pingtop` em qualquer pasta

Dentro da pasta clonada, crie um atalho para o executável.

```sh
mkdir -p ~/.local/bin
ln -s "$PWD/pingtop" ~/.local/bin/pingtop
export PATH="$HOME/.local/bin:$PATH"
pingtop 8.8.8.8
```

Para manter o PATH em sessões futuras, inclua a linha
`export PATH="$HOME/.local/bin:$PATH"` em `~/.profile` caso ela ainda
não esteja configurada. Mantenha a pasta clonada no mesmo lugar.

### Atualizar

Entre na pasta onde clonou o projeto e execute.

```sh
cd /caminho/para/pingtop
git pull --ff-only
pingtop
```

O atalho passa a usar a versão atualizada.

## Windows x64

Baixe `pingtop.exe` em **Assets** na
[prévia para Windows](https://github.com/MatheusHSFeitosa/pingtop/releases/tag/v0.13.0-windows.3).
Abra o PowerShell na pasta do arquivo e execute.

```powershell
.\pingtop.exe 8.8.8.8
.\pingtop.exe 192.168.1.0/24
```

O executável pode ser aberto sem argumentos para adicionar alvos pela interface.
A interface interativa ainda aguarda validação completa no Windows Terminal.
Para atualizar, feche o programa e substitua o executável pelo da nova versão.

## Exemplos de uso

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
| i | Abrir detalhes da rede local |
| g | Abrir consultas SNMP GET, BULK e WALK |
| n | Abrir NSLOOKUP |
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
opções definem a família inicial para alvos adicionados com `a`. Pressione
`v` no painel para alternar entre Auto, IPv4, IPv6 e IPv4+IPv6 para as
próximas inclusões. No modo Auto, URLs carregam as duas famílias disponíveis.

A lista agrupa os IPs sob o hostname da URL. URLs com o mesmo hostname
compartilham um grupo, pois o caminho e a porta não fazem parte do ping.
IPs informados diretamente ficam separados.

## Mouse

Em terminais com suporte a eventos de mouse, clique em um alvo ou salto para
selecioná-lo e use a roda sobre a lista para navegar. Os atalhos nas molduras
e no rodapé também aceitam clique. No menu, clique em uma opção para abrir
ou alterar seu valor.

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

## Rede local

O painel mostra a interface prioritária, endereços, gateway e DNS. Pressione
`i` para abrir a árvore de interfaces, inclusive em terminais estreitos.
A configuração é atualizada a cada dez segundos. No Linux, os endereços e
rotas vêm do comando `ip`, e o DNS vem do `resolvectl` ou de
`/etc/resolv.conf`.

## SNMP

Abra **Esc → SNMP**, pressione `g` ou clique em **g SNMP** para consultar o equipamento selecionado.
No campo **Operação**, use ←/→ para escolher.

- **GET** consulta um objeto, começando pelo OID `sysDescr.0`
  (`.1.3.6.1.2.1.1.1.0`).
- **BULK** executa GETBULK a partir do OID informado. O campo **Repetições**
  controla o máximo de objetos retornados na requisição, de 1 a 100.
- **WALK** percorre a árvore completa acessível a partir da raiz informada.
  A raiz `.1` percorre os objetos acessíveis ao usuário ou à community.
  Para limitar a uma subárvore, informe sua raiz numérica.

Ao mudar de GET para BULK/WALK, o OID inicial padrão muda para `.1`.
Use Tab para alternar campos e Enter para consultar. Durante o WALK, as
respostas aparecem no painel conforme chegam. PgUp/PgDn rolam o resultado,
Ctrl+X interrompe a consulta e preserva os resultados já coletados, e Esc
interrompe e fecha o painel. O WALK prossegue até terminar, ocorrer um erro
ou você cancelar.

Em SNMP v2c, informe a community. Em SNMP v3, escolha o usuário, nível de
segurança e os protocolos e senhas exigidos pelo nível selecionado.
Os campos sensíveis aparecem ocultos e as configurações duram a sessão.
Requer `snmpget`, `snmpbulkget` e `snmpwalk`, disponíveis no pacote `snmp`
no Debian/Ubuntu.

## NSLOOKUP

Pressione `n` ou clique em **n DNS** para abrir a consulta. O alvo selecionado
preenche o campo. Use Tab para alternar para **Servidor DNS** e digite um IP
ou hostname, ou deixe vazio para usar o DNS do sistema. Delete limpa o campo
ativo. O servidor escolhido fica disponível até sair do PINGTOP. Enter consulta o DNS, as setas
rolam o resultado e Esc fecha o painel. Domínios retornam registros de
endereço disponíveis, e IPs fazem consulta reversa. Requer o comando
`nslookup` (pacote `dnsutils` no Debian/Ubuntu).

## Tracert

Instale o pacote opcional `traceroute` para usar o Tracert ICMP. Pressione
`t` para sondar continuamente a rota do alvo selecionado, até 24 saltos.
Use `Tab` para alternar o foco e as setas para selecionar um salto. A tabela
mostra o número do salto, o nome ou IP três RTTs por ciclo em milissegundos e a perda acumulada das sondagens por salto.
`*` indica uma tentativa sem resposta. Cada salto tem seu próprio gráfico.

## Terminal e aparência

Em uma janela de pelo menos 96 colunas por 20 linhas, os painéis de rede local,
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
