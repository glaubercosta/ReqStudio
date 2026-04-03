import socket
import os
import re

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def find_free_port(start, end):
    for port in range(start, end):
        if is_port_free(port):
            return port
    return None

def update_env(api_port, frontend_port):
    env_path = 'reqstudio/.env'
    if not os.path.exists(env_path):
        env_path = '.env'
    
    if not os.path.exists(env_path):
        print("❌ .env not found!")
        return False
        
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if line.startswith('API_PORT='):
            new_lines.append(f'API_PORT={api_port}\n')
        elif line.startswith('FRONTEND_PORT='):
            new_lines.append(f'FRONTEND_PORT={frontend_port}\n')
        elif line.startswith('ALLOWED_ORIGINS='):
             new_lines.append(f'ALLOWED_ORIGINS=http://localhost:{frontend_port},http://localhost:5175\n')
        else:
            new_lines.append(line)
            
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"✅ .env updated: API={api_port}, Frontend={frontend_port}")
    return True

def update_ui_client(api_port):
    client_path = 'reqstudio/reqstudio-ui/src/services/apiClient.ts'
    if not os.path.exists(client_path):
        # Tenta caminho relativo se rodando de dentro de reqstudio
        client_path = 'reqstudio-ui/src/services/apiClient.ts'
    
    if not os.path.exists(client_path):
        print(f"⚠️ UI apiClient.ts not found at {client_path}. Skipping UI patch.")
        return False
        
    with open(client_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r"const API_BASE = import\.meta\.env\.VITE_API_URL \?\? 'http://localhost:\d+'"
    replacement = f"const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:{api_port}'"
    new_content = re.sub(pattern, replacement, content)
    
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ UI apiClient.ts patched to fallback to {api_port}")
    return True

def main():
    print("--- ReqStudio Port Resolver ---")
    
    api_port = find_free_port(8080, 8100)
    frontend_port = find_free_port(5180, 5200)
    
    if not api_port or not frontend_port:
        print("❌ Could not find free ports!")
        return
        
    if update_env(api_port, frontend_port):
        update_ui_client(api_port)
        print("\n🚀 CONFIGURAÇÃO PRONTA!")
        print("Agora rode os comandos abaixo para limpar os conflitos:")
        print(f"1. docker-compose down")
        print(f"2. docker-compose up -d --build --force-recreate")
        print(f"\nSwagger: http://localhost:{api_port}/docs")
        print(f"Frontend: http://localhost:{frontend_port}\n")

if __name__ == "__main__":
    main()
