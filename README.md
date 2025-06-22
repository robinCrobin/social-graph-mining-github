# 🔍 GitHub Data Miner - NumPy Repository

Sistema completo de mineração de dados do repositório NumPy no GitHub usando GraphQL API.

## 🚀 Funcionalidades

- **Mineração Completa**: Issues, Pull Requests, Comments e Reviews
- **GraphQL API**: Consultas otimizadas com paginação automática
- **Rotação de Tokens**: Suporte a múltiplos tokens para evitar rate limit
- **Salvamento Incremental**: Dados salvos em CSV durante a mineração
- **Rate Limit Management**: Sleep automático entre requests
- **Logging Completo**: Logs detalhados de todo o processo
- **Exploração de Dados**: Scripts para análise dos dados minerados

## 📋 Pré-requisitos

1. **Python 3.8+**
2. **Tokens do GitHub**: Crie tokens em [GitHub Settings](https://github.com/settings/tokens)
   - Permissões necessárias: `public_repo`, `read:org`
3. **Dependências Python**: Listadas em `requirements.txt`

## ⚙️ Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Tokens

1. Copie o arquivo de exemplo:
   ```bash
   cp env_example.txt .env
   ```

2. Edite o arquivo `.env` com seus tokens:
   ```env
   GITHUB_TOKEN_1=ghp_seu_token_aqui_1
   GITHUB_TOKEN_2=ghp_seu_token_aqui_2
   GITHUB_TOKEN_3=ghp_seu_token_aqui_3
   GITHUB_TOKEN_4=ghp_seu_token_aqui_4
   
   REPO_OWNER=numpy
   REPO_NAME=numpy
   REQUESTS_PER_TOKEN=2500
   SLEEP_BETWEEN_REQUESTS=0.8
   ```


## 🎯 Uso

### Mineração Completa

```bash
python main.py
```

Este comando irá:
- Carregar os tokens configurados
- Minerar Issues, Pull Requests, Comments e Reviews
- Salvar os dados em arquivos CSV na pasta `data/`
- Gerar logs detalhados em `github_miner.log`

### Exploração dos Dados

```bash
python data_explorer.py
```

Este comando irá:
- Carregar os dados minerados
- Mostrar estatísticas e resumos
- Identificar top contribuidores
- Analisar tendências temporais
- Gerar relatório completo

## 📊 Estrutura dos Dados

### Issues (`data/issues.csv`)
- `id`, `number`, `title`, `body`, `state`
- `created_at`, `updated_at`, `closed_at`
- `author`, `assignees`, `labels`
- `comments_count`, `reactions_count`

### Pull Requests (`data/pull_requests.csv`)
- `id`, `number`, `title`, `body`, `state`
- `created_at`, `updated_at`, `closed_at`, `merged_at`
- `merged`, `author`, `assignees`, `labels`
- `comments_count`, `reactions_count`, `reviews_count`
- `additions`, `deletions`, `changed_files`

### Comments (`data/comments.csv`)
- `id`, `body`, `created_at`, `updated_at`
- `author`, `issue_number`, `issue_title`
- `reactions_count`

### Reviews (`data/reviews.csv`)
- `id`, `body`, `state`, `created_at`, `updated_at`
- `author`, `pr_number`, `pr_title`
- `comments_count`

## ⚡ Configurações de Performance

### Rate Limit
- **Limite do GitHub**: 5.000 requests/hora com token
- **Configuração padrão**: 2.500 requests por token
- **Sleep entre requests**: 0.8 segundos
- **Rotação automática**: Quando atingir o limite

### Otimizações
- **Paginação**: 100 registros por página
- **Salvamento em lotes**: 1.000 registros por vez
- **Campos limitados**: Body limitado a 1.000 caracteres
- **Timeout**: 30 segundos por request

## 📁 Estrutura do Projeto

```
social-graph-mining-github/
├── main.py                 # Script principal
├── github_miner.py         # Classe principal do minerador
├── data_explorer.py        # Explorador de dados
├── requirements.txt        # Dependências
├── env_example.txt         # Exemplo de configuração
├── .env                    # Configuração (criar manualmente)
├── data/                   # Dados minerados (CSV)
│   ├── issues.csv
│   ├── pull_requests.csv
│   ├── comments.csv
│   └── reviews.csv
├── github_miner.log        # Logs da mineração
└── data_report.txt         # Relatório gerado
```

## 🔧 Configurações Avançadas

### Alterar Repositório

No arquivo `.env`:
```env
REPO_OWNER=outro_usuario
REPO_NAME=outro_repositorio
```

### Ajustar Rate Limit

No arquivo `.env`:
```env
REQUESTS_PER_TOKEN=2000      # Menor para ser mais conservador
SLEEP_BETWEEN_REQUESTS=1.0   # Mais tempo entre requests
```

### Executar Mineração Parcial

Você pode modificar o `main.py` para executar apenas partes específicas:

```python
# Apenas Issues
results = {"issues": miner.mine_issues()}

# Apenas Pull Requests
results = {"pull_requests": miner.mine_pull_requests()}

# Apenas Comments
results = {"comments": miner.mine_comments()}

# Apenas Reviews
results = {"reviews": miner.mine_reviews()}
```

## 🛠️ Troubleshooting

### Erro de Token
```
❌ Erro: Nenhum token encontrado!
```
**Solução**: Verifique se o arquivo `.env` existe e contém os tokens válidos.

### Rate Limit Atingido
```
HTTP Error 403: rate limit exceeded
```
**Solução**: O sistema deve rotacionar automaticamente. Se persistir, aumente o `SLEEP_BETWEEN_REQUESTS`.

### Timeout de Conexão
```
Request exception: timeout
```
**Solução**: Problema de rede. O sistema tentará continuar automaticamente.

### Dados Corrompidos
Se algum arquivo CSV ficar corrompido, você pode:
1. Deletar o arquivo específico
2. Executar novamente o `main.py` (continuará de onde parou)

## 📝 Logs

Todos os logs são salvos em `github_miner.log`:
- Informações de progresso
- Rotação de tokens
- Erros e exceções
- Estatísticas de mineração
