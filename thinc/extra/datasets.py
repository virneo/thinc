import random # pragma: no cover
import io # pragma: no cover
from collections import Counter # pragma: no cover
import os.path # pragma: no cover
import csv # pragma: no cover
import numpy
from pathlib import Path
import json

from ._vendorized.keras_data_utils import get_file # pragma: no cover
from ..neural.util import partition
from ..neural.util import to_categorical

try:
    basestring
except NameError:
    basestring = str


GITHUB = 'https://github.com/UniversalDependencies/' # pragma: no cover
ANCORA_1_4_ZIP = '{github}/{ancora}/archive/r1.4.zip'.format(
    github=GITHUB, ancora='UD_Spanish-AnCora') # pragma: no cover
EWTB_1_4_ZIP = '{github}/{ewtb}/archive/r1.4.zip'.format(
    github=GITHUB, ewtb='UD_English') # pragma: no cover

SNLI_URL = 'http://nlp.stanford.edu/projects/snli/snli_1.0.zip'
QUORA_QUESTIONS_URL = 'http://qim.ec.quoracdn.net/quora_duplicate_questions.tsv'


def ancora_pos_tags(encode_words=False): # pragma: no cover
    data_dir = get_file('UD_Spanish-AnCora-r1.4', ANCORA_1_4_ZIP,
                        unzip=True)
    train_loc = os.path.join(data_dir, 'es_ancora-ud-train.conllu')
    dev_loc = os.path.join(data_dir, 'es_ancora-ud-dev.conllu')
    return ud_pos_tags(train_loc, dev_loc, encode_words=encode_words)


def ewtb_pos_tags(encode_tags=False, encode_words=False): # pragma: no cover
    data_dir = get_file('UD_English-r1.4', EWTB_1_4_ZIP, unzip=True)
    train_loc = os.path.join(data_dir, 'en-ud-train.conllu')
    dev_loc = os.path.join(data_dir, 'en-ud-dev.conllu')
    return ud_pos_tags(train_loc, dev_loc,
        encode_tags=encode_tags, encode_words=encode_words)


def ud_pos_tags(train_loc, dev_loc, encode_tags=True, encode_words=True): # pragma: no cover
    train_sents = list(read_conll(train_loc))
    dev_sents = list(read_conll(dev_loc))
    tagmap = {}
    freqs = Counter()
    for words, tags in train_sents:
        for tag in tags:
            tagmap.setdefault(tag, len(tagmap))
        for word in words:
            freqs[word] += 1
    vocab = {word: i for i, (word, freq) in enumerate(freqs.most_common())
             if (freq >= 5)}

    def _encode(sents):
        X = []
        y = []
        for words, tags  in sents:
            if encode_words:
                X.append(
                    numpy.asarray(
                        [vocab.get(word, len(vocab)) for word in words],
                        dtype='uint64'))
            else:
                X.append(words)
            if encode_tags:
                y.append(numpy.asarray(
                    [tagmap[tag] for tag in tags],
                    dtype='int32'))
            else:
                y.append(tags)
        return zip(X, y)

    return _encode(train_sents), _encode(dev_sents), len(tagmap)


def read_conll(loc): # pragma: no cover
    n = 0
    with io.open(loc, encoding='utf8') as file_:
        sent_strs = file_.read().strip().split('\n\n')
    for sent_str in sent_strs:
        lines = [line.split() for line in sent_str.split('\n')
                 if not line.startswith('#')]
        words = []
        tags = []
        for i, pieces in enumerate(lines):
            if len(pieces) == 4:
                word, pos, head, label = pieces
            else:
                idx, word, lemma, pos1, pos, morph, head, label, _, _2 = pieces
            if '-' in idx:
                continue
            words.append(word)
            tags.append(pos)
        yield words, tags


def mnist(): # pragma: no cover
    from ._vendorized.keras_datasets import load_mnist

    # the data, shuffled and split between tran and test sets
    (X_train, y_train), (X_test, y_test) = load_mnist()

    X_train = X_train.reshape(60000, 784)
    X_test = X_test.reshape(10000, 784)
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')

    X_train /= 255.
    X_test /= 255.
    train_data = list(zip(X_train, y_train))
    nr_train = X_train.shape[0]
    random.shuffle(train_data)
    heldout_data = train_data[:int(nr_train * 0.1)]
    train_data = train_data[len(heldout_data):]
    test_data = list(zip(X_test, y_test))
    return train_data, heldout_data, test_data


def reuters(): # pragma: no cover
    from ._vendorized.keras_datasets import load_reuters
    (X_train, y_train), (X_test, y_test) = load_reuters()
    return (X_train, y_train), (X_test, y_test)


def quora_questions(loc=None):
    if loc is None:
        loc = get_file('quora_similarity.tsv', QUORA_QUESTIONS_URL)
    if isinstance(loc, basestring):
        loc = Path(loc)
    is_header = True
    lines = []
    with loc.open('r') as file_:
        for row in csv.reader(file_, delimiter='\t'):
            if is_header:
                is_header = False
                continue
            id_, qid1, qid2, sent1, sent2, is_duplicate = row
            sent1 = sent1.strip()
            sent2 = sent2.strip()
            if sent1 and sent2:
                lines.append(((sent1, sent2), int(is_duplicate)))
    train, dev = partition(lines, 0.9)
    return train, dev


THREE_LABELS = {'entailment': 2, 'contradiction': 1, 'neutral': 0}
TWO_LABELS = {'entailment': 2, 'contradiction': 0, 'neutral': 0}
def snli(loc=None, ternary=False):
    label_scheme = THREE_LABELS if ternary else TWO_LABELS
    if loc is None:
        loc = get_file('snli_1.0', SNLI_URL, unzip=True)
    if isinstance(loc, basestring):
        loc = Path(loc)

    train = read_snli(Path(loc) / 'snli_1.0_train.jsonl', label_scheme)
    dev = read_snli(Path(loc) / 'snli_1.0_dev.jsonl', label_scheme)
    return train, dev


def read_snli(loc, label_scheme):
    rows = []
    with loc.open() as file_:
        for line in file_:
            eg = json.loads(line)
            label = eg['gold_label']
            if label == '-':
                continue
            rows.append(((eg['sentence1'], eg['sentence2']), label_scheme[label]))
    return rows


def get_word_index(path='reuters_word_index.pkl'): # pragma: no cover
    path = get_file(path, origin='https://s3.amazonaws.com/text-datasets/reuters_word_index.pkl')
    f = open(path, 'rb')

    if sys.version_info < (3,):
        data = cPickle.load(f)
    else:
        data = cPickle.load(f, encoding='latin1')

    f.close()
    return data

