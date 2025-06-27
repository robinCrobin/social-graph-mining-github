#!/usr/bin/env python3
"""
Exemplo de análises específicas com os dados minerados
Este script demonstra como usar os dados para responder questões específicas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

class NumPyAnalysis:
    """Análises específicas do repositório NumPy"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.issues_df = None
        self.prs_df = None
        self.comments_df = None
        self.reviews_df = None
        
    def load_data(self):
        """Carrega os dados minerados"""
        try:
            self.issues_df = pd.read_csv(os.path.join(self.data_dir, "issues.csv"))
            self.prs_df = pd.read_csv(os.path.join(self.data_dir, "pull_requests.csv"))
            self.comments_df = pd.read_csv(os.path.join(self.data_dir, "comments.csv"))
            self.reviews_df = pd.read_csv(os.path.join(self.data_dir, "reviews.csv"))
            
            # Converter datas
            for df in [self.issues_df, self.prs_df, self.comments_df, self.reviews_df]:
                if df is not None and 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
            
            print("✅ Dados carregados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return False
    
    def analyze_issue_resolution_time(self):
        """Analisa tempo de resolução de issues"""
        print("\n🕐 ANÁLISE: Tempo de Resolução de Issues")
        print("="*50)
        
        if self.issues_df is None:
            print("❌ Dados de issues não disponíveis")
            return
        
        # Filtrar issues fechadas
        closed_issues = self.issues_df[
            (self.issues_df['state'] == 'CLOSED') & 
            (self.issues_df['closed_at'].notna())
        ].copy()
        
        if len(closed_issues) == 0:
            print("❌ Nenhuma issue fechada encontrada")
            return
        
        # Calcular tempo de resolução
        closed_issues['closed_at'] = pd.to_datetime(closed_issues['closed_at'])
        closed_issues['resolution_time'] = (
            closed_issues['closed_at'] - closed_issues['created_at']
        ).dt.days
        
        # Estatísticas
        stats = closed_issues['resolution_time'].describe()
        
        print(f"📊 Estatísticas de Tempo de Resolução (dias):")
        print(f"   Total de issues fechadas: {len(closed_issues):,}")
        print(f"   Média: {stats['mean']:.1f} dias")
        print(f"   Mediana: {stats['50%']:.1f} dias")
        print(f"   Mínimo: {stats['min']:.0f} dias")
        print(f"   Máximo: {stats['max']:.0f} dias")
        
        # Categorizar por tempo
        categories = {
            'Muito Rápido (< 1 dia)': len(closed_issues[closed_issues['resolution_time'] < 1]),
            'Rápido (1-7 dias)': len(closed_issues[
                (closed_issues['resolution_time'] >= 1) & 
                (closed_issues['resolution_time'] <= 7)
            ]),
            'Médio (1-4 semanas)': len(closed_issues[
                (closed_issues['resolution_time'] > 7) & 
                (closed_issues['resolution_time'] <= 28)
            ]),
            'Lento (1-6 meses)': len(closed_issues[
                (closed_issues['resolution_time'] > 28) & 
                (closed_issues['resolution_time'] <= 180)
            ]),
            'Muito Lento (> 6 meses)': len(closed_issues[closed_issues['resolution_time'] > 180])
        }
        
        print(f"\n📈 Distribuição por Categoria:")
        for category, count in categories.items():
            percentage = (count / len(closed_issues)) * 100
            print(f"   {category}: {count:,} ({percentage:.1f}%)")
    
    def analyze_pr_merge_patterns(self):
        """Analisa padrões de merge de Pull Requests"""
        print("\n🔀 ANÁLISE: Padrões de Merge de Pull Requests")
        print("="*50)
        
        if self.prs_df is None:
            print("❌ Dados de PRs não disponíveis")
            return
        
        total_prs = len(self.prs_df)
        merged_prs = len(self.prs_df[self.prs_df['merged'] == True])
        closed_prs = len(self.prs_df[self.prs_df['state'] == 'CLOSED'])
        open_prs = len(self.prs_df[self.prs_df['state'] == 'OPEN'])
        
        print(f"📊 Estatísticas Gerais:")
        print(f"   Total de PRs: {total_prs:,}")
        print(f"   PRs Merged: {merged_prs:,} ({(merged_prs/total_prs)*100:.1f}%)")
        print(f"   PRs Fechados: {closed_prs:,} ({(closed_prs/total_prs)*100:.1f}%)")
        print(f"   PRs Abertos: {open_prs:,} ({(open_prs/total_prs)*100:.1f}%)")
        
        # Análise de tamanho dos PRs
        merged_df = self.prs_df[self.prs_df['merged'] == True].copy()
        
        if len(merged_df) > 0:
            print(f"\n📏 Análise de Tamanho (PRs Merged):")
            print(f"   Média de adições: {merged_df['additions'].mean():.0f} linhas")
            print(f"   Média de deleções: {merged_df['deletions'].mean():.0f} linhas")
            print(f"   Média de arquivos alterados: {merged_df['changed_files'].mean():.1f}")
            
            # Categorizar por tamanho
            small_prs = len(merged_df[merged_df['additions'] + merged_df['deletions'] <= 50])
            medium_prs = len(merged_df[
                (merged_df['additions'] + merged_df['deletions'] > 50) & 
                (merged_df['additions'] + merged_df['deletions'] <= 500)
            ])
            large_prs = len(merged_df[merged_df['additions'] + merged_df['deletions'] > 500])
            
            print(f"\n📊 Distribuição por Tamanho:")
            print(f"   Pequenos (≤ 50 linhas): {small_prs:,} ({(small_prs/len(merged_df))*100:.1f}%)")
            print(f"   Médios (51-500 linhas): {medium_prs:,} ({(medium_prs/len(merged_df))*100:.1f}%)")
            print(f"   Grandes (> 500 linhas): {large_prs:,} ({(large_prs/len(merged_df))*100:.1f}%)")
    
    def analyze_community_engagement(self):
        """Analisa engajamento da comunidade"""
        print("\n👥 ANÁLISE: Engajamento da Comunidade")
        print("="*50)
        
        # Coletar todos os contribuidores únicos
        all_contributors = set()
        
        if self.issues_df is not None:
            all_contributors.update(self.issues_df['author'].dropna().unique())
            
        if self.prs_df is not None:
            all_contributors.update(self.prs_df['author'].dropna().unique())
            
        if self.comments_df is not None:
            all_contributors.update(self.comments_df['author'].dropna().unique())
            
        if self.reviews_df is not None:
            all_contributors.update(self.reviews_df['author'].dropna().unique())
        
        print(f"👤 Total de contribuidores únicos: {len(all_contributors):,}")
        
        # Analisar atividade por tipo
        activity_stats = {}
        
        if self.issues_df is not None:
            activity_stats['Issues criadas'] = len(self.issues_df)
            activity_stats['Autores únicos de issues'] = self.issues_df['author'].nunique()
            
        if self.prs_df is not None:
            activity_stats['PRs criados'] = len(self.prs_df)
            activity_stats['Autores únicos de PRs'] = self.prs_df['author'].nunique()
            
        if self.comments_df is not None:
            activity_stats['Comments feitos'] = len(self.comments_df)
            activity_stats['Autores únicos de comments'] = self.comments_df['author'].nunique()
            
        if self.reviews_df is not None:
            activity_stats['Reviews feitos'] = len(self.reviews_df)
            activity_stats['Autores únicos de reviews'] = self.reviews_df['author'].nunique()
        
        print(f"\n📊 Atividade por Tipo:")
        for activity, count in activity_stats.items():
            print(f"   {activity}: {count:,}")
    
    def analyze_popular_labels(self):
        """Analisa labels mais populares"""
        print("\n🏷️  ANÁLISE: Labels Mais Populares")
        print("="*50)
        
        all_labels = []
        
        # Coletar labels de issues
        if self.issues_df is not None:
            for labels_str in self.issues_df['labels'].dropna():
                if labels_str:
                    labels = [l.strip() for l in labels_str.split(',') if l.strip()]
                    all_labels.extend(labels)
        
        # Coletar labels de PRs
        if self.prs_df is not None:
            for labels_str in self.prs_df['labels'].dropna():
                if labels_str:
                    labels = [l.strip() for l in labels_str.split(',') if l.strip()]
                    all_labels.extend(labels)
        
        if all_labels:
            label_counts = Counter(all_labels)
            top_labels = label_counts.most_common(15)
            
            print(f"📈 Top 15 Labels Mais Usadas:")
            for i, (label, count) in enumerate(top_labels, 1):
                print(f"   {i:2d}. {label:<30} ({count:,} usos)")
        else:
            print("❌ Nenhuma label encontrada")
    
    def analyze_temporal_trends(self):
        """Analisa tendências temporais"""
        print("\n📈 ANÁLISE: Tendências Temporais")
        print("="*50)
        
        # Analisar atividade por ano
        yearly_activity = {}
        
        for name, df in [('Issues', self.issues_df), ('PRs', self.prs_df), 
                        ('Comments', self.comments_df), ('Reviews', self.reviews_df)]:
            if df is not None and 'created_at' in df.columns:
                yearly_counts = df.groupby(df['created_at'].dt.year).size()
                yearly_activity[name] = yearly_counts.to_dict()
        
        if yearly_activity:
            all_years = set()
            for activity in yearly_activity.values():
                all_years.update(activity.keys())
            
            all_years = sorted(all_years)
            
            print(f"📊 Atividade por Ano:")
            print(f"{'Ano':<6} {'Issues':<8} {'PRs':<8} {'Comments':<10} {'Reviews':<8}")
            print("-" * 50)
            
            for year in all_years:
                issues = yearly_activity.get('Issues', {}).get(year, 0)
                prs = yearly_activity.get('PRs', {}).get(year, 0)
                comments = yearly_activity.get('Comments', {}).get(year, 0)
                reviews = yearly_activity.get('Reviews', {}).get(year, 0)
                
                print(f"{year:<6} {issues:<8,} {prs:<8,} {comments:<10,} {reviews:<8,}")
    
    def generate_insights_report(self):
        """Gera relatório de insights"""
        print("\n📄 Gerando relatório de insights...")
        
        with open("numpy_insights.txt", "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE INSIGHTS - NUMPY/NUMPY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Estatísticas básicas
            f.write("ESTATÍSTICAS BÁSICAS:\n")
            f.write("-" * 20 + "\n")
            
            if self.issues_df is not None:
                f.write(f"Issues: {len(self.issues_df):,}\n")
            if self.prs_df is not None:
                f.write(f"Pull Requests: {len(self.prs_df):,}\n")
            if self.comments_df is not None:
                f.write(f"Comments: {len(self.comments_df):,}\n")
            if self.reviews_df is not None:
                f.write(f"Reviews: {len(self.reviews_df):,}\n")
            
            f.write("\nEste relatório contém análises detalhadas do repositório NumPy.\n")
            f.write("Execute o script sample_analysis.py para ver análises completas.\n")
        
        print("✅ Relatório salvo em: numpy_insights.txt")

def main():
    """Função principal"""
    print("🔬 ANÁLISES ESPECÍFICAS - NUMPY/NUMPY")
    print("="*50)
    
    analyzer = NumPyAnalysis()
    
    if not analyzer.load_data():
        print("❌ Não foi possível carregar os dados. Execute main.py primeiro.")
        return
    
    # Executar análises
    try:
        analyzer.analyze_issue_resolution_time()
        analyzer.analyze_pr_merge_patterns()
        analyzer.analyze_community_engagement()
        analyzer.analyze_popular_labels()
        analyzer.analyze_temporal_trends()
        analyzer.generate_insights_report()
        
        print("\n✅ Análises concluídas!")
        print("💡 Veja os arquivos gerados para mais detalhes.")
        
    except Exception as e:
        print(f"❌ Erro durante as análises: {e}")

if __name__ == "__main__":
    main() 