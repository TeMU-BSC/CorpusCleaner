from typing import Union, Tuple, List
from typing import Iterable
from corpus_cleaner.document import Document
from alphabet_detector import AlphabetDetector
from langid.langid import LanguageIdentifier, model
from corpus_cleaner.components.cleaner_component import CleanerComponent
import unicodedata
import re
import argparse


# TODO: Check whether in pre-filtering or later on:  from profanity_check import predict, predict_prob


class PreFilterer(CleanerComponent):
    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--no-remove-tags', action='store_true', help='Avoid removing XML/HTML tags')
        parser.add_argument('--char-length-filter', type=int, help='Minimum char length per document. Set to 0 not'
                                                                   'to apply any filter.', default=40)
        parser.add_argument('--no-head-filter', action='store_true', help='Avoid filtering documents coming from'
                                                                          'a crawler (having a "heads" attribute) with common HTTP errors.')
        parser.add_argument('--digits_filter', type=float, help='Maximum allowed proportion of digit characters',
                            default=0.1)
        parser.add_argument('--alphanum_filter', type=float, help='Maximum allowed proportion of non-alphanumeric'
                                                                  'characters', default=0.1)
        parser.add_argument('--uppercase_filter', type=float, help='Maximum allowed proportion of uppercase characters',
                            default=0.4)
        parser.add_argument('--alphabet-filter', type=str, help='Alphabets that should be present (eg. LATIN)',
                            nargs='+', default=['LATIN'])
        parser.add_argument('--lang-filter', type=str, help='List of languages that should allowed when filtering by'
                                                            'lang. If not set, no filtering is applied.',
                            nargs='+')
        parser.add_argument('--lang-filter-threshold', type=float, help='If --lang-filter is set, minimum threshold',
                            default=0.90)
        parser.add_argument('--dictionary-filter', type=str, help='Path to dictionary (plain text, one term per line'
                                                                  'of terms that should not appear', default=None)

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def __init__(self, args: argparse.Namespace,
                 no_remove_tags: bool = True,
                 char_length_filter: int = 40, no_head_filter: bool = False, digits_filter: float = 0.1,
                 alphanum_filter: float = 0.1, uppercase_filter: float = 0.4,
                 alphabet_filter: Union[Tuple[str], None] = ('LATIN',), lang_filter: Union[Tuple[str], None] = None,
                 lang_filter_threshold: float = 0.90,
                 dictionary_filter: Union[None, List[str]] = None):
        super().__init__(args)
        self.remove_tags = not args.no_remove_tags if args.no_remove_tags is not None else not no_remove_tags
        self.tags_pattern = None
        self.char_length_filter = args.char_length_filter if args.char_length_filter is not None else char_length_filter
        self.head_filter = not args.no_head_filter if args.no_head_filter is not None else not no_head_filter
        self.digits_filter = args.digits_filter if args.digits_filter is not None else digits_filter
        self.alphanum_filter = args.alphanum_filter if args.alphanum_filter is not None else alphanum_filter
        self.uppercase_filter = args.uppercase_filter if args.uppercase_filter is not None else uppercase_filter
        self.alphabet_filter = args.alphabet_filter if args.alphabet_filter is not None else alphabet_filter
        self.lang_filter = args.lang_filter if args.lang_filter is not None else lang_filter
        self.lang_id = None
        self.lang_filter_threshold = args.lang_filter_threshold if args.lang_filter_threshold is not None else \
            lang_filter_threshold
        self.dictionary_filter = args.dictionary_filter if args.dictionary_filter is not None else dictionary_filter
        self.dictionary_filter_pattern = None
        self.filters = []
        self._build_filters()

    def _remove_tags(self, text):
        """This function substitute HTML tags with a period "." assuming each tag marks the end of the sentence."""
        return re.sub(self.tags_pattern, '. ', text)

    # def _remove_newlines_and_tabs(self):
    #     pass

    def _build_filters(self):
        if self.remove_tags:
            self.tags_pattern = re.compile('[. ]*(<.*?> ?)+ *')
        if self.char_length_filter > 0:
            self.filters.append(self._filter_by_length)
        if self.head_filter:
            self.filters.append(self._filter_by_heads)
        if self.digits_filter > 0:
            self.filters.append(self._filter_by_digits)
        if self.alphanum_filter > 0:
            self.filters.append(self._filter_by_alphanum)
        if self.uppercase_filter > 0:
            self.filters.append(self._filter_by_alphanum)
        if self.alphabet_filter is not None:
            self.ad = AlphabetDetector()
            self.filters.append(self._filter_by_alphabet)
        if self.lang_filter is not None:
            self.lang_id = LanguageIdentifier.from_modelstring(model, norm_probs=True)
            self.filters.append(self._filter_by_lang)
        if self.dictionary_filter is not None:
            self.dictionary_filter_pattern = re.compile("|".join(self.dictionary_filter))
            self.filters.append(self._filter_by_dict)

    def _filter_by_length(self, doc: Document):
        if len(doc.content) < self.char_length_filter:
            return False
        return True

    @staticmethod
    def _filter_by_heads(doc: Document):
        if doc.heads is not None:
            for token in ['found', '404', 'robots.txt', 'error']:
                if re.search(token, doc.heads, re.IGNORECASE):
                    return False
        return True

    def _filter_by_digits(self, doc: Document):
        if sum(c.isdigit() for c in doc.content) / len(doc.content) > self.digits_filter:
            return False
        return True

    def _filter_by_alphanum(self, doc: Document):
        concat_content = ''.join(doc.content.split())
        if (1 - (sum(c.isalnum() for c in concat_content) / len(concat_content))) > self.alphanum_filter:
            return False
        return True

    def _filter_by_uppercase(self, doc: Document):
        if sum(c.isupper() for c in doc.content) / len(doc.content) > self.uppercase_filter:
            return False
        return True

    def _filter_by_alphabet(self, doc: Document):
        # TODO: Check thresholds?
        if len(self.ad.detect_alphabet(doc.content).intersection(set(self.alphabet_filter))) == 0:
            return False
        return True

    def _filter_by_lang(self, doc: Document):
        res = self.lang_id.classify(doc.content)
        if res[0] in self.lang_filter and res[1] > self.lang_filter_threshold:
            doc.language = res[0]
            return True
        return False

    def _filter_by_dict(self, doc: Document):
        if self.dictionary_filter_pattern.search(doc.content):
            return False
        return True

    def _filter(self, documents: Iterable[Document]):
        i = 0
        for doc in documents:
            i += 1
            if self.remove_tags:
                doc.content = self._remove_tags(doc.content)
            keep = True
            for filter_ in self.filters:
                keep = filter_(doc)
                if not keep:
                    break
            if keep:
                yield doc

    def apply(self, documents: Union[Iterable[Document], None]) -> Union[Iterable[Document], None]:
        return self._filter(documents)