#!/usr/bin/env python3
"""
Script para testar WebSocket de alertas
"""
import asyncio
import websockets
import json
import requests
import sys

async def test_websocket_alerts():
    # Configurações
    BASE_URL = "http://localhost:8000"
    WS_URL = "ws://localhost:8000/ws/user"
    DEVICE_ID = "05c4010d-2c55-400f-9216-9d77f93b164c"
    
    # Token de autenticação (substitua pelo seu)
    TOKEN = input("Digite seu token de autenticação: ").strip()
    
    if not TOKEN:
        print("❌ Token é obrigatório!")
        return
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🔌 Conectando ao WebSocket...")
    
    try:
        # Conectar ao WebSocket
        async with websockets.connect(
            WS_URL,
            extra_headers={"Authorization": f"Bearer {TOKEN}"}
        ) as websocket:
            print("✅ WebSocket conectado!")
            print("⏳ Aguardando notificações...")
            
            # Enviar heartbeat que deve disparar alerta
            print("📡 Enviando heartbeat com CPU alta...")
            
            heartbeat_data = {
                "cpu_usage": 90,  # CPU alta para disparar alerta
                "ram_usage": 60,
                "temperature": 45,
                "free_disk_space": 70,
                "dns_latency": 50,
                "connectivity": True
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/heartbeats/{DEVICE_ID}",
                headers=headers,
                json=heartbeat_data
            )
            
            if response.status_code == 201:
                print("✅ Heartbeat enviado com sucesso!")
                print("🔔 Aguardando notificação de alerta...")
                
                # Aguardar notificação por 10 segundos
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    print("🎉 NOTIFICAÇÃO RECEBIDA!")
                    print("=" * 50)
                    print(f"Tipo: {data.get('type')}")
                    print(f"Timestamp: {data.get('timestamp')}")
                    
                    if data.get('type') == 'alert_triggered':
                        alert_data = data.get('data', {})
                        print(f"🚨 Alerta: {alert_data.get('name')}")
                        print(f"📱 Device: {alert_data.get('device_name')}")
                        print(f"📊 Condições: {alert_data.get('conditions_summary')}")
                        print(f"💻 CPU: {alert_data.get('heartbeat_data', {}).get('cpu_usage')}%")
                        print("=" * 50)
                        print("✅ TESTE WEBSOCKET PASSOU!")
                    else:
                        print(f"📨 Mensagem recebida: {data}")
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout - Nenhuma notificação recebida em 10 segundos")
                    print("❌ Possível problema no sistema de alertas")
                    
            else:
                print(f"❌ Erro ao enviar heartbeat: {response.status_code}")
                print(f"Resposta: {response.text}")
                
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")

if __name__ == "__main__":
    print("🧪 TESTE DE WEBSOCKET - SISTEMA DE ALERTAS")
    print("=" * 50)
    asyncio.run(test_websocket_alerts())
