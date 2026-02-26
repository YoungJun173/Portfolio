import urllib.request
import ssl

proxy = 'http://brd-customer-hl_79cc5ce7-zone-residential_proxy_group_5:9we09i6qly4m@brd.superproxy.io:33335'
url = 'https://geo.brdtest.com/welcome.txt?product=resi&method=native'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
)

try:
    print(opener.open(url).read().decode())
except Exception as e:
    print(f"Error: {e}")
