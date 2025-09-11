# AutoPatch

1. Clonar repo
   ```bash
   git clone <este-repo>
   cd foundry
   ```
2. Crear venv + instalar dependencias
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Ejecutar main.py con ejemplo de `report.json`
   ```bash
   cat > report.json <<'JSON'
   {"vulnerabilities": [{"pkg": "log4j", "version": "1.2.17", "hosts": ["host1"], "cve": "CVE-2025-0001"}]}
   JSON
   python main.py --tenable-file report.json --window "2025-09-15 01:00-06:00"
   ```
4. Revisar salida y PR generado
5. Importar `foundry_agent.yaml` en AI Foundry
