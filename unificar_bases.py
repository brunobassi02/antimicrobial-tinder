import pandas as pd
import re
import os

def normalize_sequence(seq):
    """
    Normaliza una secuencia de péptidos:
    - Convierte a mayúsculas.
    - Elimina espacios en blanco.
    - Elimina caracteres que no sean letras (A-Z).
    """
    if pd.isna(seq):
        return ""
    seq = str(seq).upper()
    seq = re.sub(r'[^A-Z]', '', seq)
    return seq

def parse_fasta(file_path):
    """
    Lee un archivo FASTA y lo convierte en un DataFrame de pandas.
    """
    ids = []
    sequences = []
    try:
        with open(file_path, 'r') as f:
            current_id = ""
            current_seq = []
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if current_id:
                        ids.append(current_id)
                        sequences.append("".join(current_seq))
                    current_id = line[1:] # Quitar el '>'
                    current_seq = []
                else:
                    current_seq.append(line)
            if current_id:
                ids.append(current_id)
                sequences.append("".join(current_seq))
        
        df = pd.DataFrame({
            'APD_ID': ids,
            'Sequence': sequences
        })
        return df
    except Exception as e:
        print(f"Error al leer el archivo FASTA {file_path}: {e}")
        return pd.DataFrame()

def main():
    data_dir = 'data_raw'
    output_file = 'Master_Peptides_Final.csv'
    
    # Archivos de entrada
    dbaasp_peptides_file = os.path.join(data_dir, 'peptides dbaasp.csv')
    dbaasp_hemolytic_file = os.path.join(data_dir, 'hemolytic-and-cytotoxic-activities dbaasp.csv')
    dbaasp_activity_file = os.path.join(data_dir, 'activity-against-target-species dbaasp.csv')
    dramp_file = os.path.join(data_dir, 'Antifungal_amps.xlsx')
    apd_fasta_file = os.path.join(data_dir, 'naturalAMPs_APD2024a.fasta.txt')
    
    try:
        print("Cargando bases de datos de DBAASP...")
        # 1. Cargar y procesar DBAASP
        df_dbaasp_pep = pd.read_csv(dbaasp_peptides_file)
        df_dbaasp_hemo = pd.read_csv(dbaasp_hemolytic_file)
        df_dbaasp_act = pd.read_csv(dbaasp_activity_file)
        
        # Limpiar nombre de columna en activity (quitar comillas y espacios)
        # El usuario menciona que hay una columna ' "Salt Type"' que hay que limpiar
        df_dbaasp_act.rename(columns=lambda x: x.strip().replace('"', ''), inplace=True)
        
        # Renombrar 'Peptide ID' a 'ID' para facilitar el merge
        if 'Peptide ID' in df_dbaasp_hemo.columns:
            df_dbaasp_hemo.rename(columns={'Peptide ID': 'ID'}, inplace=True)
        if 'Peptide ID' in df_dbaasp_act.columns:
            df_dbaasp_act.rename(columns={'Peptide ID': 'ID'}, inplace=True)
        
        # Unir los 3 de DBAASP usando 'ID'
        df_dbaasp = pd.merge(df_dbaasp_pep, df_dbaasp_hemo, on='ID', how='outer')
        df_dbaasp = pd.merge(df_dbaasp, df_dbaasp_act, on='ID', how='outer')
        
        # Consolidar la secuencia de DBAASP (puede venir de diferentes archivos)
        # Buscamos las columnas de secuencia posibles
        seq_cols = [col for col in df_dbaasp.columns if 'SEQUENCE' in col.upper()]
        if seq_cols:
            df_dbaasp['Sequence'] = df_dbaasp[seq_cols[0]]
            for col in seq_cols[1:]:
                df_dbaasp['Sequence'] = df_dbaasp['Sequence'].combine_first(df_dbaasp[col])
        else:
            df_dbaasp['Sequence'] = ""
             
        df_dbaasp['Source_DB'] = 'DBAASP'
        
        print("Cargando base de datos DRAMP...")
        # 2. Cargar DRAMP (Excel)
        # Requiere openpyxl instalado (pip install openpyxl)
        df_dramp = pd.read_excel(dramp_file)
        df_dramp['Source_DB'] = 'DRAMP'
        
        print("Cargando base de datos APD3 (FASTA)...")
        # 3. Cargar APD3 (FASTA)
        df_apd = parse_fasta(apd_fasta_file)
        df_apd['Source_DB'] = 'APD3'
        
        print("Normalizando secuencias...")
        # 4. Normalizar secuencias en todos los DataFrames
        df_dbaasp['Sequence_Normalized'] = df_dbaasp['Sequence'].apply(normalize_sequence)
        df_dramp['Sequence_Normalized'] = df_dramp['Sequence'].apply(normalize_sequence)
        df_apd['Sequence_Normalized'] = df_apd['Sequence'].apply(normalize_sequence)
        
        # Eliminar filas sin secuencia normalizada válida (vacías o nulas)
        df_dbaasp = df_dbaasp[df_dbaasp['Sequence_Normalized'] != ""]
        df_dramp = df_dramp[df_dramp['Sequence_Normalized'] != ""]
        df_apd = df_apd[df_apd['Sequence_Normalized'] != ""]
        
        print("Uniendo todas las bases de datos (Outer Join)...")
        # 5. Outer Join usando la secuencia normalizada como llave
        # Primero unimos DBAASP y DRAMP
        df_master = pd.merge(df_dbaasp, df_dramp, on='Sequence_Normalized', how='outer', suffixes=('_DBAASP', '_DRAMP'))
        
        # Luego unimos el resultado con APD3
        df_master = pd.merge(df_master, df_apd, on='Sequence_Normalized', how='outer')
        
        print(f"Guardando resultado final en {output_file}...")
        # 6. Guardar el resultado
        df_master.to_csv(output_file, index=False)
        
        print("¡Proceso completado con éxito!")
        print(f"Total de péptidos únicos (por secuencia): {len(df_master)}")
        
    except FileNotFoundError as e:
        print(f"Error: No se encontró un archivo. Asegúrate de que la carpeta '{data_dir}' exista y contenga los archivos correctos.")
        print(f"Detalle: {e}")
    except pd.errors.EmptyDataError:
        print("Error: Uno de los archivos CSV está vacío o corrupto.")
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrate de tener instaladas las librerías necesarias:")
        print("pip install pandas openpyxl")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()