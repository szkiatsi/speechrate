from datetime import datetime
import json
import math
from types import SimpleNamespace
# noinspection PyUnresolvedReferences
from browser import ajax, alert, bind, document, window, html


morae = 0


def on_complete(req):
    global morae
    if req.status == 200 or req.status == 0:
        result = json.loads(req.text)
        morae = [mora for chunk in result for token in chunk for mora in token['morae']
                 if not (token['pos'].startswith('記号,') or not token['morae'])]
        #    ' || '.join([' | '.join([', '.join(token['morae']) for token in chunk]) for chunk in result])
        document['text_result'].value = ', '.join(morae)
        document['text_result'].value += '\nmorae: ' + str(len(morae))
        del document['start_stop'].attrs['disabled']
    else:
        alert('error')


@bind(document['analyze'], 'click')
def analyze(ev):
    req = ajax.ajax()
    req.bind('complete', on_complete)
    req.open('POST', '/api/analyze', True)
    req.set_header('Content-Type', 'application/x-www-form-urlencoded')
    req.send(document['text_original'].value)


line = window.TimeSeries.new()


def process_audio(ev):
    now = datetime.now()

    buf = ev.inputBuffer.getChannelData(0)
    buf_length = buf.length
    sum_ = 0

    for i in range(buf_length):
        x = buf[i]
        sum_ += pow(x, 2)

    rms = math.sqrt(sum_ / buf_length) * 100

    # volume_ = max(rms, volume * averaging)
    volume = round(rms)

    document['volume'].value = volume
    line.append(window.Date.new().getTime(), volume)

    global last_clipped
    global t_pause
    global t_pause_tmp
    global t_talking
    global is_talking
    if not last_clipped:
        if volume > 0:
            is_talking = True
            last_clipped = now
    else:
        t_since_last_clip = (now - last_clipped).microseconds
        if volume > 0:
            if is_talking:
                t_talking += t_since_last_clip
            else:
                t_pause += t_pause_tmp
                t_pause += t_since_last_clip
                t_pause_tmp = 0
                is_talking = True
        else:
            if not is_talking:
                t_pause_tmp += t_since_last_clip
            else:
                t_talking += t_since_last_clip
                is_talking = False
        last_clipped = now

    document['talking'].value = t_talking / 1000000
    document['silence'].value = t_pause / 1000000


def process_stream(stream):
    global gum_stream
    global audio_ctx
    global mic
    global js_node

    global t_pause
    global t_pause_tmp
    global t_talking
    global is_talking
    global last_clipped

    t_pause = 0
    t_pause_tmp = 0
    t_talking = 0
    is_talking = False
    last_clipped = None

    gum_stream = stream
    audio_ctx = window.AudioContext.new()
    js_node = audio_ctx.createScriptProcessor(256, 1, 1)
    js_node.onaudioprocess = process_audio
    mic = audio_ctx.createMediaStreamSource(stream)
    mic.connect(js_node)
    js_node.connect(audio_ctx.destination)


getUserMedia = window.navigator.getUserMedia or window.navigator.webkitGetUserMedia or window.navigator.mozGetUserMedia

if getUserMedia:
    print('getUserMedia supported')
    constraints = SimpleNamespace()
    constraints.audio = {'mandatory': {
        'googEchoCancellation': False,
        'googAutoGainControl': False,
        'googNoiseSuppression': False,
        'googHighpassFilter': False
    }, 'optional': []}

    @bind(document['start_stop'], 'click)
    def start_stop(ev):
        global gum_stream
        global smoothie
        if not gum_stream or not gum_stream.active:
            document['start_stop_text'].text = 'Stop'
            if not smoothie:
                smoothie = window.SmoothieChart.new({'millisPerPixel': 10})
                smoothie.addTimeSeries(line, {'lineWidth': 1, 'strokeStyle': '#ffffff'})
            smoothie.streamTo(document['graph'])
            getUserMedia(constraints, process_stream, lambda err: print('error: {}'.format(err.text)))
        else:
            js_node.disconnect()
            mic.disconnect()
            audio_ctx.close()
            del js_node
            del mic
            del audio_ctx
            gum_stream.getTracks()[0].stop
            del gum_stream
            smoothie.stop()
            document['start_stop_text'].text = 'Start'
            t_all = (t_talking + t_pause) / 1000000
            document['result'].text = \
                f'duration: {t_all}. morae/sec: {len(morae)/t_talking*1000000}, pause ratio: {t_pause/1000000/t_all}'


else:
    print('getUserMedia not supported')





