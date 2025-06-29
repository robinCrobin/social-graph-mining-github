#!/usr/bin/env python3
"""
Script para explorar dados minerados do GitHub - Versão Otimizada
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
        
        # Cria o arquivo relatorio.txt vazio no início
        with open('relatorio.txt', 'w', encoding='utf-8') as f:
            pass
    
    def load_data(self):
        """Carrega os dados dos arquivos CSV de forma otimizada"""
        try:
            # Carrega apenas colunas necessárias para cada DataFrame
            self.issues = pd.read_csv('data/issues.csv', 
                                    usecols=['author', 'state', 'closed_at', 'number'])
            self.pull_requests = pd.read_csv('data/pull_requests.csv', 
                                           usecols=['author', 'state', 'merged_at', 'closed_at', 'number', 'merged'])
            self.comments = pd.read_csv('data/comments.csv', 
                                      usecols=['author', 'issue_number'])
            self.reviews = pd.read_csv('data/reviews.csv', 
                                     usecols=['pr_number', 'author', 'state'])
            
            # Pré-processamento básico
            for df in [self.issues, self.pull_requests, self.comments, self.reviews]:
                df['author'] = df['author'].fillna('unknown')
            
            # Cria dicionários para acesso rápido
            self._pr_cache = {row['number']: row for _, row in self.pull_requests.iterrows()}
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
        """Constrói o grafo de interações de forma otimizada"""
        if not self.data:
            return
        
        # Processa em lotes para melhor desempenho
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
                1,  # Peso padrão para arestas
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
            source_row = self._issue_cache.get(issue_num, self._pr_cache.get(issue_num))
            
            if source_row is not None:
                interactions.append((
                    source_row['author'],
                    comment['author'],
                    1,  # Peso padrão para arestas
                    f"Comment on #{comment['issue_number']}"
                ))
        
        self._add_batch_interactions(interactions)
    
    def _add_batch_interactions(self, interactions):
        """Adiciona um lote de interações ao grafo de forma otimizada"""
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
            
            # Adiciona a aresta
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
                    user_scores[source_id] += weight  # saída
                    user_scores[target_id] += weight  # entrada

        return user_scores

    
    def identify_influential_users(self, top_n=10):
        """Identifica os usuários mais influentes baseado no grau total"""
        user_scores = self.calculate_user_scores()
        return heapq.nlargest(top_n, user_scores.items(), key=lambda x: x[1])

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
        
        report += f"\nTotal de Vértices no Grafo: {len(self.graph.vertices)}\n"
        report += f"Total de Arestas no Grafo: {len(self.graph.edges)}\n"
        
        top_users = self.identify_influential_users()
        if top_users:
            report += "\nTOP 10 USUÁRIOS MAIS INFLUENTES (POR GRAU TOTAL):\n"
            for i, (user, score) in enumerate(top_users, 1):
                report += f"{i}. {user}: Grau total = {score}\n"
        
        # Salva o relatório em arquivo
        with open('relatorio.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Exibe no console
        print(report)

def main():
    explorer = DataExplorer()
    
    print("EXPLORADOR DE DADOS - VERSÃO OTIMIZADA")
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