import json
import sys
if sys.implementation.name == 'brython':
    # noinspection PyUnresolvedReferences
    from browser import ajax, alert, bind, document, html
else:
    from mockbrython.browser import ajax, bind, alert, document, html


def on_complete(req):
    if req.status == 200 or req.status == 0:
        result = json.loads(req.text)
        document['text_result'].value = \
            ' || '.join([' | '.join([', '.join(token['morae']) for token in chunk]) for chunk in result])
    else:
        alert('error')


@bind(document['analyze'], 'click')
def analyze(ev):
    req = ajax.ajax()
    req.bind('complete', on_complete)
    req.open('POST', '/api/analyze', True)
    req.set_header('Content-Type', 'application/x-www-form-urlencoded')
    req.send(document['text_original'].value)
