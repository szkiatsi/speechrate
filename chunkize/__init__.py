from itertools import tee, zip_longest
from typing import Iterable, Iterator, List, Optional, Tuple
from janome.tokenizer import Token


class Chunk(object):
    small_kana = 'ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ' # except っ, that is a separated mora

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens

    def __str__(self) -> str:
        return ''.join(token.surface for token in self.tokens)

    @property
    def morae(self) -> List[str]:
        ret = []

        mora = ''
        a: str
        b: Optional[str]
        for a, b in pairwise(''.join(token.phonetic for token in self.tokens if token.phonetic != '*')):
            mora += a

            """
            バ : 1 mora
            ヴァ: 1 mora
            ヴァァ: 2 morae
            """
            if b and a not in Chunk.small_kana and b in Chunk.small_kana:
                continue
            else:
                ret.append(mora)
                mora = ''

        return ret


def chunkize(tokens: Iterable[Token]) -> List[Chunk]:
    ret = []

    def pos(token: Token, string: str) -> bool:
        return token.part_of_speech.startswith(string)

    a: Token
    b: Token
    chunk_tmp: List[Token] = []
    for a, b in pairwise(tokens):
        # cf.
        # Chunkize rules:
        # https://www.ieice.org/jpn/event/FIT/pdf/d/2014/E-005`.pdf
        # part-of-speech types in the IPA system:
        # http://www.unixuser.org/~euske/doc/postag/#chasen
        # https://taku910.github.io/mecab/posid.html
        chunk_tmp.append(a)

        if not b or \
                pos(a, 'その他,間投') and not pos(b, 'その他,間投') or \
                pos(a, '助詞,') and not (pos(b, '助詞,') or pos(b, '助動詞')) or \
                not pos(a, '名詞,') and pos(b, '名詞,') or \
                not pos(a, '名詞,') and pos(b, '動詞,自立') or \
                pos(a, '副詞,') or \
                pos(a, '連体詞') or \
                pos(b, '連体詞') or \
                pos(a, '接続詞') or \
                pos(b, '形容詞,自立') or \
                pos(a, '助動詞') and not (pos(b, '助詞,') or pos(b, '助動詞')) or \
                pos(a, '感動詞') or \
                pos(a, '記号,') or \
                pos(b, '記号,') or \
                pos(a, 'フィラー') or \
                pos(a, '未知語'):
            ret.append(Chunk(chunk_tmp))
            chunk_tmp = []
        else:
            continue
    return ret


def pairwise(iterable: Iterable) -> Iterator[Tuple]:
    # cf. https://docs.python.org/3/library/itertools.html#itertools-recipes
    # change from original pairwise: last element is paired with None
    # e.g. s -> (s0,s1), (s1,s2), (s2,s3), ..., (sn,None)
    a: Iterator
    b: Iterator
    a, b = tee(iterable)
    next(b, None)
    # return zip(a, b)
    return zip_longest(a, b, fillvalue=None)