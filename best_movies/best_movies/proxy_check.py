import urllib.request
import ssl

proxy = 'http://brd-customer-hl_79cc5ce7-zone-datacenter_proxy_jun:qa33fpbgpo7o@brd.superproxy.io:33335'
url = 'https://geo.brdtest.com/welcome.txt?product=dc&method=native'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
)

try:
    print(opener.open(url).read().decode())
except Exception as e:
    print(f"Error: {e}")
