from itertools import tee, zip_longest
import math
from typing import Dict, Iterable, Iterator, List, Optional, Tuple
import jaconv
import jaconv.conv_table
from janome.tokenfilter import TokenFilter
from janome.tokenizer import Token


def token_to_morae(token: Token) -> Iterator[str]:
    small_kana: str = 'ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ'  # except っ, that is a separated mora
    number_yomi_1: Dict[int, str] = \
            {0: 'ゼロ', 1: 'イチ', 2: 'ニ', 3: 'サン', 4: 'ヨン', 5: 'ゴ', 6: 'ロク', 7: 'ナナ', 8: 'ハチ', 9: 'キュー'}
    number_yomi_4: List[Tuple[int, str]] = [(1000, 'セン'), (100, 'ヒャク'), (10, 'ジュー'), (1, '')]
    number_yomi_5: List[Tuple[int, str]] = [(1_0000_0000_0000, 'チョー'), (1_0000_0000, 'オク'), (1_0000, 'マン'), (1, '')]
    morae: str = ''
    phonetic: str = ''
    a: str
    b: Optional[str]

    if token.part_of_speech == '名詞,数,*,*' and token.phonetic == '*':
        try:
            num: int = int(token.surface)
            if num == 0:
                phonetic = number_yomi_1[0]
            elif num < 1_0000_0000_0000_0000:
                num_tmp: int = num
                for num_5, yomi_5 in number_yomi_5:
                    num_9999 = math.floor(num_tmp / num_5)
                    if num_9999:
                        num_9999_tmp: int = num_9999
                        for num_4, yomi_4 in number_yomi_4:
                            num_1 = int(math.floor(num_9999_tmp / num_4))
                            if num_1:
                                if num_1 != 1 or num_4 == 1:
                                    phonetic += number_yomi_1[num_1]
                                phonetic += yomi_4
                                num_9999_tmp -= num_1 * num_4
                        phonetic += yomi_5
                        num_tmp -= num_9999 * num_5
            else:
                phonetic = token.phonetic
        except ValueError:
            phonetic = token.phonetic
    elif token.phonetic == '*':
        if all(ord(c) in jaconv.conv_table.K2H_TABLE.keys() for c in token.surface):
            phonetic = token.surface
        elif all(ord(c) in jaconv.conv_table.H2K_TABLE.keys() for c in token.surface):
            phonetic = jaconv.hira2kata(token.surface)
        else:
            phonetic = token.surface
    else:
        phonetic = token.phonetic

    for a, b in pairwise(phonetic):
        morae += a

        """
        バ : 1 mora
        ヴァ: 1 mora
        ヴァァ: 2 morae
        """
        if b and a not in small_kana and b in small_kana:
            continue
        else:
            yield morae
            morae = ''


class ChunkFilter(TokenFilter):
    def apply(self, tokens: Iterable[Token]) -> Iterator[List[Token]]:
        def pos(token: Token, string: str) -> bool:
            return token.part_of_speech.startswith(string)

        a: Token
        b: Token
        chunk: List[Token] = []
        token_pairs: Iterator[Tuple[Token, Optional[Token]]] = pairwise(tokens)
        for a, b in token_pairs:
            # cf.
            # Chunkize rules:
            # https://www.ieice.org/jpn/event/FIT/pdf/d/2014/E-005.pdf
            # part-of-speech types in the IPA system:
            # http://www.unixuser.org/~euske/doc/postag/#chasen
            # https://taku910.github.io/mecab/posid.html
            chunk.append(a)

            # TODO: revise rules for IPA types
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
                yield chunk
                chunk.clear()
            else:
                continue


def pairwise(iterable: Iterable) -> Iterator[Tuple]:
    # cf. https://docs.python.org/3/library/itertools.html#itertools-recipes
    # change from original pairwise: last element is paired with None
    # e.g. (s0,s1,...,sn) -> (s0,s1), (s1,s2), (s2,s3), ..., (sn,None)
    a: Iterator
    b: Iterator
    a, b = tee(iterable)
    next(b, None)
    # return zip(a, b)
    return zip_longest(a, b, fillvalue=None)
