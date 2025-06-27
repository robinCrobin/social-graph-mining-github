#!/usr/bin/env python3
"""
Script para explorar os dados minerados do GitHub
"""

import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class DataExplorer:
    """Explorador de dados minerados"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.data = {}
        
    def load_data(self):
        """Carrega todos os arquivos CSV"""
        files = {
            'issues': 'issues.csv',
            'pull_requests': 'pull_requests.csv',
            'comments': 'comments.csv',
            'reviews': 'reviews.csv'
        }
        
        for key, filename in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath)
                    self.data[key] = df
                    print(f"✅ {key}: {len(df)} registros carregados")
                except Exception as e:
                    print(f"❌ Erro ao carregar {filename}: {e}")
            else:
                print(f"⚠️  Arquivo não encontrado: {filename}")
    
    def show_summary(self):
        """Mostra resumo dos dados"""
        print("\n" + "="*50)
        print("📊 RESUMO DOS DADOS MINERADOS")
        print("="*50)
        
        total_records = 0
        for key, df in self.data.items():
            count = len(df)
            total_records += count
            print(f"{key.upper():<15}: {count:>8,} registros")
        
        print("-"*50)
        print(f"{'TOTAL':<15}: {total_records:>8,} registros")
        
        # Informações adicionais
        if 'issues' in self.data:
            issues_df = self.data['issues']
            open_issues = len(issues_df[issues_df['state'] == 'OPEN'])
            closed_issues = len(issues_df[issues_df['state'] == 'CLOSED'])
            print(f"\n📋 ISSUES:")
            print(f"   Abertas: {open_issues:,}")
            print(f"   Fechadas: {closed_issues:,}")
        
        if 'pull_requests' in self.data:
            prs_df = self.data['pull_requests']
            open_prs = len(prs_df[prs_df['state'] == 'OPEN'])
            closed_prs = len(prs_df[prs_df['state'] == 'CLOSED'])
            merged_prs = len(prs_df[prs_df['merged'] == True])
            print(f"\n🔀 PULL REQUESTS:")
            print(f"   Abertos: {open_prs:,}")
            print(f"   Fechados: {closed_prs:,}")
            print(f"   Merged: {merged_prs:,}")
    
    def show_top_contributors(self, top_n: int = 10):
        """Mostra top contribuidores"""
        print(f"\n🏆 TOP {top_n} CONTRIBUIDORES")
        print("="*50)
        
        all_authors = []
        
        # Coletar autores de todas as fontes
        for key, df in self.data.items():
            if 'author' in df.columns:
                authors = df['author'].dropna().tolist()
                all_authors.extend([(author, key) for author in authors])
        
        if all_authors:
            # Contar contribuições por autor
            author_counts = {}
            for author, source in all_authors:
                if author not in author_counts:
                    author_counts[author] = {'total': 0, 'issues': 0, 'pull_requests': 0, 'comments': 0, 'reviews': 0}
                author_counts[author]['total'] += 1
                author_counts[author][source] += 1
            
            # Ordenar por total de contribuições
            sorted_authors = sorted(author_counts.items(), key=lambda x: x[1]['total'], reverse=True)
            
            print(f"{'AUTOR':<20} {'TOTAL':<8} {'ISSUES':<8} {'PRs':<8} {'COMMENTS':<10} {'REVIEWS':<8}")
            print("-" * 70)
            
            for i, (author, counts) in enumerate(sorted_authors[:top_n]):
                print(f"{author:<20} {counts['total']:<8} {counts['issues']:<8} {counts['pull_requests']:<8} {counts['comments']:<10} {counts['reviews']:<8}")
    
    def analyze_time_trends(self):
        """Analisa tendências temporais"""
        print("\n📈 ANÁLISE TEMPORAL")
        print("="*50)
        
        for key, df in self.data.items():
            if 'created_at' in df.columns and len(df) > 0:
                try:
                    # Converter para datetime
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    
                    # Estatísticas básicas
                    min_date = df['created_at'].min()
                    max_date = df['created_at'].max()
                    
                    print(f"\n{key.upper()}:")
                    print(f"   Período: {min_date.strftime('%Y-%m-%d')} até {max_date.strftime('%Y-%m-%d')}")
                    print(f"   Duração: {(max_date - min_date).days} dias")
                    
                    # Atividade por ano
                    yearly_counts = df.groupby(df['created_at'].dt.year).size()
                    print(f"   Atividade por ano:")
                    for year, count in yearly_counts.items():
                        print(f"      {year}: {count:,}")
                        
                except Exception as e:
                    print(f"   Erro na análise temporal de {key}: {e}")
    
    def show_label_analysis(self):
        """Analisa labels mais comuns"""
        print("\n🏷️  ANÁLISE DE LABELS")
        print("="*50)
        
        for key in ['issues', 'pull_requests']:
            if key in self.data and 'labels' in self.data[key].columns:
                df = self.data[key]
                
                # Extrair todas as labels
                all_labels = []
                for labels_str in df['labels'].dropna():
                    if labels_str:
                        labels = labels_str.split(',')
                        all_labels.extend([label.strip() for label in labels if label.strip()])
                
                if all_labels:
                    # Contar labels
                    label_counts = pd.Series(all_labels).value_counts()
                    
                    print(f"\n{key.upper()} - Top 10 Labels:")
                    for i, (label, count) in enumerate(label_counts.head(10).items()):
                        print(f"   {i+1:2d}. {label:<30} ({count:,})")
    
    def generate_report(self, output_file: str = "data_report.txt"):
        """Gera relatório completo"""
        print(f"\n📄 Gerando relatório: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE MINERAÇÃO DE DADOS - NUMPY/NUMPY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumo
            f.write("RESUMO DOS DADOS:\n")
            f.write("-" * 20 + "\n")
            total_records = 0
            for key, df in self.data.items():
                count = len(df)
                total_records += count
                f.write(f"{key.upper():<15}: {count:>8,} registros\n")
            f.write(f"{'TOTAL':<15}: {total_records:>8,} registros\n\n")
            
            # Detalhes por tipo
            for key, df in self.data.items():
                f.write(f"\n{key.upper()}:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total de registros: {len(df):,}\n")
                f.write(f"Colunas: {', '.join(df.columns)}\n")
                
                if 'created_at' in df.columns and len(df) > 0:
                    try:
                        df['created_at'] = pd.to_datetime(df['created_at'])
                        min_date = df['created_at'].min()
                        max_date = df['created_at'].max()
                        f.write(f"Período: {min_date.strftime('%Y-%m-%d')} até {max_date.strftime('%Y-%m-%d')}\n")
                    except:
                        pass
        
        print(f"✅ Relatório salvo em: {output_file}")

def main():
    """Função principal"""
    explorer = DataExplorer()
    
    print("🔍 EXPLORADOR DE DADOS - NUMPY/NUMPY")
    print("="*50)
    
    # Carregar dados
    explorer.load_data()
    
    if not explorer.data:
        print("❌ Nenhum dado encontrado! Execute primeiro o main.py")
        return
    
    # Análises
    explorer.show_summary()
    explorer.show_top_contributors()
    explorer.analyze_time_trends()
    explorer.show_label_analysis()
    
    # Gerar relatório
    explorer.generate_report()

if __name__ == "__main__":
    main() 