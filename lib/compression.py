import random

class TextCompressor:
    def __init__(self, compression_rate):
        self.compression_rate = compression_rate

    def compress(self, input_string):
        # Split sentence into words
        words = input_string.split()

        # Calculate the number of words to mask
        num_words_to_mask = int(len(words) * self.compression_rate)

        # Randomly select words to mask
        indices_to_mask = random.sample(range(len(words)), num_words_to_mask)

        # Mask the selected words
        mask = '[*]'
        for index in indices_to_mask:
            words[index] = mask

        # Combine adjacent masks
        compressed_words = []
        i = 0
        while i < len(words):
            if words[i] == mask:
                # Count consecutive masks
                consecutive_masks = 1
                while i + consecutive_masks < len(words) and words[i + consecutive_masks] == mask:
                    consecutive_masks += 1
                compressed_words.append(mask)
                i += consecutive_masks
            else:
                compressed_words.append(words[i])
                i += 1

        # Join the words back into a sentence
        compressed_string = ' '.join(compressed_words)

        return compressed_string

    def set_compression_rate(self, new_rate):
        self.compression_rate = new_rate