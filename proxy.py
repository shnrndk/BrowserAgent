from flask import Flask, request, Response, redirect
import requests
import re
import urllib.parse

app = Flask(__name__)
KIWIX_URL = "http://127.0.0.1:22015"
CONTENT_ID = "wikipedia_en_all_maxi_2022-05"

SEARCH_FORM_HTML = f"""
<div id="simpleSearch" style="padding:10px;background:#f8f9fa;border-bottom:1px solid #a2a9b1;margin-bottom:10px;">
    <form action="/wiki/search" method="get">
        <input type="hidden" name="content" value="{CONTENT_ID}">
        <input type="text" name="pattern" id="searchInput" placeholder="Search Wikipedia" style="padding:5px;width:300px;">
        <button type="submit" id="searchButton" style="padding:5px;">Search</button>
    </form>
</div>
"""

def rewrite_html(html_bytes):
    # Try decoding
    try:
        html = html_bytes.decode('utf-8')
    except:
        return html_bytes
        
    # Rewrite links
    html = html.replace('href="/search', 'href="/wiki/search')
    html = html.replace('href="/random', 'href="/wiki/random')
    html = html.replace(f'href="/{CONTENT_ID}', f'href="/wiki/{CONTENT_ID}')
    html = html.replace(f'src="/{CONTENT_ID}', f'src="/wiki/{CONTENT_ID}')
    
    # Also catch root paths
    html = html.replace('href="/', 'href="/wiki/')
    html = html.replace('src="/-/mw/', 'src="/wiki/-/mw/')
    
    # Inject search bar into articles
    if '<div id="mw-mf-page-center">' in html:
        html = html.replace('<div id="mw-mf-page-center">', SEARCH_FORM_HTML + '<div id="mw-mf-page-center">', 1)
    # Inject search bar into search results page
    elif '<body' in html:
        # insert right after body tag
        html = re.sub(r'(<body[^>]*>)', r'\1' + SEARCH_FORM_HTML, html, count=1)
        
    return html.encode('utf-8')

@app.route('/wiki/search')
def proxy_search():
    # Forward to kiwix search
    pattern = request.args.get('pattern', '')
    start = request.args.get('start', '0')
    target_url = f"{KIWIX_URL}/search?pattern={urllib.parse.quote(pattern)}&content={CONTENT_ID}&start={start}"
    resp = requests.get(target_url)
    modified = rewrite_html(resp.content)
    return Response(modified, resp.status_code, content_type=resp.headers.get('content-type', 'text/html'))

@app.route('/wiki/<path:path>')
def proxy_wiki(path):
    # Forward everything else to Kiwix /content/ (if it doesn't already start with content or -)
    if not path.startswith('content/') and not path.startswith('-/'):
        target_url = f"{KIWIX_URL}/content/{path}"
    else:
        target_url = f"{KIWIX_URL}/{path}"
        
    resp = requests.get(target_url)
    content_type = resp.headers.get('content-type', '')
    
    if 'text/html' in content_type:
        modified = rewrite_html(resp.content)
        return Response(modified, resp.status_code, content_type=content_type)
    else:
        return Response(resp.content, resp.status_code, content_type=content_type)

@app.route('/')
def index():
    return redirect(f"/wiki/content/{CONTENT_ID}/A/User%3AThe_other_Kiwix_guy/Landing")

if __name__ == '__main__':
    print("Starting Wikipedia Adapter Proxy on port 8888...")
    app.run(host='0.0.0.0', port=8888, threaded=True)
