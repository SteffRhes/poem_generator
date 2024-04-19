import re
from random import randint


dict_filepath = "../data/cmu_pronouncing_dictionary.txt"
raw_input_text_filepath  = "../data/cleaned_text_only.txt"
limit_text_lines = 10000
verse_lengths = [3, 5, 3, 6, 2]


def build_word_to_phoneme(dict_filepath):
    dict_word_to_phonemes = {}
    with open(dict_filepath) as file:
        for line in file:
            list_tmp = line.split()
            word = list_tmp[0]
            phonemes = list_tmp[1:]
            dict_word_to_phonemes[word] = phonemes
    return dict_word_to_phonemes


def parse_input_text(raw_input_text_filepath, limit_text_lines):
    list_words = []
    with open(raw_input_text_filepath) as file:
        line = file.readline()
        i = 0
        if limit_text_lines is None:
            limit_text_lines = float("inf")
        while line and i < limit_text_lines:
            for word in line.split(" "):
                word = re.sub(r"""\n|\(|\)|\"|”|“""", "", word)
                word = word.lstrip(".")
                if "http" not in word and word != "" and word != "-" and word != "–":
                    list_words.append(word)

            line = file.readline()
            i += 1

    return list_words


def create_random_verse_pair(dict_word_to_phonemes, list_words, verse_length):

    def search_for_rhymes(word_a, list_words, dict_word_to_phonemes):
        result_indices = []
        word_a = word_a.upper()
        if word_a in dict_word_to_phonemes:
            phonemes_a_to_match = dict_word_to_phonemes[word_a]
            dict_matches = {}
            for i in range(len(list_words)):
                word_b = list_words[i].upper()
                if word_b != word_a and word_b in dict_word_to_phonemes:
                    phonemes_b_to_match = dict_word_to_phonemes[word_b]
                    limit = 0
                    if len(phonemes_a_to_match) < len(phonemes_b_to_match):
                        limit = len(phonemes_a_to_match)
                    else:
                        limit = len(phonemes_b_to_match)
                    count_match = 0
                    for j in range(1, limit + 1):
                        if phonemes_a_to_match[-j] == phonemes_b_to_match[-j]:
                            count_match += 1
                        else:
                            break

                    if count_match >= 4:
                        list_indices = []
                        if count_match in dict_matches:
                            list_indices = dict_matches[count_match]
                        list_indices.append(i)
                        dict_matches[count_match] = list_indices
                        # print(list_all_words[i], phonemes_b_to_match)

            if dict_matches:
                list_match_keys = list(dict_matches.keys())
                max_count_match = max(list_match_keys)
                # print("highest count_match:", max_count_match)
                result_indices = dict_matches[max_count_match]

        return result_indices

    found = False
    verse_a = ""
    verse_b = ""
    while not found:
        random_index = randint(verse_length, len(list_words) - 1)
        random_word = list_words[random_index]
        if random_word[-1] == "." or random_word[-1] == "!" or random_word[-1] == "?" or random_word[-1] == ",":
            random_word = random_word[:-1]
        verse_a = " ".join([ list_words[i] for i in range(random_index-verse_length+1, random_index+1) ])
        if not any( char in verse_a[:-1] for char in [". ", "! ", "? ", ] ) and random_word.upper() in dict_word_to_phonemes:
            result_indices = search_for_rhymes(random_word, list_words, dict_word_to_phonemes)
            if result_indices:
                length_verse_a = len(verse_a)
                difference = length_verse_a
                for result_index in result_indices:
                    verse_b_tmp = " ".join([ list_words[i] for i in range(result_index-verse_length+1, result_index+1) ])
                    if not any( char in verse_b_tmp[:-1] for char in [". ", "! ", "? ", ] ):
                        length_verse_b = len(verse_b_tmp)
                        difference_tmp = abs(length_verse_a - length_verse_b)
                        if difference_tmp < difference:
                            difference = difference_tmp
                            verse_b = verse_b_tmp

                if verse_b != "":
                    found = True

    return (verse_a, verse_b)


def clean_and_print_verses(verses):
    if len(verses) % 2 == 0:
        verses_to_mingle = verses[:-2]
        verses_last = verses[-2:]
    else:
        verses_to_mingle = verses[:-1]
        verses_last = verses[-1:]

    verses_mingled = []
    for i in range(0, len(verses_to_mingle)-1, 2):
        verses_mingled.append(verses_to_mingle[i][0])
        verses_mingled.append(verses_to_mingle[i+1][0])
        verses_mingled.append(verses_to_mingle[i][1])
        verses_mingled.append(verses_to_mingle[i+1][1])

    for vl in verses_last:
        verses_mingled.append(vl[0])
        verses_mingled.append(vl[1])

    verse_start = verses_mingled[0]
    if verse_start[0].isalpha():
        verses_mingled[0] = verse_start[0].upper() + verse_start[1:]
    for i in range(0, len(verses_mingled)):
        verse = verses_mingled[i]
        if i < len(verses_mingled)-1:
            if verse[-1] != "." and verse[-1] != "!" and verse[-1] != "?":
                if verse[-1] != ",":
                    verses_mingled[i] = verse + ","
            else:
                verse_next = verses_mingled[i+1]
                if verse_next[0].isalpha():
                    verses_mingled[i+1] = verse_next[0].upper() + verse_next[1:]

        elif verse[-1] != "." and verse[-1] != "!" and verse[-1] != "?":
            if verse[-1] == ",":
                verses_mingled[i] = verse[:-1] + "."
            else:
                verses_mingled[i] = verse + "."

    for v in verses_mingled:
        print(v)


def main(dict_filepath, raw_input_text_filepath, verse_lengths, limit_text_lines=None):
    dict_word_to_phonemes = build_word_to_phoneme(dict_filepath)
    list_words = parse_input_text(raw_input_text_filepath, limit_text_lines)
    verses = [
        create_random_verse_pair(dict_word_to_phonemes, list_words, vl) 
        for vl in 
        verse_lengths
    ]
    clean_and_print_verses(verses)


if __name__ == "__main__":
    main(dict_filepath, raw_input_text_filepath, verse_lengths, limit_text_lines)

