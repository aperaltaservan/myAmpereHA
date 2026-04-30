#!/usr/bin/env python3
import argparse
import html
import json
import os
import socket
import struct
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = '172.16.0.220'
DEFAULT_PORT = 502
DEFAULT_UNIT = 1
DEFAULT_FUNC = 4
DEFAULT_START = 0
DEFAULT_COUNT = 50
DEFAULT_WEB_PORT = 8787
DEFAULT_NAMES_FILE = '/home/aperalta/.openclaw/workspace/state/modbus_register_names.json'


def recv_exact(sock, size):
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            break
        data += chunk
    return data


def modbus_read_registers(host, port, unit, func, start, count, timeout=3.0):
    tid = int(time.time() * 1000) & 0xFFFF
    pdu = struct.pack('>BHH', func, start, count)
    mbap = struct.pack('>HHHB', tid, 0, len(pdu) + 1, unit)
    req = mbap + pdu
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.sendall(req)
        header = recv_exact(s, 7)
        if len(header) < 7:
            raise RuntimeError('cabecera Modbus incompleta')
        _tid, _pid, length, _unit = struct.unpack('>HHHB', header)
        body = recv_exact(s, length - 1)
        if not body:
            raise RuntimeError('respuesta Modbus vacía')
        if body[0] == (func | 0x80):
            code = body[1] if len(body) > 1 else 'desconocido'
            raise RuntimeError(f'excepción Modbus {code}')
        if body[0] != func:
            raise RuntimeError(f'función inesperada {body[0]}')
        byte_count = body[1]
        data = body[2:2 + byte_count]
        return [struct.unpack('>H', data[i:i + 2])[0] for i in range(0, len(data), 2)]
    finally:
        s.close()


def u16_to_s16(value):
    return value - 65536 if value >= 32768 else value


def safe_float(raw):
    try:
        value = struct.unpack('>f', raw)[0]
        if value != value:
            return 'NaN'
        if value == float('inf'):
            return 'inf'
        if value == float('-inf'):
            return '-inf'
        return f'{value:.6g}'
    except Exception:
        return 'n/a'


def pair_to_views(a, b):
    raw = struct.pack('>HH', a, b)
    raw_swapped = struct.pack('>HH', b, a)
    return {
        'u32_be': struct.unpack('>I', raw)[0],
        's32_be': struct.unpack('>i', raw)[0],
        'f32_be': safe_float(raw),
        'u32_swap': struct.unpack('>I', raw_swapped)[0],
        's32_swap': struct.unpack('>i', raw_swapped)[0],
        'f32_swap': safe_float(raw_swapped),
        'ascii': ''.join(chr(c) if 32 <= c < 127 else '.' for c in raw),
    }


