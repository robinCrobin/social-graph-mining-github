import pandas as pd
from collections import defaultdict
from graphs_project.matrix import MatrixGraph  # ou from graphs_project.list import ListGraph
from graphs_project.list import ListGraph

class GitHubGraphProcessor:
    def __init__(self, graph_type='matrix'):
        """
        Inicializa o processador de grafos
        :param graph_type: 'matrix' para MatrixGraph ou 'list' para ListGraph
        """
        if graph_type == 'matrix':
            self.graph = MatrixGraph(directed=True)
        else:
            self.graph = ListGraph(directed=True)
        
        self.user_weights = defaultdict(int)  # Para armazenar pesos dos usuários
        self.added_vertices = set()  # Para controlar vértices já adicionados
    
    def load_data(self):
        """Carrega todos os CSVs necessários"""
        self.issues = pd.read_csv('data/issues.csv')
        self.pull_requests = pd.read_csv('data/pull_requests.csv')
        self.comments = pd.read_csv('data/comments.csv')
        self.reviews = pd.read_csv('data/reviews.csv')
        
        # Pré-processamento básico
        for df in [self.issues, self.pull_requests, self.comments, self.reviews]:
            df['author'] = df['author'].fillna('unknown')
            if 'closed_by' in df.columns:
                df['closed_by'] = df['closed_by'].fillna('unknown')
            if 'merged_by' in df.columns:
                df['merged_by'] = df['merged_by'].fillna('unknown')
    
    def process_interactions(self):
        """Processa todas as interações conforme as regras definidas"""
        # 1. A abre Issue e B fecha
        self._process_issue_closures()
        
        # 2. A abre PR e B faz merge/close
        self._process_pr_merges()
        
        # 3. B aprova/solicita mudanças no PR de A
        self._process_reviews()
        
        # 4. B comenta na Issue/PR de A
        self._process_comments()
    
    def _process_issue_closures(self):
        """Regra 1: A abre Issue e B fecha (weight=3)"""
        if 'state' not in self.issues.columns or 'closed_by' not in self.issues.columns:
            return
            
        closed_issues = self.issues[self.issues['state'] == 'closed']
        for _, issue in closed_issues.iterrows():
            if pd.notna(issue.get('closed_by')):
                self._add_interaction(
                    source=issue['author'],
                    target=issue['closed_by'],
                    weight=3,
                    label=f"Closed issue #{issue['number']}"
                )
    
    def _process_pr_merges(self):
        """Regra 2: A abre PR e B faz merge/close (weight=3)"""
        if 'state' not in self.pull_requests.columns:
            return
            
        closed_prs = self.pull_requests[self.pull_requests['state'] == 'closed']
        for _, pr in closed_prs.iterrows():
            closer = pr.get('merged_by') if pr.get('merged', False) else pr.get('closed_by', 'unknown')
            if pd.notna(closer):
                self._add_interaction(
                    source=pr['author'],
                    target=closer,
                    weight=3,
                    label=f"{'Merged' if pr.get('merged') else 'Closed'} PR #{pr['number']}"
                )
    
    def _process_reviews(self):
        """Regra 3: B aprova/solicita mudanças no PR de A (weight=2)"""
        if 'pr_number' not in self.reviews.columns or 'author' not in self.reviews.columns:
            print("Colunas necessárias não encontradas no arquivo de reviews")
            return
            
        for _, review in self.reviews.iterrows():
            try:
                # Verifica se o PR existe
                pr = self.pull_requests[self.pull_requests['number'] == review['pr_number']]
                if pr.empty:
                    continue
                    
                pr_author = pr.iloc[0]['author']
                review_author = review['author']
                
                if pd.isna(pr_author) or pd.isna(review_author):
                    continue
                    
                self._add_interaction(
                    source=pr_author,
                    target=review_author,
                    weight=2,
                    label=f"Review on PR #{review['pr_number']} ({review.get('state', 'unknown')})"
                )
            except Exception as e:
                print(f"Erro ao processar review {review.get('id', 'unknown')}: {str(e)}")
                continue
    
    def _process_comments(self):
        """Regra 4: B comenta na Issue/PR de A (weight=2)"""
        if 'issue_number' not in self.comments.columns:
            return
            
        for _, comment in self.comments.iterrows():
            # Verifica se é issue ou PR
            if comment['issue_number'] in self.issues['number'].values:
                source_df = self.issues
            else:
                source_df = self.pull_requests
                
            source_author = source_df[source_df['number'] == comment['issue_number']]['author']
            
            if not source_author.empty:
                self._add_interaction(
                    source=source_author.iloc[0],
                    target=comment['author'],
                    weight=2,
                    label=f"Comment on #{comment['issue_number']}"
                )
    
    def _add_interaction(self, source, target, weight, label):
        """Adiciona uma interação ao grafo"""
        if source == target or not source or not target:
            return  
        
        if source not in self.added_vertices:
            try:
                self.graph.lib_add_vertex(source)
                self.graph.lib_set_vertex_label(source, source)
                self.added_vertices.add(source)
            except Exception as e:
                print(f"Erro ao adicionar vértice {source}: {str(e)}")
                return
                
        if target not in self.added_vertices:
            try:
                self.graph.lib_add_vertex(target)
                self.graph.lib_set_vertex_label(target, target)
                self.added_vertices.add(target)
            except Exception as e:
                print(f"Erro ao adicionar vértice {target}: {str(e)}")
                return

        self.user_weights[source] += weight
        self.user_weights[target] += weight
        
        edge_exists = False
        for edge in self.graph.edges:
            if (edge.sourceVertex.id == source and 
                edge.targetVertex.id == target and 
                edge.label == label):
                edge_exists = True
                break
        
        if edge_exists:
            try:
                current_weight = self._get_edge_weight(source, target, label)
                self.graph.lib_set_edge_weight(
                    weight=current_weight + weight,
                    source_id=source,
                    target_id=target,
                    label=label
                )
            except Exception as e:
                print(f"Erro ao atualizar aresta {source}->{target}: {str(e)}")
        else:
            try:
                self.graph.lib_add_edge(
                    source_id=source,
                    target_id=target,
                    weight=weight,
                    label=label
                )
            except Exception as e:
                print(f"Erro ao adicionar aresta {source}->{target}: {str(e)}")
    
    def _get_edge_weight(self, source, target, label):
        """Obtém o peso atual de uma aresta"""
        for edge in self.graph.edges:
            if (edge.sourceVertex.id == source and 
                edge.targetVertex.id == target and 
                edge.label == label):
                return edge.weight
        return 0
    
    def export_graph(self, filename):
        """Exporta o grafo para GEXF"""
        # Aplica pesos acumulados aos vértices
        for user, weight in self.user_weights.items():
            try:
                self.graph.lib_set_vertex_weight(user, weight)
            except Exception as e:
                print(f"Erro ao definir peso para {user}: {str(e)}")
        
        self.graph.export_to_gexf(filename)
        print(f"Grafo exportado com sucesso para {filename}.gexf")


if __name__ == "__main__":
    processor = GitHubGraphProcessor(graph_type='matrix')  # ou 'list'
    processor.load_data()
    processor.process_interactions()
    processor.export_graph('github_interactions')