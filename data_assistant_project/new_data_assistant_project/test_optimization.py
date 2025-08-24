#!/usr/bin/env python3
"""
Einfacher Test für die optimierten Agenten
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_react_agent():
    """Test ReAct Agent Optimierung"""
    print("🔬 Teste ReAct Agent...")
    
    try:
        from src.agents.ReAct_agent import ReActAgent
        from src.utils.my_config import MyConfig
        
        # Test initialization
        config = MyConfig()
        db_config = config.get_postgres_config()
        
        print("  ✅ Import erfolgreich")
        
        # Test agent creation with caching enabled
        start_time = time.time()
        agent = ReActAgent(database_config=db_config, enable_caching=True)
        init_time = time.time() - start_time
        
        print(f"  ✅ Agent initialisiert in {init_time:.2f}s")
        
        # Test a simple query
        test_query = "Show me available tables"
        start_time = time.time()
        result = agent.execute_query(test_query)
        query_time = time.time() - start_time
        
        print(f"  ✅ Query ausgeführt in {query_time:.3f}s")
        print(f"  📊 Query erfolgreich: {'Ja' if result.success else 'Nein'}")
        
        # Test performance stats
        if hasattr(agent, 'get_performance_stats'):
            stats = agent.get_performance_stats()
            print(f"  📈 Performance Stats verfügbar: {len(stats)} Metriken")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return False

def test_clt_cft_agent():
    """Test CLT-CFT Agent Optimierung"""
    print("\n🧠 Teste CLT-CFT Agent...")
    
    try:
        from src.agents.clt_cft_agent import CLTCFTAgent
        from src.utils.my_config import MyConfig
        
        # Test initialization
        config = MyConfig()
        db_config = config.get_postgres_config()
        
        print("  ✅ Import erfolgreich")
        
        # Test agent creation with caching
        start_time = time.time()
        agent = CLTCFTAgent(database_config=db_config, enable_caching=True)
        init_time = time.time() - start_time
        
        print(f"  ✅ Agent initialisiert in {init_time:.2f}s")
        
        # Test a simple assessment
        test_query = "Show me top sales"
        start_time = time.time()
        result, explanation = agent.execute_query("test_user", test_query)
        execution_time = time.time() - start_time
        
        print(f"  ✅ Assessment/Query in {execution_time:.3f}s")
        print(f"  📊 Query erfolgreich: {'Ja' if result.success else 'Nein'}")
        print(f"  💡 Erklärung generiert: {'Ja' if explanation else 'Nein'}")
        
        # Test performance stats
        if hasattr(agent, 'get_performance_stats'):
            stats = agent.get_performance_stats()
            print(f"  📈 Performance Stats verfügbar: {len(stats)} Metriken")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Haupttest"""
    print("🚀 OPTIMIERUNGSTEST")
    print("=" * 50)
    
    react_success = test_react_agent()
    clt_success = test_clt_cft_agent()
    
    print("\n📋 ZUSAMMENFASSUNG:")
    print(f"  ReAct Agent: {'✅ OK' if react_success else '❌ FEHLER'}")
    print(f"  CLT-CFT Agent: {'✅ OK' if clt_success else '❌ FEHLER'}")
    
    if react_success and clt_success:
        print("\n🎉 Alle Optimierungen funktionieren erfolgreich!")
    else:
        print("\n⚠️  Einige Optimierungen haben Probleme.")
    
    return react_success and clt_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
