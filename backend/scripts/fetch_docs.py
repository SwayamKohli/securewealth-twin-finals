import urllib.request

try:
    resp = urllib.request.urlopen('http://127.0.0.1:8000/docs')
    content = resp.read()[:2000]
    print('OK', len(content))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR', type(e).__name__, e)
