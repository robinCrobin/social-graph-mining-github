#!/usr/bin/env python3
"""
Script para explorar dados minerados do GitHub
"""

import os
import pandas as pd
from collections import defaultdict
import heapq
from graphs_project.matrix import MatrixGraph


class DataExplorer:
    def __init__(self):
        """Inicializa o explorador de dados"""
        self.graph = MatrixGraph(directed=True)
        self.added_vertices = set()
        self.data = None
        self._pr_cache = {}
        self._issue_cache = {}

        with open('relatorio.txt', 'w', encoding='utf-8') as f:
            pass

    def load_data(self):
        """Carrega os dados dos arquivos CSV"""
        try:
            self.issues = pd.read_csv('data/issues.csv',
                                      usecols=['author', 'state', 'closed_at', 'number'])
            self.pull_requests = pd.read_csv('data/pull_requests.csv',
                                             usecols=['author', 'state', 'merged_at', 'closed_at', 'number', 'merged'])
            self.comments = pd.read_csv('data/comments.csv',
                                        usecols=['author', 'issue_number'])
            self.reviews = pd.read_csv('data/reviews.csv',
                                       usecols=['pr_number', 'author', 'state'])

            for df in [self.issues, self.pull_requests, self.comments, self.reviews]:
                df['author'] = df['author'].fillna('unknown')

            self._pr_cache = {row['number']: row for _,
                              row in self.pull_requests.iterrows()}
            self._issue_cache = {row['number']: row for _, row in self.issues.iterrows()}

            self.data = {
                'issues': self.issues,
                'pull_requests': self.pull_requests,
                'comments': self.comments,
                'reviews': self.reviews
            }
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            self.data = None

    def build_interaction_graph(self):
        """Constrói o grafo de interações"""
        if not self.data:
            return

        self._process_reviews_batch()
        self._process_comments_batch()

    def _process_reviews_batch(self):
        """Processa reviews em lote"""
        if 'pr_number' not in self.reviews.columns or 'author' not in self.reviews.columns:
            print("Colunas necessárias não encontradas no arquivo de reviews")
            return

        interactions = []

        for _, review in self.reviews.iterrows():
            pr = self._pr_cache.get(review['pr_number'])
            if pr is None:
                continue

            pr_author = pr['author']
            review_author = review['author']

            if pd.isna(pr_author) or pd.isna(review_author):
                continue

            interactions.append((
                pr_author,
                review_author,
                1,
                f"Review on PR #{review['pr_number']} ({review.get('state', 'unknown')})"
            ))

        self._add_batch_interactions(interactions)

    def _process_comments_batch(self):
        """Processa comentários em lote"""
        if 'issue_number' not in self.comments.columns:
            return

        interactions = []

        for _, comment in self.comments.iterrows():
            issue_num = comment['issue_number']
            source_row = self._issue_cache.get(
                issue_num, self._pr_cache.get(issue_num))

            if source_row is not None:
                interactions.append((
                    source_row['author'],
                    comment['author'],
                    1,
                    f"Comment on #{comment['issue_number']}"
                ))

        self._add_batch_interactions(interactions)

    def _add_batch_interactions(self, interactions):
        """Adiciona um lote de interações ao grafo"""
        for source, target, weight, label in interactions:
            if source == target or not source or not target:
                continue

            if source not in self.added_vertices:
                self.graph.lib_add_vertex(source)
                self.graph.lib_set_vertex_label(source, source)
                self.added_vertices.add(source)

            if target not in self.added_vertices:
                self.graph.lib_add_vertex(target)
                self.graph.lib_set_vertex_label(target, target)
                self.added_vertices.add(target)

            self.graph.lib_add_edge(
                source_id=source,
                target_id=target,
                weight=weight,
                label=label
            )

    def calculate_user_scores(self):
        """Calcula a pontuação de cada usuário baseada no grau total (entrada + saída)"""
        user_scores = defaultdict(int)
        ids = [v.id for v in self.graph.vertices]
        n = len(ids)

        for i in range(n):
            for j in range(n):
                weight = self.graph.matrix[i][j]
                if weight > 0:
                    source_id = ids[i]
                    target_id = ids[j]
                    user_scores[source_id] += weight
                    user_scores[target_id] += weight

        return user_scores

    def calculate_weighted_degrees(self):
        """Calcula o grau ponderado de entrada + saída de cada vértice"""
        weighted_degrees = {}
        ids = [v.id for v in self.graph.vertices]
        n = len(ids)

        for i in range(n):
            vertex_id = ids[i]
            out_degree = sum(self.graph.matrix[i][j] for j in range(n))
            in_degree = sum(self.graph.matrix[j][i] for j in range(n))
            weighted_degrees[vertex_id] = out_degree + in_degree

        return weighted_degrees

    def identify_natural_groups(self):
        """Identifica grupos naturais (componentes fortemente conectados)"""
        from collections import defaultdict, deque

        ids = [v.id for v in self.graph.vertices]
        index_map = {v.id: i for i, v in enumerate(self.graph.vertices)}
        n = len(ids)

        adj = [[] for _ in range(n)]
        transpose = [[] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if self.graph.matrix[i][j] > 0:
                    adj[i].append(j)
                    transpose[j].append(i)

        visited = [False] * n
        finish_stack = []

        def dfs(v):
            visited[v] = True
            for nei in adj[v]:
                if not visited[nei]:
                    dfs(nei)
            finish_stack.append(v)

        def reverse_dfs(v, group):
            visited[v] = True
            group.append(ids[v])
            for nei in transpose[v]:
                if not visited[nei]:
                    reverse_dfs(nei, group)

        for i in range(n):
            if not visited[i]:
                dfs(i)

        visited = [False] * n
        groups = []

        while finish_stack:
            v = finish_stack.pop()
            if not visited[v]:
                group = []
                reverse_dfs(v, group)
                if group:
                    groups.append(group)

        return groups

    def identify_top_weighted_vertices(self, top_n=5):
        """Retorna os top_n vértices com maior grau ponderado"""
        weighted_degrees = self.calculate_weighted_degrees()
        return heapq.nlargest(top_n, weighted_degrees.items(), key=lambda x: x[1])

    def identify_influential_users(self, top_n=10):
        """Identifica os usuários mais influentes baseado no grau total"""
        user_scores = self.calculate_user_scores()
        return heapq.nlargest(top_n, user_scores.items(), key=lambda x: x[1])

    # TOP 5 COMUNIDADES E NÍVEL DE INFLUÊNCIA
    # A fazer

    # USUÁRIOS MAIS PRÓXIMOS DADO UM USUÁRIO
    def get_total_neighbors(self, user_id):
        """Retorna o número total de vizinhos mais próximos (entrada e saída) de um usuário (nó)."""
        if user_id not in self.added_vertices:
            return 0

        ids = [v.id for v in self.graph.vertices]
        index_map = {v.id: i for i, v in enumerate(self.graph.vertices)}
        n = len(ids)

        i = index_map.get(user_id)
        if i is None:
            return 0

        neighbors = set()

        # Vizinhos de saída
        for j in range(n):
            if self.graph.matrix[i][j] > 0:
                neighbors.add(ids[j])

        # Vizinhos de entrada
        for j in range(n):
            if self.graph.matrix[j][i] > 0:
                neighbors.add(ids[j])

        # Remove o próprio nó, se presente
        neighbors.discard(user_id)

        return len(neighbors)
    
    def calculate_group_connection_level(self, group):
        """Calcula o nível de conexão (em %) de uma comunidade (grupo fortemente conexo)"""
        ids = [v.id for v in self.graph.vertices]
        index_map = {v: i for i, v in enumerate(ids)}

        n = len(group)
        if n <= 1:
            return 100.0  

        real_connections = 0
        possible_connections = n * (n - 1)

        for i in range(n):
            for j in range(n):
                if i != j:
                    src = index_map[group[i]]
                    tgt = index_map[group[j]]
                    if self.graph.matrix[src][tgt] > 0:
                        real_connections += 1

        return (real_connections / possible_connections) * 100


    def calculate_graph_density(self):
        """Calcula a densidade do grafo de interações"""
        n = len(self.graph.vertices)
        if n <= 1:
            return 0.0

        total_edges = 0
        for i in range(n):
            for j in range(n):
                if self.graph.matrix[i][j] > 0:
                    total_edges += 1

        max_possible_edges = n * (n - 1) 
        return total_edges / max_possible_edges

    # USUÁRIOS MAIS PRÓXIMOS QUE NÃO INTERAGEM DADO UM USUÁRIO
    def get_total_indirect_neighbors(self, user_id):
        """Retorna o número total de vizinhos indiretos de um usuário (nó), ou seja, aqueles a 2 ou 3 níveis de distância (sem ligação direta)."""
        if user_id not in self.added_vertices:
            return 0

        ids = [v.id for v in self.graph.vertices]
        index_map = {v.id: i for i, v in enumerate(self.graph.vertices)}
        n = len(ids)

        start = index_map.get(user_id)
        if start is None:
            return 0

        visited = set()
        level = {start: 0}
        queue = [(start, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= 3:
                continue

            for neighbor in range(n):
                if self.graph.matrix[current][neighbor] > 0 or self.graph.matrix[neighbor][current] > 0:
                    if neighbor not in level:
                        level[neighbor] = depth + 1
                        queue.append((neighbor, depth + 1))

        # Coletar apenas os nós de nível 2 e 3
        indirect_neighbors = {ids[node]
                              for node, d in level.items() if d in (2, 3)}

        return len(indirect_neighbors)

    # GERAÇÃO DE RELATÓRIO
    def generate_report(self):
        """Gera um relatório básico sobre os dados"""
        report = "\nRELATÓRIO DE DADOS\n"
        report += "="*50 + "\n"

        if not self.data:
            report += "Nenhum dado disponível para gerar relatório\n"
            return

        report += f"\nTotal de Issues: {len(self.issues)}\n"
        report += f"Total de Pull Requests: {len(self.pull_requests)}\n"
        report += f"Total de Comentários: {len(self.comments)}\n"
        report += f"Total de Reviews: {len(self.reviews)}\n"

        top_weighted = self.identify_top_weighted_vertices()
        if top_weighted:
            report += "\nTOP 5 USUÁRIOS COM MAIOR INFLUENCIA:\n"
            for i, (user, _) in enumerate(top_weighted, 1):
                report += f"{i}. {user}\n"

        top_users = self.identify_influential_users()
        if top_users:
            report += "\nTOP 10 USUÁRIOS QUE GERAM MAIOR FRAGMENTACAO:\n"
            for i, (user, score) in enumerate(top_users, 1):
                report += f"{i}. {user}: Grau total = {score}\n"

        natural_groups = self.identify_natural_groups()
        natural_groups.sort(key=len, reverse=True)
        report += f"\nNúmero de Grupos Naturais (Componentes Fortemente Conexos): {len(natural_groups)}\n"
        report += "\nTOP 5 MAIORES GRUPOS NATURAIS:\n"
        for i, group in enumerate(natural_groups[:5], 1):
            conn_level = self.calculate_group_connection_level(group)
            report += f"{i}. ({len(group)} membros, conexão: {conn_level:.2f}%): {group}\n"

        graph_density = self.calculate_graph_density()
        report += f"\nDENSIDADE DO GRAFO: {graph_density:.3f}\n"

        report += "\nTOP 5 COMUNIDADES E NÍVEL DE INFLUÊNCIA\n"

        report += "\nUSUÁRIOS MAIS PRÓXIMOS DADO UM USUÁRIO\n"
        top1UserNeighbors = self.get_total_neighbors("seberg")
        top2UserNeighbors = self.get_total_neighbors("eric-wieser")
        top3UserNeighbors = self.get_total_neighbors("charris")
        top4UserNeighbors = self.get_total_neighbors("mattip")
        top5UserNeighbors = self.get_total_neighbors("rgommers")
        report += f"1. Usuário seberg: {top1UserNeighbors} usuários mais próximos (vizinhos diretos)\n"
        report += f"2. Usuário eric-wieser: {top2UserNeighbors} usuários mais próximos (vizinhos diretos)\n"
        report += f"3. Usuário charris: {top3UserNeighbors} usuários mais próximos (vizinhos diretos)\n"
        report += f"4. Usuário mattip: {top4UserNeighbors} usuários mais próximos (vizinhos diretos)\n"
        report += f"5. Usuário rgommers: {top5UserNeighbors} usuários mais próximos (vizinhos diretos)\n"

        report += "\nUSUÁRIOS MAIS PRÓXIMOS QUE NÃO INTERAGEM DADO UM USUÁRIO\n"
        top1UserIndirectNeighbors = self.get_total_indirect_neighbors("seberg")
        top2UserIndirectNeighbors = self.get_total_indirect_neighbors(
            "eric-wieser")
        top3UserIndirectNeighbors = self.get_total_indirect_neighbors(
            "charris")
        top4UserIndirectNeighbors = self.get_total_indirect_neighbors("mattip")
        top5UserIndirectNeighbors = self.get_total_indirect_neighbors(
            "rgommers")
        report += f"1. Usuário seberg: {top1UserIndirectNeighbors} usuários mais próximos que não interagem diretamente\n"
        report += f"2. Usuário eric-wieser: {top2UserIndirectNeighbors} usuários mais próximos que não interagem diretamente\n"
        report += f"3. Usuário charris: {top3UserIndirectNeighbors} usuários mais próximos que não interagem diretamente\n"
        report += f"4. Usuário mattip: {top4UserIndirectNeighbors} usuários mais próximos que não interagem diretamente\n"
        report += f"5. Usuário rgommers: {top5UserIndirectNeighbors} usuários mais próximos que não interagem diretamente\n"

        with open('relatorio.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print(report)


def main():
    explorer = DataExplorer()

    print("EXPLORADOR DE DADOS")
    print("="*50)

    explorer.load_data()

    if not explorer.data:
        print("Nenhum dado encontrado!")
        return

    print("\nConstruindo grafo de interações...")
    explorer.build_interaction_graph()

    print("Gerando relatório...")
    explorer.generate_report()


if __name__ == "__main__":
    main()
