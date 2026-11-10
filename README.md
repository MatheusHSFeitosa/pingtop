# PINGTOOLs

Monitor de ping para Linux com interface de terminal inspirada no btop. Acompanhe até 32 alvos em paralelo, com latência da última resposta, percentual de perda e histórico visual por alvo.

## Como rodar

Requer Python 3.10+, um terminal com suporte a UTF-8 e o comando `ping` do iputils (pacote `iputils-ping` no Debian/Ubuntu).

```sh
git clone https://github.com/MatheusHSFeitosa/pingtools.git
cd pingtools
./pingtools 127.0.0.1 1.1.1.1 example.com
```

Aceita IPv4, IPv6 e nomes de host. Use `-i 2` para definir um intervalo de dois segundos, ou abra sem argumentos e adicione os alvos na interface.

| Tecla | Ação |
| --- | --- |
| ↑ / ↓ | Selecionar alvo e ver seu histórico |
| a | Adicionar alvo |
| d | Remover alvo selecionado |
| q / Esc | Sair |

A perda é acumulada desde a adição do alvo. O gráfico exibe até 60 amostras recentes, ajusta a escala ao maior valor exibido e marca amostras sem latência com `×`. O estado `ERRO` indica falha na execução ou na resolução do alvo e fica fora do cálculo de perda.

Projeto independente. Licença MIT.
