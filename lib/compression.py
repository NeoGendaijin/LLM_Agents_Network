import random

class TextCompressor:
    def __init__(self, compression_rate):
        self.compression_rate = compression_rate

    def compress(self, input_string):
        # Split sentence into words
        words = input_string.split()

        # calculate the number of words to mask
        num_words_to_mask = int(len(words) * self.compression_rate)

        # randomly select words to mask
        indices_to_mask = random.sample(range(len(words)), num_words_to_mask)

        # mask the selected words
        for index in indices_to_mask:
            words[index] = '[mask]'

        # join the words back into a sentence
        compressed_string = ' '.join(words)

        return compressed_string

    def set_compression_rate(self, new_rate):
        self.compression_rate = new_rate
