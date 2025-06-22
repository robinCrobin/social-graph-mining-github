#!/usr/bin/env python3
"""
Script principal para mineração de dados do GitHub
Repositório: numpy/numpy

Uso:
    python main.py

Configuração:
    1. Copie env_example.txt para .env
    2. Configure seus tokens do GitHub no arquivo .env
    3. Execute o script
"""

import os
import sys
from dotenv import load_dotenv
from github_miner import GitHubMiner

def load_tokens_from_env() -> list:
    """Carrega tokens do arquivo .env"""
    tokens = []
    
    # Tentar carregar até 10 tokens
    for i in range(1, 11):
        token = os.getenv(f'GITHUB_TOKEN_{i}')
        if token:
            tokens.append(token)
    
    return tokens

def main():
    """Função principal"""
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Carregar tokens
    tokens = load_tokens_from_env()
    
    if not tokens:
        print("❌ Erro: Nenhum token encontrado!")
        print("📝 Instruções:")
        print("1. Copie env_example.txt para .env")
        print("2. Configure seus tokens do GitHub no arquivo .env")
        print("3. Crie tokens em: https://github.com/settings/tokens")
        print("4. Permissões necessárias: public_repo, read:org")
        sys.exit(1)
    
    print(f"✅ {len(tokens)} token(s) carregado(s)")
    
    # Configurações
    repo_owner = os.getenv('REPO_OWNER', 'numpy')
    repo_name = os.getenv('REPO_NAME', 'numpy')
    requests_per_token = int(os.getenv('REQUESTS_PER_TOKEN', '2500'))
    sleep_between_requests = float(os.getenv('SLEEP_BETWEEN_REQUESTS', '0.8'))
    
    print(f"🎯 Repositório: {repo_owner}/{repo_name}")
    print(f"⚡ Requests por token: {requests_per_token}")
    print(f"⏱️  Sleep entre requests: {sleep_between_requests}s")
    
    # Criar minerador
    miner = GitHubMiner(
        tokens=tokens,
        repo_owner=repo_owner,
        repo_name=repo_name,
        requests_per_token=requests_per_token,
        sleep_between_requests=sleep_between_requests
    )
    
    # Executar mineração
    try:
        print("\n🚀 Iniciando mineração...")
        results = miner.mine_all_data()
        
        print("\n✅ Mineração concluída com sucesso!")
        print(f"📊 Resultados:")
        print(f"   - Issues: {results.get('issues', 0)}")
        print(f"   - Pull Requests: {results.get('pull_requests', 0)}")
        print(f"   - Comments: {results.get('comments', 0)}")
        print(f"   - Reviews: {results.get('reviews', 0)}")
        print(f"\n📁 Dados salvos em: ./data/")
        
    except KeyboardInterrupt:
        print("\n⏹️  Mineração interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante a mineração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 