#!/usr/bin/env python3
"""
Script para testar se o token está funcionando
"""
import requests
import json

def test_token():
    # Seu token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhOWY2ZjlkMi1lMDk0LTQxNDctYTMxZi00ZDc1ZWFmZWM2ZGUiLCJleHAiOjE3NTgxNTkyNjIsInR5cGUiOiJhY2Nlc3MifQ.E8DXPq2HsJsL8TCUONcoayu9QYD_QJG19VJf34oHBX4"
    
    print("🧪 TESTANDO TOKEN")
    print("=" * 50)
    
    # Teste 1: Verificar se o token funciona em endpoint normal
    print("📡 Testando token em endpoint normal...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token válido! Usuário: {user_data.get('email')}")
            print(f"User ID: {user_data.get('id')}")
        else:
            print(f"❌ Token inválido: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 50)
    
    # Teste 2: Verificar se o token está expirado
    print("⏰ Verificando expiração do token...")
    
    try:
        import jwt
        from datetime import datetime
        
        # Decodificar sem verificar assinatura para ver o payload
        payload = jwt.decode(token, options={"verify_signature": False})
        
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            
            print(f"Token expira em: {exp_date}")
            print(f"Data atual: {now}")
            
            if exp_date > now:
                print("✅ Token ainda válido")
            else:
                print("❌ Token expirado!")
        else:
            print("❌ Token sem data de expiração")
            
    except Exception as e:
        print(f"❌ Erro ao verificar expiração: {e}")

if __name__ == "__main__":
    test_token()
