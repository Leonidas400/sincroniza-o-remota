# Sync Files

Sistema de sincronização de arquivos em tempo real entre máquinas usando FastAPI + WebSocket.

## Arquitetura

```
┌──────────────────────────────┐
│  Máquina A (host)            │
│  ngrok + Servidor + Client   │
│  pasta: ~/Documentos/sync    │
└──────────────┬───────────────┘
               │ túnel ngrok
┌──────────────▼───────────────┐
│  Máquina B (peer)            │
│  apenas Client               │
│  pasta: ~/Documentos/sync    │
└──────────────────────────────┘
```

O **servidor** roda em uma máquina e é exposto via ngrok. Os **clients** conectam ao servidor e sincronizam uma pasta local.

## Requisitos

- Python 3.11+
- ngrok (apenas na máquina do servidor)

## Setup da Máquina do Servidor (Host)

```bash
# Instalar dependências
pip install -r requirements-servidor.txt
pip install -r requirements-cliente.txt

# Configurar .env
cat > .env << EOF
SERVER_HOST=0.0.0.0
SERVER_PORT=4000
STORAGE_DIR=.sync_storage
API_KEY=mvp-senha-facil-2026
SERVER_URL=http://localhost:4000
SYNC_FOLDER=~/Documentos/sync
DEVICE_ID=device-.leonidas
EOF

# Iniciar ngrok (em outro terminal)
ngrok http 4000

# Iniciar servidor
./run.sh server

# Iniciar client (em outro terminal)
./run.sh client
```

Anote o URL do ngrok (ex: `https://abc123.ngrok-free.dev`).

## Setup da Máquina do Peer

Copiar para a máquina do peer apenas:
- `cliente/` (pasta inteira)
- `requirements-cliente.txt`
- `.env`
- `run.sh` (ou `run.bat` no Windows)

```bash
# Instalar dependências
pip install -r requirements-cliente.txt

# Configurar .env
cat > .env << EOF
SERVER_URL=https://URL_DO_NGROK
SYNC_FOLDER=~/Documentos/sync
API_KEY=mvp-senha-facil-2026
DEVICE_ID=device-.nome
EOF

# Iniciar client
./run.sh client
```

## Comandos

| Comando | Descrição |
|---------|-----------|
| `./run.sh server` | Inicia o servidor FastAPI (porta 4000) |
| `./run.sh client` | Inicia o client de sincronização |

## Como Funciona

1. Ao iniciar, o client baixa todos os arquivos do servidor para a pasta local
2. O watcher monitora a pasta e detecta **criações**, **edições** e **deleções**
3. Mudanças locais são enviadas ao servidor via HTTP
4. O servidor broadcast via WebSocket para todos os outros clients conectados
5. Clients remotos recebem a notificação e baixam/deletam o arquivo

## Variáveis de Ambiente (.env)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SERVER_HOST` | `0.0.0.0` | Host do servidor |
| `SERVER_PORT` | `4000` | Porta do servidor |
| `STORAGE_DIR` | `.sync_storage` | Pasta de storage do servidor |
| `API_KEY` | `mvp-senha-facil-2026` | Chave de autenticação |
| `SERVER_URL` | `http://localhost:8000` | URL do servidor (use ngrok URL no peer) |
| `SYNC_FOLDER` | `~/Documentos/sync` | Pasta a ser sincronizada |
| `DEVICE_ID` | `device-<random>` | Identificador único do client |
| `MAX_FILE_SIZE` | `52428800` (50MB) | Tamanho máximo de arquivo |

## Windows

Usar `run.bat` no lugar de `run.sh`:

```bat
run.bat server
run.bat client
```
