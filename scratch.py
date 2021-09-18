
"""
Links to canvas resources

https://github.com/ucfopen/canvasapi
https://github.com/unsupported/canvas/tree/master/canvas_data/sync_canvas_data/python

"""


def dom_test():
    html = """
    <html>
    <head>
    <title>
    </head>
    <body>
        <a href="https://google.com/?q=python">Search for python</a>
    </body>
    </html>
    """

    from bs4 import BeautifulSoup
    import lxml

    soup = BeautifulSoup(html, 'lxml')

    #print(list(soup.children[0]))    

    a_tags = soup.find_all('a', href=True)

    for a_tag in a_tags:
        print(a_tag)
        print(a_tag.get_text())
        print(a_tag["href"])
        # Make a new tag
        q_tag = soup.new_tag("q", cite=a_tag['href'])
        a_tag["href2"] = a_tag["href"]
        a_tag["href"] = "https://smcurl/"
        if 'href3' in a_tag and a_tag['href3'] == "1":
            print("!")
        a_tag.append(q_tag)
        print(a_tag)
        print(soup)

    flicker = 'https://flic.kr/p/5EZVCZ'


    import pdfkit
    headers = [
        ('User-Agent', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0')
        #('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36')
    ]
    #    ('sec-ch-ua', '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"'),
    #    ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'),
    #    ('accept-language', 'en-US,en;q=0.9,es;q=0.8'),
    #    ('cache-control', 'no-cache'),
    #    ('pragma', 'no-cache'),
    #    (''),
    #    ]
    options = {
        'custom-header': headers,
        #'custom-header-propagation':''
        }
    pdfkit.from_url(flicker, "test.pdf", options=options)



dom_test()
