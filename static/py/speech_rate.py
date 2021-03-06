from datetime import datetime
import json
import math
from types import SimpleNamespace
# noinspection PyUnresolvedReferences
from browser import ajax, alert, bind, document, window, html


morae = []


def on_complete(req):
    global morae
    if req.status == 200 or req.status == 0:
        result = json.loads(req.text)
        morae = [mora for chunk in result for token in chunk for mora in token['morae']
                 if not (token['pos'].startswith('記号,') or not token['morae'])]
        #    ' || '.join([' | '.join([', '.join(token['morae']) for token in chunk]) for chunk in result])
        document['text_result'].value = ', '.join(morae)
        document['morae'].clear()
        document['morae'].text = str(len(morae))
        # document['modal_sentence'].text += document['text_original'].value
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


class SpeechRate(object):
    def __init__(self, volume_threshold=10, time_threshold=0):
        self.t_pause = 0
        self.t_pause_tmp = 0
        self.t_talking = 0
        self.is_talking = False
        self.last_clipped = None
        self.volume_threshold = volume_threshold
        self.time_threshold = time_threshold

    def reset(self):
        self.__init__()

    def add_volume(self, v):
        now = datetime.now()
        if not self.last_clipped:
            if v > self.volume_threshold:
                self.is_talking = True
                self.last_clipped = now
        else:
            t_since_last_clip = (now - self.last_clipped).microseconds
            if v > self.volume_threshold:
                if self.is_talking:
                    self.t_talking += t_since_last_clip
                else:
                    self.t_pause_tmp += t_since_last_clip
                    if self.t_pause_tmp > self.time_threshold:
                        self.t_pause += self.t_pause_tmp
                    else:
                        self.t_talking += self.t_pause_tmp
                    self.t_pause_tmp = 0
                    self.is_talking = True
            else:
                if not self.is_talking:
                    self.t_pause_tmp += t_since_last_clip
                else:
                    self.t_talking += t_since_last_clip
                    self.is_talking = False
            self.last_clipped = now

    @property
    def t_talking_sec(self):
        return self.t_talking / 1000000

    @property
    def t_pause_sec(self):
        return self.t_pause / 1000000

    @property
    def t_all(self):
        return self.t_talking + self.t_pause

    @property
    def t_all_sec(self):
        return self.t_all / 1000000

    def morae_per_sec(self, len_of_morae):
        return len_of_morae / self.t_all * 1000000

    def morae_per_sec_except_pause(self, len_of_morae):
        return len_of_morae / self.t_talking * 1000000

    @property
    def pause_ratio(self):
        return self.t_pause / self.t_all


speech_rate = SpeechRate()


def process_audio(ev):
    buf = ev.inputBuffer.getChannelData(0)
    buf_length = buf.length
    sum_ = 0

    for i in range(buf_length):
        x = buf[i]
        sum_ += pow(x, 2)

    rms = math.sqrt(sum_ / buf_length)

    # volume_ = max(rms, volume * averaging)
    volume = round(rms * 1000)

    if is_running:
        document['volume'].clear()
        document['volume'].text = volume
        line.append(window.Date.new().getTime(), volume)
        speech_rate.add_volume(volume)
        document['talking'].clear()
        document['talking'].text = '{0:.2f}'.format(speech_rate.t_talking_sec)
        document['pause'].clear()
        document['pause'].text = '{0:.2f}'.format(speech_rate.t_pause_sec)


def process_stream(stream):
    global gum_stream
    global audio_ctx
    global mic
    global js_node

    speech_rate.reset()
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

    @bind(document['start_stop'], 'click')
    def start_stop(ev):
        global gum_stream
        global smoothie
        global is_running
        if not gum_stream or not gum_stream.active:
            document['start_stop_text'].text = '測定終了'
            document['duration'].clear()
            document['morae_per_min'].clear()
            document['pause_ratio'].clear()
            document['morae_per_min_except_pause'].clear()
            if not smoothie:
                smoothie = window.SmoothieChart.new({'millisPerPixel': 5, 'grid': {'millisPerLine': 100}})
                smoothie.addTimeSeries(line, {'lineWidth': 1, 'strokeStyle': '#ffffff'})
            smoothie.streamTo(document['graph'])
            is_running = True
            getUserMedia(constraints, process_stream, lambda err: print('error: {}'.format(err.text)))
        else:
            is_running = False
            js_node.disconnect()
            mic.disconnect()
            audio_ctx.close()
            del js_node
            del mic
            del audio_ctx
            gum_stream.getTracks()[0].stop
            del gum_stream
            smoothie.stop()
            document['start_stop_text'].text = '測定開始'
            document['duration'].text = '{0:.2f}'.format(speech_rate.t_all_sec)
            document['morae_per_min'].text = '{0:.2f}'.format(speech_rate.morae_per_sec(len(morae)) * 60)
            document['morae_per_min_except_pause'].text = '{0:.2f}'.format(speech_rate.morae_per_sec_except_pause(len(morae)) * 60)
            document['pause_ratio'].text = '{0:.2%}'.format(speech_rate.pause_ratio)


else:
    print('getUserMedia not supported')

