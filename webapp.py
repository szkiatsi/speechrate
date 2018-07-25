from typing import Iterable, List
from flask import Flask, jsonify, request, Response
from janome.analyzer import Analyzer
from janome.tokenizer import Token, Tokenizer
from janomeutils import ChunkFilter, token_to_morae


app = Flask(__name__)
tokenizer = Tokenizer(mmap=True)
analyzer = Analyzer(tokenizer=tokenizer, token_filters=[ChunkFilter()])


@app.route('/api/analyze', methods=['POST'])
def analyze() -> Response:
    sentence: str = request.get_data(as_text=True)
    chunks: Iterable[List[Token]] = analyzer.analyze(sentence)
    return jsonify(
        [[{'surface': token.surface, 'morae': list(token_to_morae(token)), 'pos': token.part_of_speech}
          for token in chunk] for chunk in chunks]
    )


@app.route('/', methods=['GET'])
def homepage() -> Response:
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
