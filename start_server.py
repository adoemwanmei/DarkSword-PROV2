import sys
sys.path.insert(0, '.')
from darksword.server import run_server
from darksword.config import ServeConfig

print("[START] Starting DarkSword server...")
run_server(ServeConfig(host='0.0.0.0', port=8080, redirect_url=None, custom_host_in_loader=None))
