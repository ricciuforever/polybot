import paramiko

def run_ssh():
    host = '95.217.223.4'
    user = 'root'
    secret = 'hvJbfthkEUaHkKmhF3X4'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Connessione in corso...")
    try:
        ssh.connect(host, username=user, password=secret)
        print("Connesso con successo.")
        
        # Comandi per installare Python 3.9 e 3.10 su Ubuntu (se è Ubuntu/Debian)
        commands = [
            "netstat -anp | grep 5050",
            "ps aux | grep venv/bin/python",
            "cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it && tail -n 10 dashboard_log.txt"
        ]
        
        for cmd in commands:
            print(f"Esecuzione: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # Leggi in streaming l'output per non bloccare
            exit_status = stdout.channel.recv_exit_status()
            print(f"STDOUT: {stdout.read().decode('utf-8')}")
            print(f"STDERR: {stderr.read().decode('utf-8')}")
            print(f"Exit code: {exit_status}\n")

    except Exception as e:
        print(f"Errore SSH: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    run_ssh()
