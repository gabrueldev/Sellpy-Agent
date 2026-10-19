
<img width="600" height="700" alt="logosellpycorporativo" src="https://github.com/user-attachments/assets/466f29f4-8783-47e4-8e86-a0398285d5e4" />

# Sellpy

![CI](https://github.com/gabrueldev/Sellpy-Agent/actions/workflows/main.yml/badge.svg)

### Já pensou em ganhar uma ajudinha na hora da venda?

**A Sellpy veio para resolver isso com poucos cliques no seu WhatsApp!** Com uma *IA integrada*, ela anota suas vendas e gastos, suas tarefas, ideias e muito mais com **muito pouco**!

Basta dizer:

    "gastei 16 em salgado"

ou

    "27 compras"

e ela já anota como "27 reais em compras", separando por categorias. Assim você vê **quanto por cento da sua renda vai para cada coisa** e controla seu mês.

## O que a Sellpy faz

| Você manda | A Sellpy faz |
|---|---|
| "vendi 3 bolos por 90" | Registra um ganho de R$ 90,00 em vendas |
| "gastei 16 em salgado" | Registra um gasto de R$ 16,00 em alimentação |
| "quanto gastei esse mês?" | Mostra ganhos, gastos, saldo e o % de cada categoria |
| "quero juntar 2000 até dezembro" | Cria uma meta. Cada venda nova soma nela, e a Sellpy calcula em quantos dias você chega lá no ritmo atual |
| "me lembra amanhã às 9h de pagar o fornecedor" | Anota a tarefa e **manda a mensagem de lembrete** no WhatsApp na hora marcada |
| "anota a ideia de vender brigadeiro de pistache" | Salva uma nota |
| "apaga o último gasto, digitei errado" | Lista e apaga |

Cada número de WhatsApp tem seus próprios dados: um usuário nunca vê os dados de outro.

## Teste na sua máquina

Não tem demo online: o projeto roda na sua máquina, com a sua chave da IA. Leva uns 3 minutos.

**Você vai precisar de:** Python 3.12+ e uma chave da API da Anthropic ([console.anthropic.com](https://console.anthropic.com) → API Keys). Com o Claude Haiku, cada mensagem custa uma fração de centavo.

    git clone https://github.com/gabrueldev/Sellpy-Agent.git
    cd Sellpy-Agent
    pip install -r requirements.txt
    cp .env.example .env      # cole sua chave em ANTHROPIC_API_KEY
    uvicorn main:app --reload

Abra **http://localhost:8000**. Vai aparecer um chat no estilo WhatsApp, com sugestões de mensagens para clicar. Ele usa a mesma IA e as mesmas ferramentas da versão de WhatsApp. O banco é um SQLite criado automaticamente, então não precisa instalar mais nada.

Quer ver funcionando sem nenhuma chave? Os testes simulam a IA e mostram o fluxo inteiro:

    pytest -v

Com Docker (sobe o Postgres junto):

    docker compose up --build

## Como funciona

```
WhatsApp ──► Meta Cloud API ──► POST /webhook/whatsapp ──┐
                                                         ├──► agente (Claude + ferramentas) ──► banco
Navegador ─────────────────────► POST /demo/chat ────────┘
                                                                  │
worker de lembretes (a cada minuto) ──► tarefas vencidas ──► Meta Cloud API ──► WhatsApp
```

O agente usa **tool use** da API da Anthropic. A IA não inventa números: para registrar, somar ou listar, ela chama funções Python (`tools/`) que leem e gravam no banco, e responde com base no resultado delas.

## Tecnologias

+ Python 3.12 + FastAPI
+ Claude (Anthropic) com tool use e schemas `strict`
+ WhatsApp Cloud API (Meta)
+ SQLAlchemy + PostgreSQL (SQLite no desenvolvimento)
+ Docker Compose
+ Pytest | 25 testes, com a IA simulada (os testes não gastam nada)
+ CI com GitHub Actions

## Segurança e custo

+ O webhook confere a assinatura `X-Hub-Signature-256` da Meta, então ninguém consegue se passar pelo WhatsApp.
+ Mensagens repetidas (a Meta reenvia quando demora) são respondidas uma vez só.
+ Usa o **Claude Haiku**, o modelo mais barato, com esforço baixo. A IA só cobra quando alguém manda mensagem: **parada, custa zero**.
+ Limite de mensagens por dia para cada usuário, para cada visitante da demo e para a demo inteira. Todos configuráveis no `.env`.

## Colocando no ar (opcional)

O projeto já vem pronto para deploy gratuito, caso você queira um link público.

1. **Banco:** crie um Postgres gratuito no [Neon](https://neon.tech) e copie a connection string.
2. **Servidor:** no [Render](https://render.com), escolha *New > Blueprint* e selecione este repositório. O `render.yaml` já configura tudo no plano free, que dorme quando ninguém usa. Preencha `DATABASE_URL` e `ANTHROPIC_API_KEY`.
3. **Custo da IA:** no console da Anthropic, defina um limite de gasto mensal baixo.

A demo já funciona aqui. O WhatsApp é opcional:

4. Em [developers.facebook.com](https://developers.facebook.com), crie um app do tipo *Business* e adicione o produto **WhatsApp**. A Meta dá um número de teste.
5. Em *API Setup*, copie o token e o *Phone number ID* para `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`. O *App Secret* (em *App settings > Basic*) vai em `WHATSAPP_APP_SECRET`.
6. Em *Configuration > Webhook*, use `https://SEU-APP.onrender.com/webhook/whatsapp`, coloque o mesmo `WHATSAPP_VERIFY_TOKEN` do Render e assine o campo **messages**.
7. Cadastre seu número em *API Setup > To* e mande um "oi" para o número de teste.

> O número de teste da Meta só conversa com até 5 números cadastrados, e o token temporário expira em 24h. Para algo permanente, gere um token de *System User*. Lembretes por WhatsApp só chegam se a pessoa falou com a Sellpy nas últimas 24h, que é uma regra da Meta para mensagens livres.

Copyright &copy; 2026 GabrielRodrigues
