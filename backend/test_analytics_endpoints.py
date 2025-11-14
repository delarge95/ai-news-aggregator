#!/usr/bin/env python3
"""
Script de prueba para verificar los endpoints de analytics
"""

import asyncio
import sys
import os

# Añadir el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_analytics_endpoints():
    """Probar todos los endpoints de analytics"""
    
    client = TestClient(app)
    
    print("🚀 Iniciando pruebas de endpoints de analytics...\n")
    
    # Test 1: Analytics Summary
    print("📊 Test 1: Analytics Summary")
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Summary endpoint funcionando correctamente")
    print(f"   Endpoints disponibles: {len(data['data']['available_endpoints'])}")
    print(f"   Timeframes: {len(data['data']['timeframes_available'])}")
    print()
    
    # Test 2: Dashboard Analytics
    print("📈 Test 2: Dashboard Analytics")
    response = client.get("/api/v1/analytics/dashboard?timeframe=24h&aggregation=daily")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Dashboard endpoint funcionando correctamente")
    print(f"   Métricas incluidas: {list(data['data']['metrics'].keys())}")
    print()
    
    # Test 3: Trends Analytics
    print("📉 Test 3: Trends Analytics")
    response = client.get("/api/v1/analytics/trends?timeframe=7d&aggregation=daily")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Trends endpoint funcionando correctamente")
    print(f"   Datos de volumen: {len(data['data']['volume_trends'])} puntos")
    print()
    
    # Test 4: Topics Analytics
    print("🏷️ Test 4: Topics Analytics")
    response = client.get("/api/v1/analytics/topics?timeframe=30d&min_mentions=1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Topics endpoint funcionando correctamente")
    print(f"   Top topics: {len(data['data']['top_topics'])} elementos")
    print()
    
    # Test 5: Sentiment Analytics
    print("😊 Test 5: Sentiment Analytics")
    response = client.get("/api/v1/analytics/sentiment?timeframe=7d&aggregation=daily")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Sentiment endpoint funcionando correctamente")
    print(f"   Análisis de sentimiento: {len(data['data']['overall_sentiment'])} categorías")
    print()
    
    # Test 6: Sources Analytics
    print("📰 Test 6: Sources Analytics")
    response = client.get("/api/v1/analytics/sources?timeframe=7d&min_articles=1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Sources endpoint funcionando correctamente")
    print(f"   Estadísticas de fuentes: {len(data['data']['source_statistics'])} fuentes")
    print()
    
    # Test 7: Traffic Analytics
    print("🚦 Test 7: Traffic Analytics")
    response = client.get("/api/v1/analytics/traffic?timeframe=24h&aggregation=hourly")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Traffic endpoint funcionando correctamente")
    print(f"   Resumen general incluido: {'overall_summary' in data['data']}")
    print()
    
    # Test 8: Export Analytics
    print("📤 Test 8: Export Analytics")
    response = client.get("/api/v1/analytics/export?report_type=dashboard&timeframe=7d&format=json")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✅ Export endpoint funcionando correctamente")
    print(f"   URL de descarga: {data['data']['download_url']}")
    print()
    
    # Test 9: Diferentes timeframes
    print("⏰ Test 9: Testing diferentes timeframes")
    timeframes = ["1h", "6h", "24h", "7d", "30d", "90d"]
    for timeframe in timeframes:
        response = client.get(f"/api/v1/analytics/dashboard?timeframe={timeframe}")
        assert response.status_code == 200
        print(f"   ✅ Timeframe {timeframe} funcionando")
    print()
    
    # Test 10: Formatos de exportación
    print("💾 Test 10: Testing formatos de exportación")
    formats = ["json", "csv", "xlsx"]
    for format_type in formats:
        response = client.get(f"/api/v1/analytics/dashboard?timeframe=24h&export_format={format_type}")
        assert response.status_code == 200
        print(f"   ✅ Formato {format_type} funcionando")
    print()
    
    print("🎉 ¡Todas las pruebas de analytics completadas exitosamente!")
    print("\n📋 Resumen de endpoints probados:")
    endpoints = [
        "GET /analytics/summary",
        "GET /analytics/dashboard", 
        "GET /analytics/trends",
        "GET /analytics/topics",
        "GET /analytics/sentiment",
        "GET /analytics/sources",
        "GET /analytics/traffic",
        "GET /analytics/export"
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"   {i}. {endpoint}")
    
    print(f"\n✨ Total: {len(endpoints)} endpoints de analytics implementados y funcionando")

if __name__ == "__main__":
    test_analytics_endpoints()