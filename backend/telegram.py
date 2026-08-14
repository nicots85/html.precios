"""
Envía pedidos de TechnoStore a Telegram vía API (sin librerías externas).

Cómo funciona:
1. En admin.html → Pedidos, click "Exportar para Telegram".
   Descarga `backend/pedidos_export.json` con los pedidos pendientes.
2. Correr este script en la PC:
       python backend/telegram.py
   Envía los pedidos que aún no se mandaron y guarda el registro en
   `backend/pedidos_enviados.json` (no reenvía duplicados).

Config: token del bot y chat_id en config.json → "telegram"
"""
import json
import os
import time
import sys
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(BASE_DIR), 'config.json')
EXPORT_PATH = os.path.join(BASE_DIR, 'pedidos_export.json')
ENVIADOS_PATH = os.path.join(BASE_DIR, 'pedidos_enviados.json')
API = 'https://api.telegram.org'


def cargar_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def leer_registro_enviados():
    if os.path.exists(ENVIADOS_PATH):
        with open(ENVIADOS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def guardar_registro(ids):
    with open(ENVIADOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)


def llamar_api(token, metodo, params):
    url = f'{API}/bot{token}/{metodo}'
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'ok': False, 'error': body}


def formatear_pedido(o):
    d = o.get('fecha', '')
    try:
        d = time.strftime('%d/%m/%Y %H:%M', time.localtime(time.mktime(time.strptime(d[:19], '%Y-%m-%dT%H:%M:%S'))))
    except Exception:
        pass

    cli = o.get('cliente', {})
    lineas = [f'🛒 *NUEVO PEDIDO* · {o.get("id", "")}', f'📅 {d}', '']

    lineas.append(f'👤 *{cli.get("nombre", "")}*')
    lineas.append(f'📞 {cli.get("telefono", "")}')
    if cli.get('direccion'):
        lineas.append(f'📍 {cli["direccion"]}')
    if cli.get('notas'):
        lineas.append(f'📝 {cli["notas"]}')
    lineas.append('')

    lineas.append('📦 *Items:*')
    for i in o.get('items', []):
        nombre = f'{i.get("marca", "")} {i.get("modelo", "")}'.strip()
        if i.get('calidad'):
            nombre += f' ({i["calidad"]})'
        subtotal = float(i.get('precio', 0)) * int(i.get('qty', 1))
        lineas.append(f'  • {nombre} x{i.get("qty", 1)} = ${subtotal:,.0f}'.replace(',', '.'))

    total = float(o.get('total', 0))
    lineas.append('')
    lineas.append(f'💰 *Total: ${total:,.0f}*'.replace(',', '.'))

    return '\n'.join(lineas)


def enviar_pedido(token, chat_id, o):
    texto = formatear_pedido(o)
    return llamar_api(token, 'sendMessage', {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': 'Markdown'
    })


def main():
    cfg = cargar_config().get('telegram', {})
    token = cfg.get('bot_token', '')
    chat_id = cfg.get('chat_id', '')

    if not token or not chat_id:
        print('Falta configurar Telegram en config.json:')
        print('  "telegram": {')
        print('    "bot_token": "TU_TOKEN_DE_BOTFATHER",')
        print('    "chat_id": "TU_CHAT_ID"')
        print('  }')
        sys.exit(1)

    if not os.path.exists(EXPORT_PATH):
        print(f'No se encontró {EXPORT_PATH}.')
        print('Exportá los pedidos desde admin.html → Pedidos → "Exportar para Telegram".')
        sys.exit(1)

    with open(EXPORT_PATH, 'r', encoding='utf-8') as f:
        pedidos = json.load(f)

    if not isinstance(pedidos, list) or not pedidos:
        print('El archivo de pedidos está vacío.')
        sys.exit(0)

    enviados = leer_registro_enviados()
    nuevos = [p for p in pedidos if p.get('id') not in enviados]

    if not nuevos:
        print('No hay pedidos nuevos para enviar.')
        return

    print(f'Enviando {len(nuevos)} pedido(s) a Telegram...')
    ok_cont = 0
    for p in nuevos:
        res = enviar_pedido(token, chat_id, p)
        if res.get('ok'):
            enviados.append(p['id'])
            ok_cont += 1
            print(f'  ✔ {p["id"]}')
        else:
            print(f'  ✘ {p["id"]}: {res.get("error", "error desconocido")}')

    guardar_registro(enviados)
    print(f'Listo: {ok_cont}/{len(nuevos)} enviados.')


if __name__ == '__main__':
    main()