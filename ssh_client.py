import paramiko

def run_ssh_command(ip, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(ip, username=username, password=password, timeout=5)

        stdin, stdout, stderr = client.exec_command(command)

        output = stdout.read().decode()
        error = stderr.read().decode()

        client.close()

        return {
            "output": output,
            "error": error
        }

    except Exception as e:
        return {"error": str(e)}
