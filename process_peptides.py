import os
import re
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
        df = pd.read_csv(filepath, low_memory=False)
        df = df.dropna(subset=['Sequence_Normalized'])
        
        # Filtro de aminoácidos naturales
        valid_amino_acids = '^[ACDEFGHIKLMNPQRSTVWY]+$'
        df = df[df['Sequence_Normalized'].str.contains(valid_amino_acids, regex=True, na=False)]
        
        print(f"Filtrado completo. Procesando {len(df)} registros válidos.")
    except Exception as e:
        raise RuntimeError(f"Error crítico al leer el archivo: {e}")

    # Reglas de agregación
    def join_unique(s): 
        return '; '.join(s.dropna().astype(str).unique())

    agg_rules = {}
    for col in ['Target Species', 'Source_DB', 'Comments', 'Hemolytic_activity']:
        if col in df.columns: agg_rules[col] = join_unique
            
    if 'Activity' in df.columns: agg_rules['Activity'] = 'min'
    if 'MIC' in df.columns: agg_rules['MIC'] = 'min'
    
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
    df['length'] = df['Sequence_Normalized'].str.len()
    sequences = df['Sequence_Normalized'].tolist()
    
    glob_desc = GlobalDescriptor(sequences)
    glob_desc.calculate_charge(ph=7.0)
    df['net_charge'] = glob_desc.descriptor.flatten()
    
    pep_desc = PeptideDescriptor(sequences, 'eisenberg')
    pep_desc.calculate_global() 
    df['hydrophobicity_eisenberg'] = pep_desc.descriptor.flatten()
    
    pep_desc.calculate_moment() 
    df['hydrophobic_moment'] = pep_desc.descriptor.flatten()
    
    return df

def normalize_0_100(series):
    """Normalización Min-Max."""
    if series.max() == series.min(): return 0
    return (series - series.min()) / (series.max() - series.min()) * 100

def extract_clean_hemolysis(value):
    val_str = str(value).strip().lower()
    
    # 1. TRATAMIENTO DE "NONE" Y VACÍOS
    # Si el investigador puso "None", asumimos que es SEGURO (0% hemólisis)
    # para que el score suba a 100.
    if val_str in ['none', 'non-hemolytic', '0', '0%', 'no', 'safe']:
        return 0.0  # -> Esto dará SafetyScore = 100

    # 2. LIMPIEZA DE REFERENCIAS (Elimina cosas como [Ref.28002968])
    val_clean = re.sub(r'\[.*?\]', '', val_str)
    
    # 3. EXTRACCIÓN DE PORCENTAJE (Busca "10%")
    match_pct = re.search(r'(\d+\.?\d*)\s*%', val_clean)
    if match_pct:
        return float(match_pct.group(1))
    
    # 4. EXTRACCIÓN DE MHC (Mínima Concentración Hemolítica)
    # Si MHC es alto (ej. MHC > 1000), es seguro. Si es bajo, es tóxico.
    match_mhc = re.search(r'mhc\s*[:=]?\s*(\d+\.?\d*)', val_clean)
    if match_mhc:
        mhc_val = float(match_mhc.group(1))
        if mhc_val > 100: return 0.0  # Muy seguro
        if mhc_val < 10: return 90.0  # Muy tóxico
        return 50.0
    
    # 5. SI REALMENTE ES UN VALOR NULO (NaN de Python)
    if pd.isna(value) or val_str == 'nan':
        return 50.0 # Incertidumbre
        
    return 50.0

def calculate_final_scores(df):
    print(f"--- FASE 3: Aplicación de Scoring y Clasificación ---")
    
    if 'length' not in df.columns:
        df['length'] = df['Sequence_Normalized'].str.len()

    # --- 1. NORMALIZACIÓN DE CARGA (Tope en +8) ---
    # Cualquier carga mayor a +8 es excelente, no hace falta que sea +20
    df['ChargeScore'] = (df['net_charge'] / 8).clip(0, 1) * 100

    # --- 2. NORMALIZACIÓN DE ANFIPATÍA (Tope en 0.8) ---
    # Un momento hidrofóbico de 0.8 ya es muy potente para romper membranas
    df['AmphipathicityScore'] = (df['hydrophobic_moment'] / 0.8).clip(0, 1) * 100

    # --- 3. HIDROFOBICIDAD OPTIMIZADA (Target 0.45) ---
    ideal_h = 0.45
    distancia = (df['hydrophobicity_eisenberg'] - ideal_h).abs()
    max_dist = distancia.max() if distancia.max() != 0 else 1
    df['HydrophobicityScore'] = 100 * (1 - (distancia / max_dist))

    # --- 4. SCORE POR LONGITUD ---
    def get_len_score(l):
        if 10 <= l <= 25: return 100
        if 26 <= l <= 40: return 70
        if l < 10: return 40
        return 20
    df['LengthScore'] = df['length'].apply(get_len_score)

    # --- 5. FUNCTION SCORE (Ponderación de los Scores de 0-100) ---
    df['FunctionScore'] = (df['ChargeScore'] * 0.25) + \
                          (df['HydrophobicityScore'] * 0.25) + \
                          (df['AmphipathicityScore'] * 0.30) + \
                          (df['LengthScore'] * 0.20)

    # --- 6. SAFETY SCORE ---
    hemo_values = df['Hemolytic_activity'].apply(extract_clean_hemolysis)
    df['SafetyScore'] = 100 - hemo_values.clip(upper=100)

    # --- 7. FINAL SCORE (60/40) ---
    df['FinalScore'] = (df['FunctionScore'] * 0.6) + (df['SafetyScore'] * 0.4)

    def get_category(s):
        if s >= 60: return 'Strong Candidate'
        if s >= 45: return 'Promising'
        return 'Weak/Discard'
    df['Category'] = df['FinalScore'].apply(get_category)

    return df.sort_values(by='FinalScore', ascending=False)

def main():
    # Asegurate de que el nombre del archivo de entrada sea el correcto
    input_file = 'Master_Peptides_Final.csv' 
    output_file = 'Peptides_Ranked_Final.csv'
    
    if os.path.exists(input_file):
        df_clean = load_and_aggregate_data(input_file)
        df_scored = calculate_micro_scores(df_clean)
        df_final = calculate_final_scores(df_scored)
        
        df_final.to_csv(output_file, index=False)
        print(f"\n¡ÉXITO! Archivo '{output_file}' generado.")
        print(f"Distribución de categorías:\n{df_final['Category'].value_counts()}")
    else:
        print(f"Error: No se encontró el archivo '{input_file}'.")

if __name__ == "__main__":
    main()