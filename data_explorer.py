#!/usr/bin/env python3
"""
Script otimizado para explorar dados minerados do GitHub
"""

import os
import pandas as pd
from datetime import datetime
from collections import Counter, defaultdict, deque
import heapq
from itertools import combinations

class DataExplorer:
    """Explorador de dados minerados"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.data = {}
        self.user_interactions = None
        self.user_degrees = None
        self.user_nodes = None
        
    def load_data(self):
        """Carrega todos os arquivos CSV"""
        files = {
            'issues': 'issues.csv',
            'pull_requests': 'pull_requests.csv',
            'comments': 'comments.csv',
            'reviews': 'reviews.csv'
        }
        
        cols_to_load = {
            'issues': ['author', 'assignees', 'number'],
            'pull_requests': ['author', 'assignees', 'number'],
            'comments': ['author', 'issue_number'],
            'reviews': ['author', 'pr_number']
        }
        
        for key, filename in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath, usecols=cols_to_load.get(key, None))
                    self.data[key] = df
                    print(f"✅ {key}: {len(df)} registros carregados")
                except Exception as e:
                    print(f"❌ Erro ao carregar {filename}: {e}")
            else:
                print(f"⚠️  Arquivo não encontrado: {filename}")
    
    def build_interaction_graph(self):
        """Constrói um grafo de interações"""
        if not self.data:
            print("❌ Nenhum dado carregado!")
            return None
            
        interactions = defaultdict(dict)
        degrees = defaultdict(int)
        
        self._preprocess_authors()
        
        self._process_issues(interactions, degrees)
        self._process_pull_requests(interactions, degrees)
        self._process_comments(interactions, degrees)
        self._process_reviews(interactions, degrees)
        
        self.user_interactions = dict(interactions)
        self.user_degrees = dict(degrees)
        self.user_nodes = set(interactions.keys())
        return interactions
    
    def _preprocess_authors(self):
        """Pré-processa autores para acesso rápido"""
        self.issue_authors = {}
        self.pr_authors = {}
        
        if 'issues' in self.data:
            self.issue_authors = dict(zip(
                self.data['issues']['number'],
                self.data['issues']['author']
            ))
        
        if 'pull_requests' in self.data:
            self.pr_authors = dict(zip(
                self.data['pull_requests']['number'],
                self.data['pull_requests']['author']
            ))
    
    def _process_issues(self, interactions, degrees):
        """Processa interações em issues de forma otimizada"""
        if 'issues' not in self.data:
            return
            
        issues_df = self.data['issues']
        issues_df = issues_df[['author', 'assignees']].dropna()
        
        for author, assignees_str in issues_df.itertuples(index=False):
            assignees = [a.strip() for a in assignees_str.split(',') if a.strip()]
            for assignee in assignees:
                interactions[author][assignee] = interactions[author].get(assignee, 0) + 1
                interactions[assignee][author] = interactions[assignee].get(author, 0) + 1
                degrees[author] += 1
                degrees[assignee] += 1
    
    def _process_pull_requests(self, interactions, degrees):
        """Processa interações em pull requests"""
        if 'pull_requests' not in self.data:
            return
            
        prs_df = self.data['pull_requests']
        prs_df = prs_df[['author', 'assignees']].dropna()
        
        for author, assignees_str in prs_df.itertuples(index=False):
            assignees = [a.strip() for a in assignees_str.split(',') if a.strip()]
            for assignee in assignees:
                interactions[author][assignee] = interactions[author].get(assignee, 0) + 1
                interactions[assignee][author] = interactions[assignee].get(author, 0) + 1
                degrees[author] += 1
                degrees[assignee] += 1
    
    def _process_comments(self, interactions, degrees):
        """Processa interações em comentários"""
        if 'comments' not in self.data or not self.issue_authors:
            return
            
        comments_df = self.data['comments']
        comments_df = comments_df[['author', 'issue_number']].dropna()
        
        for author, issue_num in comments_df.itertuples(index=False):
            issue_author = self.issue_authors.get(issue_num)
            if issue_author and issue_author != author:
                interactions[author][issue_author] = interactions[author].get(issue_author, 0) + 1
                interactions[issue_author][author] = interactions[issue_author].get(author, 0) + 1
                degrees[author] += 1
                degrees[issue_author] += 1
    
    def _process_reviews(self, interactions, degrees):
        """Processa interações em reviews"""
        if 'reviews' not in self.data or not self.pr_authors:
            return
            
        reviews_df = self.data['reviews']
        reviews_df = reviews_df[['author', 'pr_number']].dropna()
        
        for author, pr_num in reviews_df.itertuples(index=False):
            pr_author = self.pr_authors.get(pr_num)
            if pr_author and pr_author != author:
                interactions[author][pr_author] = interactions[author].get(pr_author, 0) + 1
                interactions[pr_author][author] = interactions[pr_author].get(author, 0) + 1
                degrees[author] += 1
                degrees[pr_author] += 1
    
    def get_top_influencers(self, top_n=5):
        """Identifica os top_n usuários mais influentes"""
        if self.user_degrees is None:
            self.build_interaction_graph()
        
        if not self.user_degrees:
            return []
        
        return heapq.nlargest(top_n, self.user_degrees.items(), key=lambda x: x[1])
    
    def identify_fragmentation_sources(self):
        """Versão otimizada para identificar fontes de fragmentação"""
        if self.user_interactions is None:
            self.build_interaction_graph()
        
        if not self.user_interactions:
            return []
        
        fragmentation_scores = {}
        
        for user in self.user_interactions:
            neighbors = set(self.user_interactions[user].keys())
            degree = len(neighbors)
            
            if degree < 2:
                fragmentation_scores[user] = 0
                continue
                
            triangles = 0
            for n1, n2 in combinations(neighbors, 2):
                if n2 in self.user_interactions.get(n1, {}):
                    triangles += 1
            
            possible_triangles = degree * (degree - 1) / 2
            clustering_coeff = triangles / possible_triangles
            
            fragmentation_scores[user] = degree * (1 - clustering_coeff)
        
        return sorted(fragmentation_scores.items(), key=lambda x: x[1], reverse=True)
    
    def find_natural_groups(self):
        """Algoritmo otimizado para detecção de comunidades"""
        if self.user_interactions is None:
            self.build_interaction_graph()
        
        if not self.user_interactions:
            return {}
        
        labels = {user: i for i, user in enumerate(self.user_interactions)}
        
        changed = True
        max_iter = 10
        current_iter = 0
        
        while changed and current_iter < max_iter:
            changed = False
            current_iter += 1
            
            nodes_ordered = sorted(self.user_interactions.keys(),
                                 key=lambda x: -len(self.user_interactions[x]))
            
            for node in nodes_ordered:
                if not self.user_interactions[node]:
                    continue
                    
                neighbor_labels = Counter()
                for neighbor in self.user_interactions[node]:
                    neighbor_labels[labels[neighbor]] += 1
                
                if not neighbor_labels:
                    continue
                
                most_common = neighbor_labels.most_common(1)[0][0]
                
                if labels[node] != most_common:
                    labels[node] = most_common
                    changed = True
        
        groups = defaultdict(list)
        for user, group_id in labels.items():
            groups[group_id].append(user)
        
        return dict(groups)
    
    def calculate_connection_level(self):
        """Cálculo otimizado do nível de conexão"""
        if self.user_interactions is None:
            self.build_interaction_graph()
        
        if not self.user_interactions:
            return 0.0
        
        n = len(self.user_interactions)
        if n < 2:
            return 0.0
        
        existing_edges = sum(len(neighbors) for neighbors in self.user_interactions.values()) // 2
        
        max_edges = n * (n - 1) // 2
        
        return (existing_edges / max_edges) * 100
    
    def find_closest_users(self, user, top_n=5):
        """BFS otimizado para encontrar usuários mais próximos"""
        if self.user_interactions is None:
            self.build_interaction_graph()
        
        if user not in self.user_interactions:
            return []
        
        distances = {user: 0}
        queue = deque([user])
        
        while queue:
            current = queue.popleft()
            for neighbor in self.user_interactions[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        
        distances.pop(user)
        
        closest = heapq.nsmallest(top_n, distances.items(), key=lambda x: x[1])
        return closest
    
    def find_non_interacting_closest(self, user, top_n=5):
        """Versão otimizada para encontrar próximos não interagentes"""
        if self.user_interactions is None:
            self.build_interaction_graph()
        
        if user not in self.user_interactions:
            return []
        
        direct_neighbors = set(self.user_interactions[user].keys())
        
        closest = self.find_closest_users(user, top_n + len(direct_neighbors))
        
        non_interacting = [(u, d) for u, d in closest if u not in direct_neighbors]
        
        return non_interacting[:top_n]
    
    def generate_report(self, output_file: str = "data_report.txt"):
        """Gera relatório otimizado"""
        print(f"\n📄 Gerando relatório: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE - VERSÃO OTIMIZADA\n")
            f.write("=" * 80 + "\n")
            f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("\n1. TOP 5 USUÁRIOS MAIS INFLUENTES\n")
            f.write("-" * 60 + "\n")
            top_influencers = self.get_top_influencers(5)
            for i, (user, degree) in enumerate(top_influencers, 1):
                f.write(f"{i}. {user}: grau {degree}\n")
            
            f.write("\n2. PRINCIPAIS FONTES DE FRAGMENTAÇÃO\n")
            f.write("-" * 60 + "\n")
            fragmenters = self.identify_fragmentation_sources()[:5]
            for i, (user, score) in enumerate(fragmenters, 1):
                f.write(f"{i}. {user}: score {score:.2f}\n")
            
            f.write("\n3. GRUPOS NATURAIS (TOP 3)\n")
            f.write("-" * 60 + "\n")
            groups = self.find_natural_groups()
            if groups:
                sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))[:3]
                for i, (group_id, members) in enumerate(sorted_groups, 1):
                    f.write(f"\nGrupo {i} ({len(members)} membros):\n")
                    f.write(", ".join(members[:5]))
                    if len(members) > 5:
                        f.write(", ...")
            else:
                f.write("Nenhum grupo identificado.\n")
            
            f.write("\n\n4. NÍVEL DE CONEXÃO DA COMUNIDADE\n")
            f.write("-" * 60 + "\n")
            connection_level = self.calculate_connection_level()
            f.write(f"{connection_level:.2f}% de conexão\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("FIM DO RELATÓRIO\n")
        
        print(f"✅ Relatório salvo em: {output_file}")

def main():
    explorer = DataExplorer()
    
    print("🔍 EXPLORADOR DE DADOS - VERSÃO OTIMIZADA")
    print("="*50)
    
    explorer.load_data()
    
    if not explorer.data:
        print("❌ Nenhum dado encontrado!")
        return
    
    print("\n⏳ Construindo grafo de interações...")
    explorer.build_interaction_graph()
    
    print("📊 Gerando relatório...")
    explorer.generate_report()

if __name__ == "__main__":
    main()