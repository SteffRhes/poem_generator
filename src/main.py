import re
import math
from random import randint
from transformers import pipeline


PIPE = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
LIMIT_TEXT_LINES = 10000
DICT_WORD_TO_PHONEMES = {}
LIST_WORDS = []
VERSE_LENGTHS = [(30, 50), (20, 50), (10, 20)]
SENTIMENT = ["POS"]
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]


def build_word_to_phoneme():
    global DICT_WORD_TO_PHONEMES
    with open(DICT_FILEPATH) as file:
        for line in file:
            list_tmp = line.split()
            word = list_tmp[0]
            phonemes = list_tmp[1:]
            DICT_WORD_TO_PHONEMES[word] = phonemes


def parse_input_text():
    global LIST_WORDS
    with open(RAW_INPUT_TEXT_FILEPATH) as file:
        line = file.readline()
        i = 0
        global LIMIT_TEXT_LINES
        if LIMIT_TEXT_LINES is None:
            LIMIT_TEXT_LINES = float("inf")
        while line and i < LIMIT_TEXT_LINES:
            for word in line.split(" "):
                word = re.sub(r"""\n|\(|\)|\"|”|“""", "", word)
                word = word.lstrip(".")
                if "http" not in word and word != "" and word != "-" and word != "–":
                    LIST_WORDS.append(word)

            line = file.readline()
            i += 1


def create_random_verse_pair(verse_length, sent_verse_a, sent_verse_b):

    def build_potential_verse_from_word(verse_length, i, sentiment_target):
        verse = None
        word = LIST_WORDS[i]
        if word.upper() in DICT_WORD_TO_PHONEMES and word[-1] in PUNCTUATION_MARKS:
            verse_potential = word
            end = False
            j = i
            while not end:
                j -= 1
                new_word = LIST_WORDS[j]
                verse_potential_safe = verse_potential
                verse_potential = new_word + " " + verse_potential
                if new_word[-1] in PUNCTUATION_MARKS or len(verse_potential) > verse_length[1]:
                    end = True
                    verse_potential = verse_potential_safe
                    
            if verse_length[0] <= len(verse_potential) <= verse_length[1]:
                sent_pred= PIPE(verse_potential)[0]
                if sent_pred["label"] == sentiment_target and sent_pred["score"] > 0.8:
                    verse = verse_potential
                    
        return verse

    def find_rhyming_verses_b(word_a):
        result_indices = []
        word_a = word_a.upper()
        phonemes_a_to_match = DICT_WORD_TO_PHONEMES[word_a]
        # dict_matches = {}
        for i, word_b in enumerate(LIST_WORDS):
            word_b = word_b.upper()
            if word_b != word_a and word_b in DICT_WORD_TO_PHONEMES:
                phonemes_b_to_match = DICT_WORD_TO_PHONEMES[word_b]
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
                if count_match >= 3 and count_match <= 5:
                    result_indices.append(i)
        #             list_indices = []
        #             if count_match in dict_matches:
        #                 list_indices = dict_matches[count_match]
        #             list_indices.append(i)
        #             dict_matches[count_match] = list_indices
        #
        # if dict_matches:
        #     list_match_keys = list(dict_matches.keys())
        #     max_count_match = max(list_match_keys)
        #     # print("highest count_match:", max_count_match)
        #     result_indices = dict_matches[max_count_match]

        return result_indices

    def find_random_verse_a(verse_length, sentiment_target):
        found_random_verse = False
        while not found_random_verse:
            random_index = randint(0, len(LIST_WORDS) - 1)
            random_word = LIST_WORDS[random_index]
            print(random_word)
            verse_a = build_potential_verse_from_word(verse_length, random_index, sentiment_target)
            if verse_a is not None:
                found_random_verse = True
        print(f"found verse_a: {verse_a}")
        return verse_a, random_word

    found = False
    verse_a = ""
    verse_b = ""
    while not found:
        verse_a, random_word = find_random_verse_a(verse_length, sent_verse_a)
        result_indices = find_rhyming_verses_b(random_word)
        if result_indices != []:
            verse_b_potential_list = []
            for result_index in result_indices:
                verse_b_potential = build_potential_verse_from_word(verse_length, result_index, "NEG")
                if verse_b_potential is not None:
                    verse_b_potential_list.append(verse_b_potential)
                
            if verse_b_potential_list != []:
                difference = math.inf
                for verse_b_potential in verse_b_potential_list:
                    difference_potential = abs(len(verse_a) - len(verse_b_potential))
                    if difference_potential < difference:
                        difference = difference_potential
                        verse_b = verse_b_potential
            # length_verse_a = len(verse_a)
            # difference = length_verse_a
            # for result_index in result_indices:
            #     # TODO verse_length
            #     verse_b_tmp = " ".join([LIST_WORDS[i] for i in range(result_index - verse_length + 1, result_index + 1)])
            #     sent_verse_b_real = PIPE(verse_b_tmp)[0]["label"]
            #     if (
            #         not any( char in verse_b_tmp[:-1] for char in [". ", "! ", "? ", ] )
            #         and sent_verse_b_real == sent_verse_b
            #     ):
            #         length_verse_b = len(verse_b_tmp)
            #         difference_potential = abs(length_verse_a - length_verse_b)
            #         if difference_potential < difference:
            #             difference = difference_potential
            #             verse_b = verse_b_tmp

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


def main():
    build_word_to_phoneme()
    parse_input_text()
    verses = []
    for vl in VERSE_LENGTHS:
        verses.append(create_random_verse_pair(vl, "POS", "NEG"))
    clean_and_print_verses(verses)


if __name__ == "__main__":
    main()

