from datetime import datetime
import json
import math
from types import SimpleNamespace
# noinspection PyUnresolvedReferences
from browser import ajax, alert, bind, document, window, html


jq = window.jQuery

morae = []


def on_complete(req):
    global morae
    if req.status == 200 or req.status == 0:
        result = json.loads(req.text)
        morae = [mora for chunk in result for token in chunk for mora in token['morae']
                 if not (token['pos'].startswith('記号,') or not token['morae'])]
        #    ' || '.join([' | '.join([', '.join(token['morae']) for token in chunk]) for chunk in result])
        document['text_result'].value = ', '.join(morae)
        document['text_result'].value += '\nmorae: ' + str(len(morae))
        document['result'].clear()
        sentence_no = 0
        token_no = 0
        mora_no = 0
        duration = 180

        count_kuten = len([token for chunk in result for token in chunk if token['pos'] == '記号,句点,*,*'])
        count_punc = len([token for chunk in result for token in chunk if token['pos'] != '記号,句点,*,*' and
                          token['pos'].startswith('記号,')])
        pause_kuten = 4
        pause_punc = 2

        speech_rate = len(morae) / duration
        speech_rate_with_pause = (len(morae) + count_kuten * pause_kuten + count_punc * pause_punc) / duration
        document['speech_rate'].clear()
        document['speech_rate'].text = '{0:.2f} morae/min, pause ratio: {1:.2%}'.format(
            speech_rate_with_pause * 60, 1 - speech_rate / speech_rate_with_pause)
        sec_per_mora = 1 / speech_rate_with_pause
        sec_sum = 0
        time_str_tmp = ''

        for chunk in result:
            for token in chunk:
                html_token = html.DIV(Class='token', id=f'token_{token_no}', data_toggle='popover',
                                      data_placement='top', data_content=token['pos'])
                html_times = html.DIV(Class='times')
                html_morae = html.DIV(Class='morae')
                for mora in token['morae']:
                    if token['pos'] == '記号,句点,*,*':
                        time = pause_kuten * sec_per_mora
                    elif token['pos'].startswith('記号,'):
                        time = pause_punc * sec_per_mora
                    else:
                        time = sec_per_mora
                    sec_sum += time
                    time_str = f'{int(sec_sum/60)}:{int(sec_sum%60):02d}'
                    if time_str != time_str_tmp:
                        time_str_tmp = time_str
                    else:
                        time_str = '→'
                    if int(sec_sum%60%5) == 0 and time_str != '→':
                        html_time = html.STRONG()
                        html_time <= html.DIV(time_str, Class='time', id=f'time_{mora_no}')
                    else:
                        html_time = html.DIV(time_str, Class='time', id=f'time_{mora_no}')
                    html_times <= html_time
                    html_morae <= html.DIV(mora, Class='mora', id=f'mora_{mora_no}')
                    mora_no += 1
                html_token <= html_times
                html_token <= html_morae
                html_token <= html.DIV(token['surface'], Class='surface')
                document['result'] <= html_token
        jq('[data-toggle="popover"]').popover()
    else:
        alert('error')


@bind(document['analyze'], 'click')
def analyze(ev):
    req = ajax.ajax()
    req.bind('complete', on_complete)
    req.open('POST', '/api/analyze', True)
    req.set_header('Content-Type', 'application/x-www-form-urlencoded')
    req.send(document['text_original'].value)
