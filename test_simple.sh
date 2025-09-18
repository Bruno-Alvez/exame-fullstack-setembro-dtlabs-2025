#!/bin/bash

# Teste simples de WebSocket com curl
echo "🧪 TESTE SIMPLES DE WEBSOCKET"
echo "================================"

# Substitua pelo seu token
TOKEN="SEU_TOKEN_AQUI"
DEVICE_ID="05c4010d-2c55-400f-9216-9d77f93b164c"

echo "📡 Enviando heartbeat com CPU alta..."

# Enviar heartbeat
curl -X POST "http://localhost:8000/api/v1/heartbeats/$DEVICE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_usage": 90,
    "ram_usage": 60,
    "temperature": 45,
    "free_disk_space": 70,
    "dns_latency": 50,
    "connectivity": true
  }'

echo ""
echo "✅ Heartbeat enviado!"
echo "🔔 Verifique os logs do backend para confirmar que o alerta foi disparado"
echo "📊 Ou use o endpoint GET /api/v1/alerts para ver se o alerta está triggered"
