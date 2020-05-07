from corpus_cleaner.components.a_data_parser.data_parser import DataParser
from corpus_cleaner.components.i_output_formatter import OutputFormatter
from corpus_cleaner.document import Document
from typing import TextIO, Iterable, Optional, Tuple, List
import subprocess
import argparse
import os
from ..cleaner_component_reducer import CleanerComponentReducer


# Class used to parse the de-duplicated documents from the Onion output file
class OnionParser(DataParser):
    def __init__(self, args: argparse.Namespace, extensions: Tuple[str] = ('.dedup',), **kwargs):
        super(OnionParser, self).__init__(args, encoding='utf-8', input_path=args.output_path,
                                          extensions=extensions, **kwargs)

    def _parse_file(self, fd: TextIO, relative_filepath: str, idx_filepath: int) -> Iterable[Document]:
        doc_sentences = []
        for line in fd.readlines():
            line_index, line = line.split('\t')
            # ignore the first two lines with the start tags
            if line.startswith('<doc>') or line.startswith('<p>') or line.startswith('</p>'):
                continue
            # empty the document sentences list when a new document is reached and return the document object
            elif line.startswith('</doc>'):
                # TODO: add the raw content for each document with the Onion tags
                yield Document(content='', sentences=doc_sentences)
                doc_sentences = []
            else:
                if line_index == '0':
                    doc_sentences.append(line.strip())


# Class used to write the documents in the Onion input file
class OnionOutputFormatter(OutputFormatter):
    def __init__(self, args: argparse.Namespace, filepath: str):
        super().__init__(args)
        self.file = filepath
        self.start_doc_tag = '<doc>\n<p>\n'
        self.end_doc_tag = '\n</p>\n</doc>\n'

    def _init_writing(self):
        self.fd = open(self.file, 'w+')

    def _write_document(self, document: Document):
        doc_onion = self.start_doc_tag + '\n'.join(document.sentences) + self.end_doc_tag
        self.fd.writelines(doc_onion)

    def _end_writing(self):
        self.fd.close()


class DocumentFilter(CleanerComponentReducer):
    def __init__(self, args: argparse.Namespace, document_deduplication_threshold: float = 0.75):
        onion_input_file = os.path.join(args.output_path, 'input.onion')
        super().__init__(args, OnionOutputFormatter(args, onion_input_file), OnionParser(args))
        self.document_deduplication_threshold = args.document_deduplication_threshold \
            if args.document_deduplication_threshold is not None else document_deduplication_threshold
        self.onion_input_file = onion_input_file
        self.onion_output_file = os.path.join(args.output_path, 'output_deduplicate.onion.dedup')
        self.onion_path = os.path.join('lib', 'onion-1.2', 'bin', 'onion')

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        parser.add_argument('--document_deduplication_threshold', type=float,
                            help='Threshold for document de-duplication, roughly related to the percentage of sentences'
                                 'overlap between the documents.',
                            default=0.75)

    @staticmethod
    def check_args(args: argparse.Namespace):
        # TODO check custom args
        pass

    def _run_onion(self):
        onion_command = f'{self.onion_path} -m -n 1 -t {self.document_deduplication_threshold} {self.onion_input_file} > {self.onion_output_file}'
        subprocess.run(onion_command, shell=True, check=True, universal_newlines=True)

    def _reduce(self):
        self._run_onion()
