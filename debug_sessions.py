#!/usr/bin/env python3
"""
Debug script pre správu uložených sessions
"""
import json
import os
from datetime import datetime

SESSIONS_FILE = "auth/sessions.json"

def show_sessions():
    """Zobrazí všetky aktívne sessions"""
    if not os.path.exists(SESSIONS_FILE):
        print("❌ Žiadny sessions súbor neexistuje")
        return
    
    try:
        with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        if not sessions:
            print("✅ Žiadne uložené sessions")
            return
        
        print(f"📋 Celkom sessions: {len(sessions)}")
        print("-" * 80)
        
        for session_id, session_data in sessions.items():
            user = session_data.get('user', {})
            created = session_data.get('created', '')
            expires = session_data.get('expires', '')
            session_key = session_data.get('session_key', 'N/A')
            
            # Kontrola expiry
            status = "✅ Aktívny"
            if expires:
                try:
                    expires_dt = datetime.fromisoformat(expires)
                    if datetime.now() > expires_dt:
                        status = "⏰ Expirovaný"
                except:
                    status = "❓ Neplatný dátum"
            
            print(f"Session ID: {session_id}")
            print(f"  👤 Používateľ: {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
            print(f"  🏢 Role: {user.get('role', 'N/A')}")
            print(f"  🏙️ Mestá: {user.get('cities', 'N/A')}")
            print(f"  📅 Vytvorený: {created}")
            print(f"  ⏰ Expiruje: {expires}")
            print(f"  🔑 Session Key: {session_key}")
            print(f"  📍 Status: {status}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Chyba pri čítaní sessions: {e}")

def clear_all_sessions():
    """Vymaže všetky sessions"""
    if os.path.exists(SESSIONS_FILE):
        try:
            os.remove(SESSIONS_FILE)
            print("✅ Všetky sessions boli vymazané")
        except Exception as e:
            print(f"❌ Chyba pri mazaní sessions: {e}")
    else:
        print("ℹ️ Žiadne sessions na vymazanie")

def clear_expired_sessions():
    """Vymaže len expirované sessions"""
    if not os.path.exists(SESSIONS_FILE):
        print("ℹ️ Žiadne sessions na vymazanie")
        return
    
    try:
        with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in sessions.items():
            expires_str = session_data.get('expires', '')
            if expires_str:
                try:
                    expires = datetime.fromisoformat(expires_str)
                    if now > expires:
                        expired_sessions.append(session_id)
                except:
                    expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del sessions[session_id]
        
        if expired_sessions:
            with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            print(f"✅ Vymazané {len(expired_sessions)} expirovaných sessions")
        else:
            print("ℹ️ Žiadne expirované sessions na vymazanie")
            
    except Exception as e:
        print(f"❌ Chyba pri čistení sessions: {e}")

if __name__ == "__main__":
    print("🔧 Session Debug Tool")
    print("=" * 50)
    
    while True:
        print("\n📋 Možnosti:")
        print("1. Zobraziť všetky sessions")
        print("2. Vymazať všetky sessions")
        print("3. Vymazať expirované sessions")
        print("4. Ukončiť")
        
        choice = input("\n🎯 Vyberte možnosť (1-4): ").strip()
        
        if choice == "1":
            show_sessions()
        elif choice == "2":
            confirm = input("❓ Skutočne vymazať VŠETKY sessions? (y/N): ").strip().lower()
            if confirm == 'y':
                clear_all_sessions()
        elif choice == "3":
            clear_expired_sessions()
        elif choice == "4":
            print("👋 Ukončujem...")
            break
        else:
            print("❌ Neplatná voľba")
