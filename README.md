# Sports Court Booking – Plataforma de Agendamento de Quadras

Aplicação distribuída composta por 3 serviços *Python/FastAPI* que permitem
o agendamento de quadras esportivas com cálculo de preço, extras (bola, coletes,
iluminação), checkout com formas de pagamento simuladas (CARD/PIX/BOLETO) e
emissão de fatura PDF.

- **Tecnologias**: Python, FastAPI
- **Banco de dados**: PostgreSQL (Aiven)
- **Autenticação**: Auth0
- **Comunicação entre serviços**: HTTP (REST)
- **Testes**: pytest + coverage (>80% como gate em CI)
- **CI/CD**: GitHub Actions (test → build docker → push Docker Hub)
- **Container**: Dockerfile por serviço; `docker-compose` para desenvolvimento local

## Arquitetura (3 serviços)

1. **Sports-Agenda** – Locais, quadras, *slots* (por hora), marcação de `BOOKED`.
2. **Sports-Booking** – Orquestra reservas: cria/cancela booking, calcula total
   estimado, integra com Agenda e consome callback do Payment.
3. **Sports-Payment** – Checkout, cupons, meios de pagamento simulados, geração de fatura e callback para Booking.

### Fluxo resumido
1) Usuário seleciona quadra/horário → `Sports-Booking` cria *booking* e pede `lock` ao `Sports-Agenda`.  
2) Usuário faz checkout → `Sports-Payment` decide (aprovado/pendente/recusado) e
   chama via **requests** em `Sports-Booking`.  
3) `Sports-Booking` confirma/cancela e informa `Sports-Agenda` para `mark-booked`/`release`.

### Segurança
- Endpoints de usuário protegidos por **Auth0** (Bearer JWT).
- Comunicação entre serviços assinados com **Requests**.

### Rodando localmente (dev)
- Requer Docker e (opcional) `docker-compose` com Postgres local.
- Cada serviço possui seu próprio `README` com variáveis de ambiente e comandos.
