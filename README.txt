CARTA ROYALE — BLACK & GOLD
Jogo de cartas original inspirado em jogos de descarte por cores.

Para testar no computador:
1. Instale Python 3.
2. Abra o terminal dentro desta pasta.
3. Execute: python server.py
4. Abra http://localhost:8765
5. Crie a sala, abra o link TV e entre com 2 a 6 jogadores em abas/dispositivos distintos.

Para celulares na mesma rede Wi-Fi, use o IP local do computador na porta 8765 (libere a porta no firewall se necessário).

Para publicar: crie NOVO repositório e NOVO serviço web no Render, sem mexer no FORTAL CITY.
Start command: python server.py
Nenhuma dependência externa.

REGRAS DA VERSÃO INICIAL:
- 7 cartas por jogador, 2 a 6 jogadores.
- Combine cor ou valor, ou use coringa.
- +2 e +4 obrigam o próximo jogador a comprar e perder a vez; sem empilhamento.
- Compra uma carta e encerra a vez (regra simplificada).
- O botão ÚLTIMA CARTA é um anúncio, ainda sem penalidade por esquecimento.
- O servidor mantém salas na memória: reiniciar o serviço apaga as partidas.
- O administrador recebe chave secreta no navegador que cria a sala.
- Não use dados pessoais reais em nomes de jogadores.
