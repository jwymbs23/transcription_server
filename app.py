
import flask

#import deepspeech
from scipy.io.wavfile import read
import numpy as np
#from pydub import AudioSegment
#from pydub.utils import make_chunks

import os
from flask import render_template, request, redirect, url_for, Flask, Response
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import subprocess


from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import json

app = Flask(__name__)




# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # save the single "profile" file
        profile = request.files['profile']
        filepath = os.path.join(uploads_dir, secure_filename(profile.filename))
        profile.save(filepath)
        if 'm4a' in filepath:
            ps = subprocess.Popen('echo y'.split(), stdout=subprocess.PIPE)
            output = subprocess.check_output(f'ffmpeg -i {filepath} -acodec pcm_s16le -ac 1 -ar 16000 {filepath.split(".")[0]}.wav'.split(), stdin=ps.stdout)
            ps.wait()
            filepath = filepath.split(".")[0]+'.wav'

        return redirect(url_for('processing', filename = filepath))

    return render_template('upload.html')



import time



@app.route('/processing')
def processing():
    
    
    filepath=request.args.get('filename')
    
    

    #a = read(filepath)    
    #
    #chunks = []
    #min_inc = 10000
    #chunk_size = min_inc * 30 #1 sec increments
    #for c in range(len(a[1])//chunk_size):
    #    chunks.append(a[1][c*chunk_size : (c+1)*chunk_size + min_inc * 2])
    #chunks.append(a[1][(c+1)*chunk_size:])
    #
    #ds = deepspeech.Model('deepspeech-0.9.3-models.pbmm')
    #print(ds.sampleRate())

    wf = wave.open(filepath, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print ("Audio file must be WAV format mono PCM.")
        #exit (1)

    model = Model("vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, wf.getframerate())
    
    if request.headers.get('accept') == 'text/event-stream':
        def generate():
            t_data = []
            #text = []
            #for cc, chunk in enumerate(chunks):
            #    text.append(ds.stt(chunk))
            #    current_text = f'{int(np.floor(cc//2))}:{(cc%2)*30:02} - ' + text[-1]
            #    with open(filepath[:-4]+'.txt', 'a') as f:
            #        f.write(current_text + '\n')
            #
            #    
            #    yield "data:" + str(f'{int(np.floor(cc//2))}:{(cc%2)*30:02} - ' + text[-1]) + "\n\n"
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    t_data.append(json.loads(rec.Result().replace('\n', '')))

                    with open(filepath[:-4]+'.txt', 'a') as f:
                        f.write(t_data[-1]['text']+ '\n')
                    try:
                        yield "data:" + (str(t_data[-1]['result'][0]['start']) + 's ' +
                                         str(t_data[-1]['result'][-1]['end']) + 's - ' +
                                         t_data[-1]['text']) + '\n\n'
                    except Exception as e:
                        print(e)
                        yield "data: \n\n"
            yield "data:done\n\n"
        return Response(generate(), mimetype= 'text/event-stream')
    return render_template('index.html')
#formatted_text = '<br>'.join([f'{int(np.floor(ct//2))}:{(ct%2)*30:02}' + ' - ' + t for ct, t in enumerate(text)])
#    return formatted_text#flask.jsonify(text)


@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    #call the run method
    print('going live')
    app.run(debug=True,host='0.0.0.0')
