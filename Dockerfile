FROM python:3.12-slim

WORKDIR /app

COPY requirements-mcp-solar.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_solar_server.py .
COPY solar_productos.csv .
COPY solar_leads.csv .
COPY solar_instalaciones.csv .
COPY solar_citas.csv .

EXPOSE 8000

CMD ["python", "mcp_solar_server.py"]
