#!/usr/bin/env python3
"""
Script de teste para verificar conectividade com a API do GitHub
"""

import os
import requests
from dotenv import load_dotenv

def test_token(token: str, token_name: str) -> bool:
    """Testa um token específico"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query simples para testar
    query = """
    query {
      viewer {
        login
      }
      rateLimit {
        limit
        remaining
        resetAt
      }
    }
    """
    
    payload = {"query": query}
    
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ {token_name}: Erro GraphQL - {data['errors']}")
                return False
            
            viewer = data["data"]["viewer"]["login"]
            rate_limit = data["data"]["rateLimit"]
            
            print(f"✅ {token_name}: OK")
            print(f"   Usuario: {viewer}")
            print(f"   Rate Limit: {rate_limit['remaining']}/{rate_limit['limit']}")
            print(f"   Reset: {rate_limit['resetAt']}")
            return True
            
        else:
            print(f"❌ {token_name}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {token_name}: Erro de conexão - {e}")
        return False

def test_repository_access(token: str) -> bool:
    """Testa acesso ao repositório NumPy"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      repository(owner: "numpy", name: "numpy") {
        name
        description
        isPrivate
        stargazerCount
        forkCount
        issues(first: 1) {
          totalCount
        }
        pullRequests(first: 1) {
          totalCount
        }
      }
    }
    """
    
    payload = {"query": query}
    
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ Erro ao acessar repositório: {data['errors']}")
                return False
            
            repo = data["data"]["repository"]
            print(f"✅ Acesso ao repositório numpy/numpy: OK")
            print(f"   Nome: {repo['name']}")
            print(f"   Descrição: {repo['description'][:100]}...")
            print(f"   Stars: {repo['stargazerCount']:,}")
            print(f"   Forks: {repo['forkCount']:,}")
            print(f"   Issues: {repo['issues']['totalCount']:,}")
            print(f"   Pull Requests: {repo['pullRequests']['totalCount']:,}")
            return True
            
        else:
            print(f"❌ Erro HTTP ao acessar repositório: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão ao acessar repositório: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🧪 TESTE DE CONECTIVIDADE - GitHub API")
    print("="*50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Carregar tokens
    tokens = []
    for i in range(1, 11):
        token = os.getenv(f'GITHUB_TOKEN_{i}')
        if token:
            tokens.append((token, f'TOKEN_{i}'))
    
    if not tokens:
        print("❌ Nenhum token encontrado no arquivo .env")
        print("\n📝 Instruções:")
        print("1. Copie env_example.txt para .env")
        print("2. Configure seus tokens do GitHub")
        return
    
    print(f"🔍 Testando {len(tokens)} token(s)...\n")
    
    valid_tokens = 0
    
    # Testar cada token
    for token, name in tokens:
        if test_token(token, name):
            valid_tokens += 1
        print()
    
    print("="*50)
    print(f"📊 Resultado: {valid_tokens}/{len(tokens)} tokens válidos")
    
    if valid_tokens > 0:
        print(f"\n🎯 Testando acesso ao repositório numpy/numpy...")
        print("-"*50)
        test_repository_access(tokens[0][0])  # Usar primeiro token válido
        
        print(f"\n✅ Sistema pronto para mineração!")
        print(f"💡 Execute: python main.py")
    else:
        print(f"\n❌ Nenhum token válido encontrado!")
        print(f"🔧 Verifique seus tokens e tente novamente")

if __name__ == "__main__":
    main() 