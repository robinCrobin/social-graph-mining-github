import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from github_miner import GitHubMiner

def quick_test_mining():
    """Executa uma mineração de teste rápida"""
    print("🚀 QUICK START - TESTE DE MINERAÇÃO")
    print("="*50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Carregar tokens
    tokens = []
    for i in range(1, 11):
        token = os.getenv(f'GITHUB_TOKEN_{i}')
        if token:
            tokens.append(token)
    
    if not tokens:
        print("❌ Erro: Nenhum token encontrado!")
        print("GITHUB_TOKEN_1=seu_token_aqui")
        return False
    
    print(f"✅ {len(tokens)} token(s) encontrado(s)")
    
    miner = GitHubMiner(
        tokens=tokens,
        repo_owner="numpy",
        repo_name="numpy",
        requests_per_token=100,
        sleep_between_requests=1.0,
        output_dir="test_data"
    )
    
    print("\n🔍 Executando mineração de teste...")
    print("⚠️  Limitado a 100 requests por token para teste")
    
    try:
        # Minerar apenas uma pequena amostra de cada tipo
        print("\n1️⃣  Minerando Issues (amostra)...")
        issues_count = mine_sample_issues(miner)
        
        print("\n2️⃣  Minerando Pull Requests (amostra)...")
        prs_count = mine_sample_prs(miner)
        
        print("\n3️⃣  Minerando Comments (amostra)...")
        comments_count = mine_sample_comments(miner)
        
        print("\n✅ Teste de mineração concluído!")
        print(f"📊 Resultados:")
        print(f"   - Issues: {issues_count}")
        print(f"   - Pull Requests: {prs_count}")
        print(f"   - Comments: {comments_count}")
        print(f"   - Dados salvos em: ./test_data/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        return False

def mine_sample_issues(miner, max_pages=2):
    """Minera uma amostra pequena de issues"""
    cursor = None
    total_issues = 0
    batch_data = []
    pages_processed = 0
    
    while pages_processed < max_pages:
        variables = {
            "owner": miner.repo_owner,
            "name": miner.repo_name,
            "cursor": cursor
        }
        
        response = miner.make_graphql_request(miner.get_issues_query(), variables)
        
        if not response or not response.get("data"):
            break
            
        issues_data = response["data"]["repository"]["issues"]
        
        for issue in issues_data["nodes"]:
            issue_record = {
                "id": issue["id"],
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created_at": issue["createdAt"],
                "author": issue["author"]["login"] if issue["author"] else "",
                "comments_count": issue["comments"]["totalCount"]
            }
            batch_data.append(issue_record)
            total_issues += 1
        
        # Verificar se há mais páginas
        page_info = issues_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
            
        cursor = page_info["endCursor"]
        pages_processed += 1
        print(f"   Processadas {total_issues} issues...")
    
    # Salvar dados
    if batch_data:
        miner.save_to_csv(batch_data, "sample_issues.csv")
    
    return total_issues

def mine_sample_prs(miner, max_pages=2):
    """Minera uma amostra pequena de PRs"""
    cursor = None
    total_prs = 0
    batch_data = []
    pages_processed = 0
    
    while pages_processed < max_pages:
        variables = {
            "owner": miner.repo_owner,
            "name": miner.repo_name,
            "cursor": cursor
        }
        
        response = miner.make_graphql_request(miner.get_pull_requests_query(), variables)
        
        if not response or not response.get("data"):
            break
            
        prs_data = response["data"]["repository"]["pullRequests"]
        
        for pr in prs_data["nodes"]:
            pr_record = {
                "id": pr["id"],
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "created_at": pr["createdAt"],
                "merged": pr["merged"],
                "author": pr["author"]["login"] if pr["author"] else "",
                "additions": pr["additions"],
                "deletions": pr["deletions"]
            }
            batch_data.append(pr_record)
            total_prs += 1
        
        # Verificar se há mais páginas
        page_info = prs_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
            
        cursor = page_info["endCursor"]
        pages_processed += 1
        print(f"   Processados {total_prs} PRs...")
    
    # Salvar dados
    if batch_data:
        miner.save_to_csv(batch_data, "sample_prs.csv")
    
    return total_prs

def mine_sample_comments(miner, max_pages=1):
    """Minera uma amostra pequena de comments"""
    cursor = None
    total_comments = 0
    batch_data = []
    pages_processed = 0
    
    while pages_processed < max_pages:
        variables = {
            "owner": miner.repo_owner,
            "name": miner.repo_name,
            "cursor": cursor
        }
        
        response = miner.make_graphql_request(miner.get_comments_query(), variables)
        
        if not response or not response.get("data"):
            break
            
        comments_data = response["data"]["repository"]["issueComments"]
        
        for comment in comments_data["nodes"]:
            comment_record = {
                "id": comment["id"],
                "created_at": comment["createdAt"],
                "author": comment["author"]["login"] if comment["author"] else "",
                "issue_number": comment["issue"]["number"],
                "reactions_count": comment["reactions"]["totalCount"]
            }
            batch_data.append(comment_record)
            total_comments += 1
        
        # Verificar se há mais páginas
        page_info = comments_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
            
        cursor = page_info["endCursor"]
        pages_processed += 1
        print(f"   Processados {total_comments} comments...")
    
    # Salvar dados
    if batch_data:
        miner.save_to_csv(batch_data, "sample_comments.csv")
    
    return total_comments

def main():
    print("Teste rápido do sistema de mineração.\n")
    
    # Verificar se é a primeira execução
    if not os.path.exists(".env"):
        print("="*30)       
        print("\n VOCÊ PRECISA:")
        print("1. Criar e abrir o arquivo .env")
        print("2. Substituir 'ghp_your_token_here_1' pelo seu token real")
        print("3. Salvar o arquivo")
        print("4. Executar novamente este script")
        print()
        print("🔗 Como criar tokens: https://github.com/settings/tokens")
        print("   Permissões necessárias: public_repo, read:org")
        return
    
    # Executar teste de mineração
    success = quick_test_mining()
    
    if not success:
        print("\n🔧 TROUBLESHOOTING:")
        print("- Verifique se seus tokens estão corretos no arquivo .env")
        print("- Execute: python test_connection.py")

if __name__ == "__main__":
    main() 