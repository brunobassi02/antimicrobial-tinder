import pandas as pd
import os

# Carpeta donde están tus datos
DATA_FOLDER = "data_raw"

def inspect_files():
    print("--- INICIO DE INSPECCIÓN ALCOA+ ---\n")
    
    # Listar archivos en la carpeta
    files = os.listdir(DATA_FOLDER)
    
    for file in files:
        path = os.path.join(DATA_FOLDER, file)
        print(f"📄 Analizando: {file}")
        
        try:
            # Caso para CSV (DBAASP)
            if file.endswith('.csv'):
                df = pd.read_csv(path, nrows=1) # Leemos solo la primera fila
                print(f"   Columnas encontradas: {df.columns.tolist()}\n")
            
            # Caso para Excel (DRAMP)
            elif file.endswith('.xlsx'):
                df = pd.read_excel(path, nrows=1)
                print(f"   Columnas encontradas: {df.columns.tolist()}\n")
            
            # Caso para FASTA (APD3)
            elif file.endswith('.fasta'):
                with open(path, 'r') as f:
                    first_lines = [next(f) for _ in range(2)]
                    print(f"   Ejemplo de cabecera FASTA: {first_lines[0].strip()}")
                    print(f"   Ejemplo de secuencia: {first_lines[1].strip()[:20]}...\n")
                    
        except Exception as e:
            print(f"   ❌ Error al leer {file}: {e}\n")

if __name__ == "__main__":
    inspect_files()