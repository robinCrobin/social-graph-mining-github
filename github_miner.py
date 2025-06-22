import os
import time
import json
import csv
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
from tqdm import tqdm
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_miner.log'),
        logging.StreamHandler()
    ]
)

class GitHubMiner:
    def __init__(self, 
                 tokens: List[str],
                 repo_owner: str = "numpy",
                 repo_name: str = "numpy",
                 requests_per_token: int = 2500,
                 sleep_between_requests: float = 0.8,
                 output_dir: str = "data"):
        
        self.tokens = tokens
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.requests_per_token = requests_per_token
        self.sleep_between_requests = sleep_between_requests
        self.output_dir = output_dir
        
        self.current_token_index = 0
        self.current_token_requests = 0
        
        self.graphql_url = "https://api.github.com/graphql"
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.headers = {
            "Authorization": f"Bearer {self.get_current_token()}",
            "Content-Type": "application/json"
        }
        
        logging.info(f"GitHubMiner inicializado para {repo_owner}/{repo_name}")
        logging.info(f"Tokens disponíveis: {len(self.tokens)}")
        logging.info(f"Requests por token: {self.requests_per_token}")
        
    def get_current_token(self) -> str:
        return self.tokens[self.current_token_index]
    
    def rotate_token(self):
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        self.current_token_requests = 0
        self.headers["Authorization"] = f"Bearer {self.get_current_token()}"
        logging.info(f"Token rotacionado para índice {self.current_token_index}")
    
    def check_rate_limit(self):
        if self.current_token_requests >= self.requests_per_token:
            logging.info(f"Rate limit atingido para token {self.current_token_index}")
            self.rotate_token()
        
        time.sleep(self.sleep_between_requests)
        self.current_token_requests += 1
    
    def make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        self.check_rate_limit()
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.graphql_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        logging.error(f"GraphQL errors: {data['errors']}")
                        return None
                    return data
                elif response.status_code in [502, 503, 504]:
                    # Erros temporários do servidor - tentar novamente
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                        logging.warning(f"Erro {response.status_code} (tentativa {attempt + 1}/{max_retries}). Aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(f"HTTP Error {response.status_code} após {max_retries} tentativas: {response.text}")
                        return None
                else:
                    logging.error(f"HTTP Error {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    logging.warning(f"Exceção de rede (tentativa {attempt + 1}/{max_retries}): {e}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"Request exception após {max_retries} tentativas: {e}")
                    return None
        
        return None
    
    def get_issues_query(self) -> str:
        return """
        query($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            issues(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                number
                title
                body
                state
                createdAt
                updatedAt
                closedAt
                author {
                  login
                }
                assignees(first: 10) {
                  nodes {
                    login
                  }
                }
                labels(first: 20) {
                  nodes {
                    name
                  }
                }
                comments {
                  totalCount
                }
                reactions {
                  totalCount
                }
              }
            }
          }
        }
        """
    
    def get_pull_requests_query(self) -> str:
        return """
        query($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            pullRequests(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}, states: [OPEN, CLOSED, MERGED]) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                number
                title
                body
                state
                createdAt
                updatedAt
                closedAt
                mergedAt
                merged
                author {
                  login
                }
                assignees(first: 10) {
                  nodes {
                    login
                  }
                }
                labels(first: 20) {
                  nodes {
                    name
                  }
                }
                comments {
                  totalCount
                }
                reactions {
                  totalCount
                }
                reviews {
                  totalCount
                }
                additions
                deletions
                changedFiles
              }
            }
          }
        }
        """
    
    def get_comments_query(self) -> str:
        return """
        query($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            issues(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                number
                title
                comments(first: 100) {
                  nodes {
                    id
                    body
                    createdAt
                    updatedAt
                    author {
                      login
                    }
                    reactions {
                      totalCount
                    }
                  }
                }
              }
            }
          }
        }
        """
    
    def get_reviews_query(self) -> str:
        return """
        query($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            pullRequests(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                number
                title
                reviews(first: 100) {
                  nodes {
                    id
                    body
                    state
                    createdAt
                    updatedAt
                    author {
                      login
                    }
                    comments {
                      totalCount
                    }
                  }
                }
              }
            }
          }
        }
        """
    
    def save_to_csv(self, data: List[Dict], filename: str, mode: str = 'a'):  
        if not data:
            return
            
        filepath = os.path.join(self.output_dir, filename)
        file_exists = os.path.exists(filepath)
        
        df = pd.DataFrame(data)
        
        df.to_csv(filepath, mode=mode, index=False, header=not file_exists, encoding='utf-8')
        
        logging.info(f"Salvos {len(data)} registros em {filename}")
    
    def mine_issues(self, save_batch_size: int = 1000) -> int:
        logging.info("Iniciando mineração de Issues...")
        
        cursor = None
        total_issues = 0
        batch_data = []
        
        while True:
            variables = {
                "owner": self.repo_owner,
                "name": self.repo_name,
                "cursor": cursor
            }
            
            response = self.make_graphql_request(self.get_issues_query(), variables)
            
            if not response or not response.get("data"):
                break
                
            issues_data = response["data"]["repository"]["issues"]
            
            for issue in issues_data["nodes"]:
                issue_record = {
                    "id": issue["id"],
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue["body"][:1000] if issue["body"] else "",  # Limitar tamanho
                    "state": issue["state"],
                    "created_at": issue["createdAt"],
                    "updated_at": issue["updatedAt"],
                    "closed_at": issue["closedAt"],
                    "author": issue["author"]["login"] if issue["author"] else "",
                    "assignees": ",".join([a["login"] for a in issue["assignees"]["nodes"]]),
                    "labels": ",".join([l["name"] for l in issue["labels"]["nodes"]]),
                    "comments_count": issue["comments"]["totalCount"],
                    "reactions_count": issue["reactions"]["totalCount"]
                }
                batch_data.append(issue_record)
                total_issues += 1
            
            if len(batch_data) >= save_batch_size:
                self.save_to_csv(batch_data, "issues.csv")
                batch_data = []
            
            page_info = issues_data["pageInfo"]
            if not page_info["hasNextPage"]:
                break
                
            cursor = page_info["endCursor"]
            logging.info(f"Issues processadas: {total_issues}")
        
        if batch_data:
            self.save_to_csv(batch_data, "issues.csv")
        
        logging.info(f"Mineração de Issues concluída. Total: {total_issues}")
        return total_issues
    
    def mine_pull_requests(self, save_batch_size: int = 1000) -> int:
        logging.info("Iniciando mineração de Pull Requests...")
        
        cursor = None
        total_prs = 0
        batch_data = []
        
        while True:
            variables = {
                "owner": self.repo_owner,
                "name": self.repo_name,
                "cursor": cursor
            }
            
            response = self.make_graphql_request(self.get_pull_requests_query(), variables)
            
            if not response or not response.get("data"):
                break
                
            prs_data = response["data"]["repository"]["pullRequests"]
            
            for pr in prs_data["nodes"]:
                pr_record = {
                    "id": pr["id"],
                    "number": pr["number"],
                    "title": pr["title"],
                    "body": pr["body"][:1000] if pr["body"] else "",  # Limitar tamanho
                    "state": pr["state"],
                    "created_at": pr["createdAt"],
                    "updated_at": pr["updatedAt"],
                    "closed_at": pr["closedAt"],
                    "merged_at": pr["mergedAt"],
                    "merged": pr["merged"],
                    "author": pr["author"]["login"] if pr["author"] else "",
                    "assignees": ",".join([a["login"] for a in pr["assignees"]["nodes"]]),
                    "labels": ",".join([l["name"] for l in pr["labels"]["nodes"]]),
                    "comments_count": pr["comments"]["totalCount"],
                    "reactions_count": pr["reactions"]["totalCount"],
                    "reviews_count": pr["reviews"]["totalCount"],
                    "additions": pr["additions"],
                    "deletions": pr["deletions"],
                    "changed_files": pr["changedFiles"]
                }
                batch_data.append(pr_record)
                total_prs += 1
            
            if len(batch_data) >= save_batch_size:
                self.save_to_csv(batch_data, "pull_requests.csv")
                batch_data = []
            
            page_info = prs_data["pageInfo"]
            if not page_info["hasNextPage"]:
                break
                
            cursor = page_info["endCursor"]
            logging.info(f"Pull Requests processados: {total_prs}")
        
        if batch_data:
            self.save_to_csv(batch_data, "pull_requests.csv")
        
        logging.info(f"Mineração de Pull Requests concluída. Total: {total_prs}")
        return total_prs
    
    def mine_comments(self, save_batch_size: int = 1000) -> int:
        logging.info("Iniciando mineração de Comments...")
        
        cursor = None
        total_comments = 0
        batch_data = []
        
        while True:
            variables = {
                "owner": self.repo_owner,
                "name": self.repo_name,
                "cursor": cursor
            }
            
            response = self.make_graphql_request(self.get_comments_query(), variables)
            
            if not response or not response.get("data"):
                break
                
            comments_data = response["data"]["repository"]["issues"]
            
            for issue in comments_data["nodes"]:
                for comment in issue["comments"]["nodes"]:
                    comment_record = {
                        "id": comment["id"],
                        "body": comment["body"][:1000] if comment["body"] else "",  # Limitar tamanho
                        "created_at": comment["createdAt"],
                        "updated_at": comment["updatedAt"],
                        "author": comment["author"]["login"] if comment["author"] else "",
                        "issue_number": issue["number"],
                        "issue_title": issue["title"],
                        "reactions_count": comment["reactions"]["totalCount"]
                    }
                    batch_data.append(comment_record)
                    total_comments += 1

            if len(batch_data) >= save_batch_size:
                self.save_to_csv(batch_data, "comments.csv")
                batch_data = []
            
            page_info = comments_data["pageInfo"]
            if not page_info["hasNextPage"]:
                break
                
            cursor = page_info["endCursor"]
            logging.info(f"Comments processados: {total_comments}")
        
        if batch_data:
            self.save_to_csv(batch_data, "comments.csv")
        
        logging.info(f"Mineração de Comments concluída. Total: {total_comments}")
        return total_comments
    
    def mine_reviews(self, save_batch_size: int = 1000) -> int:
        logging.info("Iniciando mineração de Reviews...")
        
        cursor = None
        total_reviews = 0
        batch_data = []
        
        while True:
            variables = {
                "owner": self.repo_owner,
                "name": self.repo_name,
                "cursor": cursor
            }
            
            response = self.make_graphql_request(self.get_reviews_query(), variables)
            
            if not response or not response.get("data"):
                break
                
            prs_data = response["data"]["repository"]["pullRequests"]
            
            for pr in prs_data["nodes"]:
                for review in pr["reviews"]["nodes"]:
                    review_record = {
                        "id": review["id"],
                        "body": review["body"][:1000] if review["body"] else "",  # Limitar tamanho
                        "state": review["state"],
                        "created_at": review["createdAt"],
                        "updated_at": review["updatedAt"],
                        "author": review["author"]["login"] if review["author"] else "",
                        "pr_number": pr["number"],
                        "pr_title": pr["title"],
                        "comments_count": review["comments"]["totalCount"]
                    }
                    batch_data.append(review_record)
                    total_reviews += 1
            
            if len(batch_data) >= save_batch_size:
                self.save_to_csv(batch_data, "reviews.csv")
                batch_data = []
            
            page_info = prs_data["pageInfo"]
            if not page_info["hasNextPage"]:
                break
                
            cursor = page_info["endCursor"]
            logging.info(f"Reviews processados: {total_reviews}")
        
        if batch_data:
            self.save_to_csv(batch_data, "reviews.csv")
        
        logging.info(f"Mineração de Reviews concluída. Total: {total_reviews}")
        return total_reviews
    
    def mine_all_data(self):
        start_time = datetime.now()
        logging.info("=== INICIANDO MINERAÇÃO COMPLETA ===")
        
        results = {}
        
        try:
            results["issues"] = self.mine_issues()
            
            results["pull_requests"] = self.mine_pull_requests()
            
            results["comments"] = self.mine_comments()
            
            results["reviews"] = self.mine_reviews()
            
        except Exception as e:
            logging.error(f"Erro durante a mineração: {e}")
            raise
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logging.info("=== MINERAÇÃO CONCLUÍDA ===")
        logging.info(f"Duração total: {duration}")
        logging.info(f"Issues: {results.get('issues', 0)}")
        logging.info(f"Pull Requests: {results.get('pull_requests', 0)}")
        logging.info(f"Comments: {results.get('comments', 0)}")
        logging.info(f"Reviews: {results.get('reviews', 0)}")
        logging.info(f"Total de requests: {self.current_token_requests}")
        
        return results 