from .output_formatter import OutputFormatter, OutputFormatterConfig
from corpus_cleaner.document import Document
import os
from corpus_cleaner.constants import TXT_OUTPUT_PATH


class SentenceOutputFormatter(OutputFormatter):

    def __init__(self, config: OutputFormatterConfig):
        super().__init__(config)

    def _init_writing(self):
        self.fd = open(os.path.join(self.path, TXT_OUTPUT_PATH), 'a')

    def _write_document(self, document: Document):
        if len(document.sentences) > 0:
            # sentences = [sentence.replace(f'{self.separator}', '\t') for sentence in document.sentences]
            self.fd.writelines(f'{sentence}\n' for sentence in document.sentences)

    def _end_writing(self):
        self.fd.close()

