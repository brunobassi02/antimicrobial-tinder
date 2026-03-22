import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from modlamp.descriptors import PeptideDescriptor, GlobalDescriptor

# 1. CONFIGURACIÓN INICIAL
load_dotenv()  # Carga la API Key desde el archivo .env
tqdm.pandas()

def load_and_aggregate_data(filepath):
    """
    Carga el CSV, elimina ambigüedades y colapsa duplicados.
    """
    print(f"--- FASE 1: Limpieza y Carga de Datos ---")
    try:
        # Lectura robusta del archivo maestro
        df = pd.read_csv(filepath, low_memory=False)
        
        # Eliminamos nulos en la columna clave
        df = df.dropna(subset=['Sequence_Normalized'])
        
        # FILTRO DE PUREZA: Solo permitimos los 20 aminoácidos naturales.
        # Esto elimina automáticamente cualquier 'X', 'Z', 'B' o caracteres extraños.
        valid_amino_acids = '^[ACDEFGHIKLMNPQRSTVWY]+$'
        df = df[df['Sequence_Normalized'].str.contains(valid_amino_acids, regex=True, na=False)]
        
        print(f"Filtrado completo. Procesando {len(df)} registros válidos.")
    except Exception as e:
        raise RuntimeError(f"Error crítico al leer el archivo: {e}")

    # REGLAS DE AGREGACIÓN: Colapsar 49k filas a péptidos únicos
    def join_unique(s): 
        return '; '.join(s.dropna().astype(str).unique())

    agg_rules = {}
    # Unimos textos de especies y fuentes
    for col in ['Target Species', 'Source_DB', 'Comments']:
        if col in df.columns: agg_rules[col] = join_unique
            
    # Conservamos mejor potencia (mínimo MIC) y peor seguridad (máxima hemólisis)
    if 'Activity' in df.columns: agg_rules['Activity'] = 'min'
    if 'MIC' in df.columns: agg_rules['MIC'] = 'min'
    if 'Hemolytic_activity' in df.columns: agg_rules['Hemolytic_activity'] = 'max'
    
    for col in df.columns:
        if col not in agg_rules and col != 'Sequence_Normalized': 
            agg_rules[col] = 'first'
            
    df_agg = df.groupby('Sequence_Normalized', as_index=False).agg(agg_rules)
    print(f"Colapso finalizado. Total de péptidos únicos: {len(df_agg)}")
    return df_agg

def calculate_micro_scores(df):
    """
    Cálculo de descriptores biofísicos usando modlamp.
    """
    print(f"--- FASE 2: Cálculos Biofísicos (modlamp) ---")
    sequences = df['Sequence_Normalized'].tolist()
    
    # Descriptor Global: Carga neta a pH 7.0 [cite: 12]
    glob_desc = GlobalDescriptor(sequences)
    glob_desc.calculate_charge(ph=7.0)
    df['net_charge'] = glob_desc.descriptor.flatten()
    
    # Descriptor de Péptido: Hidrofobicidad y Anfipatía (Eisenberg) [cite: 13, 14]
    pep_desc = PeptideDescriptor(sequences, 'eisenberg')
    pep_desc.calculate_global() # Hidrofobicidad global
    df['hydrophobicity_eisenberg'] = pep_desc.descriptor.flatten()
    
    pep_desc.calculate_moment() # Momento hidrofóbico (μH)
    df['hydrophobic_moment'] = pep_desc.descriptor.flatten()
    
    return df

def normalize_0_100(series):
    """Normalización Min-Max para escalas comparables."""
    if series.max() == series.min(): return 0
    return (series - series.min()) / (series.max() - series.min()) * 100

def calculate_final_scores(df):
    """
    Lógica de Scoring basada en el perfil agrobiotecnológico. [cite: 10, 21]
    """
    print(f"--- FASE 3: Aplicación de Scoring y Clasificación ---")
    
    # 1. Normalizamos los micro-scores para que pesen igual en la suma
    c_score = normalize_0_100(df['net_charge'])
    h_score = normalize_0_100(df['hydrophobicity_eisenberg'])
    a_score = normalize_0_100(df['hydrophobic_moment'])
    
    # 2. FUNCTION SCORE (60%): Potencial fisicoquímico [cite: 10]
    df['FunctionScore'] = (c_score * 0.3) + (h_score * 0.3) + (a_score * 0.4)
    
    # 3. SAFETY SCORE (40%): Basado en datos reales o penalización neutral [cite: 19]
    hemo = pd.to_numeric(df['Hemolytic_activity'], errors='coerce').fillna(50)
    df['SafetyScore'] = 100 - hemo.clip(upper=100)
    
    # 4. FINAL SCORE Y CATEGORÍA [cite: 21]
    df['FinalScore'] = (df['FunctionScore'] * 0.6) + (df['SafetyScore'] * 0.4)
    
    def get_category(s):
        if s >= 80: return 'Strong Candidate'
        if s >= 60: return 'Promising'
        return 'Weak/Discard'
        
    df['Category'] = df['FinalScore'].apply(get_category)
    return df.sort_values(by='FinalScore', ascending=False)

def main():
    input_file = 'Master_Peptides_Final.csv'
    output_file = 'Peptides_Ranked_Final.csv'
    
    if os.path.exists(input_file):
        # Ejecución del Pipeline
        df_clean = load_and_aggregate_data(input_file)
        df_scored = calculate_micro_scores(df_clean)
        df_final = calculate_final_scores(df_scored)
        
        df_final.to_csv(output_file, index=False)
        print(f"\n¡ÉXITO! Archivo '{output_file}' generado con {len(df_final)} péptidos únicos.")
    else:
        print(f"Error: No se encontró el archivo '{input_file}'.")

if __name__ == "__main__":
    main()