def ensure_parent(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_names(path):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return {}


def save_names(path, names):
    ensure_parent(path)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(names, fh, ensure_ascii=False, indent=2, sort_keys=True)


def redirect(handler, location):
    handler.send_response(303)
    handler.send_header('Location', location)
    handler.send_header('Content-Length', '0')
    handler.send_header('Connection', 'close')
    handler.end_headers()


def build_data_payload(params, names):
    rows = []
    pair_rows = []
    error = None
    fetched_at = None
    try:
        regs = modbus_read_registers(params['host'], params['port'], params['unit'], params['func'], params['start'], params['count'])
        fetched_at = time.strftime('%Y-%m-%d %H:%M:%S')
        for idx, value in enumerate(regs):
            reg = params['start'] + idx
            hi = (value >> 8) & 0xFF
            lo = value & 0xFF
            signed = u16_to_s16(value)
            rows.append({
                'reg': reg,
                'name': names.get(str(reg), ''),
                'u16': value,
                's16': signed,
                'div10': f'{value / 10:.1f}',
                'div100': f'{value / 100:.2f}',
                'div1000': f'{value / 1000:.3f}',
                'sdiv10': f'{signed / 10:.1f}',
                'sdiv100': f'{signed / 100:.2f}',
                'sdiv1000': f'{signed / 1000:.3f}',
                'hex': hex(value),
                'ascii': ''.join(chr(c) if 32 <= c < 127 else '.' for c in [hi, lo]),
            })
        for idx in range(0, len(regs) - 1, 2):
            a, b = regs[idx], regs[idx + 1]
            pair_rows.append({'regs': f'{params["start"] + idx}-{params["start"] + idx + 1}', **pair_to_views(a, b)})
    except Exception as exc:
        error = str(exc)
    return {'rows': rows, 'pair_rows': pair_rows, 'error': error, 'fetched_at': fetched_at}


def render_page(params, payload, names_path):
    rows = payload['rows']
    pair_rows = payload['pair_rows']
    error = payload['error']
    fetched_at = payload['fetched_at']
    params_json = html.escape(json.dumps({k: params[k] for k in ['host', 'port', 'unit', 'func', 'start', 'count', 'refresh']}))
    export_url = '/names.json'
    host = html.escape(params['host'])
    func_label = 'Input Registers (FC04)' if params['func'] == 4 else 'Holding Registers (FC03)'
    qs = html.escape(params['query_string'])

    def row_html(row):
        reg = row['reg']
        current_name = html.escape(row.get('name', ''))
        return (
            '<tr>'
            f'<td>{reg}</td>'
            f'<td class="name">{current_name or "—"}</td>'
            f'<td>{row["u16"]}</td>'
            f'<td>{row["s16"]}</td>'
            f'<td>{row["div10"]}</td>'
            f'<td>{row["div100"]}</td>'
            f'<td>{row["div1000"]}</td>'
            f'<td>{row["sdiv10"]}</td>'
            f'<td>{row["sdiv100"]}</td>'
            f'<td>{row["sdiv1000"]}</td>'
            f'<td>{row["hex"]}</td>'
            f'<td><code>{html.escape(row["ascii"])}</code></td>'
            '<td>'
            '<form method="post" action="/save-name" class="rowform">'
            f'<input type="hidden" name="reg" value="{reg}" />'
            f'<input type="hidden" name="return_to" value="{qs}" />'
            f'<input type="text" name="name" value="{current_name}" placeholder="ej. Producción solar" />'
            '<button type="submit">Guardar</button>'
            '</form>'
            '</td>'
            '</tr>'
        )

    def pair_html(row):
        return (
            '<tr>'
            f'<td>{row["regs"]}</td>'
            f'<td>{row["u32_be"]}</td>'
            f'<td>{row["s32_be"]}</td>'
            f'<td>{row["f32_be"]}</td>'
            f'<td>{row["u32_swap"]}</td>'
            f'<td>{row["s32_swap"]}</td>'
            f'<td>{row["f32_swap"]}</td>'
            f'<td><code>{html.escape(row["ascii"])}</code></td>'
            '</tr>'
        )

    parts = [
        '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        '<title>Monitor Modbus</title>',
        '<style>',
        'body{font-family:Arial,Helvetica,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}',
        '.wrap{max-width:1500px;margin:0 auto}',
        '.card{background:#111827;border:1px solid #334155;border-radius:14px;padding:18px;margin-bottom:18px}',        'input,select,button{background:#0b1220;color:#e2e8f0;border:1px solid #475569;border-radius:8px;padding:8px 10px}',
        'input[type=text]{min-width:220px}',
        'table{width:100%;border-collapse:collapse;font-size:14px}',
        'th,td{border:1px solid #334155;padding:8px;vertical-align:top}',
        'th{background:#1e293b}',
        '.muted{color:#94a3b8}', '.err{color:#fca5a5;font-weight:bold}', '.ok{color:#86efac}','.name{font-weight:700;color:#f8fafc}', '.rowform{display:flex;gap:8px;align-items:center;flex-wrap:wrap}',
        '.status{min-height:24px}', 'code{color:#f8fafc}', 'a{color:#93c5fd}',
        '</style></head><body><div class="wrap">',
        '<div class="card">',
        '<h1 style="margin-top:0">Monitor Modbus TCP</h1>',
        '<form method="get">',
        f'Host <input name="host" value="{host}" /> ',
        f'Puerto <input name="port" type="number" value="{params["port"]}" style="width:90px" /> ',
        f'Unit ID <input name="unit" type="number" value="{params["unit"]}" style="width:80px" /> ',
        'Función <select name="func">',
        f'<option value="4"{" selected" if params["func"] == 4 else ""}>FC04 Input</option>',
        f'<option value="3"{" selected" if params["func"] == 3 else ""}>FC03 Holding</option>',
        '</select> ',
        f'Inicio <input name="start" type="number" value="{params["start"]}" style="width:90px" /> ',
        f'Cantidad <input name="count" type="number" value="{params["count"]}" style="width:90px" /> ',
        f'Refresh (s) <input name="refresh" type="number" value="{params["refresh"]}" style="width:80px" /> ',
        '<button type="submit">Leer</button> <button type="button" onclick="refreshData(true)">Refresco inmediato</button>',
        '</form>',
        f'<p class="muted">Equipo: <code>{host}:{params["port"]}</code> · unidad <code>{params["unit"]}</code> · {func_label}</p>',
        f'<p class="muted">Alias guardados en <code>{html.escape(names_path)}</code> · <a href="{export_url}">exportar JSON</a></p>',
        '<h2 style="margin:18px 0 8px 0">Añadir alias manual</h2>',
        '<form method="post" action="/save-name-manual" class="rowform">',
        '<label>Registro <input name="reg" type="number" min="0" step="1" placeholder="ej. 9" style="width:120px" /></label> ',
        '<label>Nombre <input name="name" type="text" placeholder="ej. Producción solar" /></label> ',
        f'<input type="hidden" name="return_to" value="{qs}" />',
        '<button type="submit">Guardar alias manual</button>',
        '</form>',
        f'<p id="statusLine" class="{"err" if error else "ok"} status">' + (f'Error: {html.escape(error)}' if error else f'Lectura OK · {len(rows)} registros · {html.escape(fetched_at or "")}') + '</p>',
        '</div>',
        '<div class="card"><h2 style="margin-top:0">Vista registro a registro</h2><table>',
        '<thead><tr><th>Reg</th><th>Nombre</th><th>u16</th><th>s16</th><th>/10</th><th>/100</th><th>/1000</th><th>s/10</th><th>s/100</th><th>s/1000</th><th>hex</th><th>ascii</th><th>Guardar alias</th></tr></thead>',
        '<tbody id="rowsBody">',
        ''.join(row_html(row) for row in rows),
        '</tbody></table></div>',
        '<div class="card"><h2 style="margin-top:0">Vista por pares (32-bit / float / swap)</h2><table>',
        '<thead><tr><th>Regs</th><th>u32 BE</th><th>s32 BE</th><th>f32 BE</th><th>u32 swap</th><th>s32 swap</th><th>f32 swap</th><th>ascii</th></tr></thead>',
        '<tbody id="pairsBody">',
        ''.join(pair_html(row) for row in pair_rows),
        '</tbody></table></div>',        '<div class="card"><h2 style="margin-top:0">Alias guardados</h2><table><tbody id="namesBody">',
    ]
    for reg, name in sorted(load_names(names_path).items(), key=lambda item: int(item[0])):
        parts.append(f'<tr><td>{reg}</td><td>{html.escape(name)}</td></tr>')
        parts.extend([
        '</tbody></table></div>',
        '<div class="card"><h2 style="margin-top:0">Pistas rápidas</h2><ul>',
        '<li><strong>SOC</strong>: suele oler a valor entero con escala <code>/10</code>.</li>',
        '<li><strong>Potencias</strong>: muchas veces salen en W directos o con escala <code>/10</code>.</li>',
        '<li><strong>Texto</strong>: en ASCII se ve rápido si una zona guarda hostname, versión, etc.</li>',
        '<li><strong>32-bit</strong>: mira la tabla de pares por si una magnitud está partida en dos registros.</li>',
        '</ul></div>',
        f'''<script>
const params = JSON.parse('{params_json}');
function esc(v) {{ return String(v ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'); }}
function currentQS() {{ return new URLSearchParams(params).toString(); }}
function rowHtml(row) {{ const currentName=row.name||''; return `<tr><td>${{row.reg}}</td><td class="name">${{esc(currentName||'—')}}</td><td>${{esc(row.u16)}}</td><td>${{esc(row.s16)}}</td><td>${{esc(row.div10)}}</td><td>${{esc(row.div100)}}</td><td>${{esc(row.div1000)}}</td><td>${{esc(row.sdiv10)}}</td><td>${{esc(row.sdiv100)}}</td><td>${{esc(row.sdiv1000)}}</td><td>${{esc(row.hex)}}</td><td><code>${{esc(row.ascii)}}</code></td><td><form method="post" action="/save-name" class="rowform"><input type="hidden" name="reg" value="${{row.reg}}" /><input type="hidden" name="return_to" value="${{esc(currentQS())}}" /><input type="text" name="name" value="${{esc(currentName)}}" placeholder="ej. Producción solar" /><button type="submit">Guardar</button></form></td></tr>`; }}
function pairHtml(row) {{ return `<tr><td>${{esc(row.regs)}}</td><td>${{esc(row.u32_be)}}</td><td>${{esc(row.s32_be)}}</td><td>${{esc(row.f32_be)}}</td><td>${{esc(row.u32_swap)}}</td><td>${{esc(row.s32_swap)}}</td><td>${{esc(row.f32_swap)}}</td><td><code>${{esc(row.ascii)}}</code></td></tr>`; }}
function namesHtml(names) {{ return names.map(n => `<tr><td>${{esc(n.register)}}</td><td>${{esc(n.name)}}</td></tr>`).join(''); }}
async function refreshData(manual=false) {{
  try {{
    const res = await fetch('/data.json?' + currentQS(), {{cache:'no-store'}});
    const data = await res.json();
    const status = document.getElementById('statusLine');
    if (data.error) {{ status.className='err status'; status.textContent='Error: ' + data.error; return; }}
    document.getElementById('rowsBody').innerHTML = data.rows.map(rowHtml).join('');
    document.getElementById('pairsBody').innerHTML = data.pair_rows.map(pairHtml).join('');
    document.getElementById('namesBody').innerHTML = namesHtml(data.names);
    status.className='ok status';
    status.textContent = `Lectura OK · ${{data.rows.length}} registros · ${{data.fetched_at}}` + (manual ? ' · refresco manual' : '');
  }} catch (e) {{
    const status = document.getElementById('statusLine');
    status.className='err status';
    status.textContent = 'Error: ' + e;
  }}
}}
document.addEventListener('keydown', (e) => {{ if (e.key === 'r' || e.key === 'R') refreshData(true); }});
if (params.refresh > 0) setInterval(() => refreshData(false), params.refresh * 1000);
</script>''',
        '</div></body></html>'
    ])
    return ''.join(parts).encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def get_params(self, parsed):        
        qs = urllib.parse.parse_qs(parsed.query)
        return {
            'host': qs.get('host', [self.server.cfg['host']])[0],
            'port': int(qs.get('port', [self.server.cfg['port']])[0]),
            'unit': int(qs.get('unit', [self.server.cfg['unit']])[0]),
            'func': int(qs.get('func', [self.server.cfg['func']])[0]),
            'start': int(qs.get('start', [self.server.cfg['start']])[0]),
            'count': int(qs.get('count', [self.server.cfg['count']])[0]),
            'refresh': int(qs.get('refresh', [self.server.cfg['refresh']])[0]),'query_string': parsed.query or urllib.parse.urlencode({
                'host': self.server.cfg['host'], 'port': self.server.cfg['port'], 'unit': self.server.cfg['unit'],
                'func': self.server.cfg['func'], 'start': self.server.cfg['start'], 'count': self.server.cfg['count'], 'refresh': self.server.cfg['refresh'],
            }),
        }

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/names.json':
            return self.serve_names_json()
        if parsed.path == '/data.json':
            return self.serve_data_json(parsed)
        params = self.get_params(parsed)
        payload = build_data_payload(params, self.server.names)
        body = render_page(params, payload, self.server.names_path)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ('/save-name', '/save-name-manual'):
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)
        reg = data.get('reg', [''])[0].strip()
        name = data.get('name', [''])[0].strip()
        return_to = data.get('return_to', [''])[0].strip()
        if reg:
            if name:
                self.server.names[reg] = name
            else:
                self.server.names.pop(reg, None)
            save_names(self.server.names_path, self.server.names)
        redirect(self, '/?' + return_to if return_to else '/')

    def serve_names_json(self):
        payload = {
            'host': self.server.cfg['host'], 'port': self.server.cfg['port'], 'unit': self.server.cfg['unit'], 'func': self.server.cfg['func'],
            'names': [{'register': int(reg), 'name': name} for reg, name in sorted(self.server.names.items(), key=lambda item: int(item[0]))]
        }
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_data_json(self, parsed):
        params = self.get_params(parsed)
        payload = build_data_payload(params, self.server.names)
        payload['names'] = [{'register': int(reg), 'name': name} for reg, name in sorted(self.server.names.items(), key=lambda item: int(item[0]))]
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description='Monitor web simple para Modbus TCP')
    parser.add_argument('--host', default=DEFAULT_HOST)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--unit', type=int, default=DEFAULT_UNIT)
    parser.add_argument('--func', type=int, default=DEFAULT_FUNC, choices=[3, 4])
    parser.add_argument('--start', type=int, default=DEFAULT_START)
    parser.add_argument('--count', type=int, default=DEFAULT_COUNT)
    parser.add_argument('--web-port', type=int, default=DEFAULT_WEB_PORT)
    parser.add_argument('--refresh', type=int, default=3)
    parser.add_argument('--names-file', default=DEFAULT_NAMES_FILE)
    args = parser.parse_args()

    httpd = ThreadingHTTPServer(('0.0.0.0', args.web_port), Handler)
    httpd.cfg = {'host': args.host, 'port': args.port, 'unit': args.unit, 'func': args.func, 'start': args.start, 'count': args.count, 'refresh': args.refresh}
    httpd.names_path = args.names_file
    httpd.names = load_names(args.names_file)
    print(f'Monitor disponible en http://0.0.0.0:{args.web_port} (equipo Modbus {args.host}:{args.port}, unit {args.unit})')
    print(f'Alias JSON: {args.names_file}')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
