from corpus_cleaner.document import Document
from typing import Union, Tuple, Optional, List
from corpus_cleaner.components.cleaner_component_mapper import CleanerComponentMapper
from langid.langid import LanguageIdentifier, model
from ordered_set import OrderedSet
import argparse
import fasttext
import os
import re


class SentenceFilter(CleanerComponentMapper):
    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--char-length-filter-sentence', type=int, default=30,
                            help='filter sentences shorter than a given minimum character length')
        parser.add_argument('--profanity-check', action='store_true',
                            help='filter sentences with sensible content')
        parser.add_argument('--fast-lang-filter-threshold', type=float, help='If --lang-filter is set, minimum'
                                                                             'threshold for the faster lang identifier',
                            default=0.3)
        parser.add_argument('--slow-lang-filter-threshold', type=float, help='If --lang-filter is set, minimum'
                                                                             'threshold for the slower lang identifier',
                            default=0.9)
        parser.add_argument('--code-threshold', type=float, help='Threshold (percentage) of code-like chars and tokens'
                                                                 'to filter a sentence (-1 to deactivate)',
                            default=0.25)
        parser.add_argument('--dictionary-filter-sen', type=str, help='Path to dictionary (plain text, one term per'
                                                                      'line of terms that should not appear in a'
                                                                      'sentence',
                            default=None)
        parser.add_argument('--no-dedup-same-doc-sentences', action='store_true',
                            help='Do not eduplicate sentences in the same document.')

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def __init__(self, args: argparse.Namespace, char_length_filter_sentence: int = 30,
                 lang_filter: Union[Tuple[str], None] = None, slow_lang_filter_threshold: float = 0.90,
                 code_threshold: float = 0.25,
                 profanity_check: bool = False, dictionary_filter: Optional[str] = None,
                 dedup_same_doc_sentences: bool = True):
        # TODO: Review way of setting defaults, thresholds will never be None!
        super().__init__(args)
        self.char_length_filter_sentence = args.char_length_filter_sentence if args.char_length_filter_sentence is not \
                                                                               None else char_length_filter_sentence
        self.profanity_check = args.profanity_check if args.profanity_check is not None else profanity_check
        self.lang_filter = args.lang_filter if args.lang_filter is not None else lang_filter
        self.lang_id = None
        self.fasttext_lid = None
        self.slow_lang_filter_threshold = args.slow_lang_filter_threshold if args.slow_lang_filter_threshold is not \
                                                                             None else slow_lang_filter_threshold
        self.code_threshold = args.code_threshold if args.code_threshold is not None else code_threshold
        self.dictionary_filter = \
            args.dictionary_filter_sen if args.dictionary_filter_sen is not None else dictionary_filter
        if self.dictionary_filter is not None:
            with open(self.dictionary_filter, 'r') as f:
                self.dictionary_filter = [line.strip() for line in f.readlines()]
        self.dictionary_filter_pattern = None
        self.filters = []
        self._get_filters()
        self.code_keywords_pattern = re.compile('\\b(var|function|const|if|else|script)\\b')
        self.code_chars_pattern = re.compile('[;=&\[\](){}/\\\\]')
        self.dedup_same_doc_sentences = \
            not args.no_dedup_same_doc_sentences if args.no_dedup_same_doc_sentences is not None else dedup_same_doc_sentences

    def _filter(self, document: Optional[Document]) -> Optional[Document]:
        sentences_filtered = []
        sentences_deduplicate = document.sentences
        if self.dedup_same_doc_sentences:
            # first, de-duplicate sentences
            sentences_deduplicate = OrderedSet(document.sentences).items
        for sent in sentences_deduplicate:
            # keep only sentences that are not filtered out by all the filters
            if all(_filter(sent) for _filter in self.filters):
                sentences_filtered.append(sent)
        # return the document if contains at least one sentence
        if sentences_filtered:
            document.sentences = sentences_filtered
            return document
        else:
            return None

    def _get_filters(self):
        if self.char_length_filter_sentence is not None:
            self.filters.append(self._filter_by_char_len)
        if self.code_threshold != -1:
            self.filters.append(self._filter_by_code)
        if self.lang_filter is not None:
            self.fasttext_lid = fasttext.load_model(os.path.join('lib', 'lid.176.bin'))
            self.lang_id = LanguageIdentifier.from_modelstring(model, norm_probs=True)
            _ = self.lang_id.classify('')  # force init
            self.filters.append(self._filter_by_lang)
        if self.dictionary_filter is not None:
            self.dictionary_filter_pattern = re.compile("|".join(self.dictionary_filter))
            self.filters.append(self._filter_by_dict)

    def _filter_by_char_len(self, sentence: str) -> bool:
        if len(sentence) > self.char_length_filter_sentence:
            return True
        return False

    def _filter_by_code(self, sentence: str) -> bool:
        if (len(re.findall(self.code_keywords_pattern, sentence)) / len(sentence.split())) \
                + len(re.findall(self.code_chars_pattern, sentence)) / len(sentence) > self.code_threshold:
            return False
        return True

    def _filter_by_lang(self, sentence: str) -> bool:
        res = self.fasttext_lid.predict(sentence.lower())
        lang = res[0][0][-2:]
        conf = res[1][0]
        if lang in self.lang_filter and conf > self.slow_lang_filter_threshold - 0.1:
            return True
        elif lang in self.lang_filter:
            res = self.lang_id.classify(sentence)
            if res[0] in self.lang_filter and res[1] > self.slow_lang_filter_threshold:
                return True
        return False

    def _filter_by_dict(self, sentence: str):
        if self.dictionary_filter_pattern.search(sentence):
            return False
        return True

    def apply(self, document: Optional[Document]) -> Optional[Document]:
        return self._filter(document)

# TODO: UDP. homoglyphs in prefilterer
