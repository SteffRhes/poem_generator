import re
import math
from random import randint
from transformers import pipeline


PIPE = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
LIMIT_TEXT_LINES = 10000
DICT_WORD_TO_PHONEMES = {}
TEXT_LIST = []
VERSE_LENGTHS = [(10, 30), (10, 30), (10, 20)]
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
    global TEXT_LIST
    with open(RAW_INPUT_TEXT_FILEPATH) as file:
        line = file.readline()
        i = 0
        global LIMIT_TEXT_LINES
        if LIMIT_TEXT_LINES is None:
            LIMIT_TEXT_LINES = math.inf
        while line and i < LIMIT_TEXT_LINES:
            # TODO: Add sentence splitting here, or sub-sentence phrase detection
            TEXT_LIST.append(line)
            line = file.readline()
            i += 1
            # for word in line.split(" "):
            #     word = re.sub(r"""\n|\(|\)|\"|”|“""", "", word)
            #     word = word.lstrip(".")
            #     if "http" not in word and word != "" and word != "-" and word != "–":
            #         PHRASES_LIST.append(word)
            #
            # line = file.readline()
            # i += 1


def create_random_verse_pair(verse_length, exclusion_set, sent_verse_a, sent_verse_b):
    
    def get_last_word_of_text(text):
        word = ""
        punctuation_found = False
        for i in range(len(text) - 1, -1, -1):
            c = text[i]
            if c in PUNCTUATION_MARKS:
                word_i_end = i
                punctuation_found = True
            elif punctuation_found:
                if c != " ":
                    word = c + word
                else:
                    break
        return word, word_i_end
        

    def build_potential_verse_from_word(verse_length, i, sentiment_target):
        verse = None
        text = TEXT_LIST[i]
        word, word_i_end = get_last_word_of_text(text)
        if word.upper() in DICT_WORD_TO_PHONEMES:
            verse_potential = ""
            end = False
            j = word_i_end
            while not end:
                if j >= 0:
                    c = text[j]
                    verse_potential = c + verse_potential
                    if len(verse_potential) > verse_length[0]:
                        if c in PUNCTUATION_MARKS:
                            end = True
                            verse_potential = verse_potential[1:].strip()
                        if len(verse_potential) > verse_length[1]:
                            end = True
                            verse_potential = None
                            
                    j -= 1
                    
                else:
                    end = True
                
            if verse_potential is not None:
                sent_pred= PIPE(verse_potential)[0]
                if sent_pred["label"] == sentiment_target and sent_pred["score"] > 0.8:
                    verse = verse_potential
                    
        return verse, word

    def find_rhyming_verses_b(verse_length, word_a, sent_verse_b):
        rhyming_verses_b_word_list = []
        phonemes_a_to_match = DICT_WORD_TO_PHONEMES[word_a.upper()]
        for i in range(len(TEXT_LIST)):
            word_b, _ = get_last_word_of_text(TEXT_LIST[i])
            if word_b.upper() != word_a.upper():
                phonemes_b_to_match = DICT_WORD_TO_PHONEMES.get(word_b.upper())
                if phonemes_b_to_match is not None:
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
                        verse_b_potential, _ = build_potential_verse_from_word(verse_length, i, sent_verse_b)
                        if verse_b_potential is not None:
                            rhyming_verses_b_word_list.append((verse_b_potential, word_b))

        return rhyming_verses_b_word_list

    def find_random_verse_a(verse_length, sentiment_target):
        found_random_verse = False
        while not found_random_verse:
            random_index = randint(0, len(TEXT_LIST) - 1)
            verse_a, random_word = build_potential_verse_from_word(verse_length, random_index, sentiment_target)
            if verse_a is not None:
                found_random_verse = True
        # print(f"found verse_a: {verse_a}")
        return verse_a, random_word

    found = False
    verse_a = ""
    word_a = ""
    verse_b = ""
    word_b = ""
    while not found:
        verse_a, word_a = find_random_verse_a(verse_length, sent_verse_a)
        if word_a.upper() not in exclusion_set:
            rhyming_verses_b_word_list = find_rhyming_verses_b(verse_length, word_a, sent_verse_b)
            if rhyming_verses_b_word_list != []:
                difference = math.inf
                for verses_b_word_potential in rhyming_verses_b_word_list:
                    verse_b_potential = verses_b_word_potential[0]
                    word_b_potential = verses_b_word_potential[1]
                    if word_b_potential.upper() not in exclusion_set:
                        difference_potential = abs(len(verse_a) - len(verse_b_potential))
                        if difference_potential < difference:
                            difference = difference_potential
                            verse_b = verse_b_potential
                            word_b = word_b_potential
            
                        if verse_b != "":
                            found = True

    exclusion_set.add(word_a.upper())
    exclusion_set.add(word_b.upper())
    return (verse_a, verse_b, exclusion_set)


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
    exclusion_set = set()
    for vl in VERSE_LENGTHS:
        verse_a, verse_b, exclusion_set = create_random_verse_pair(vl, exclusion_set, "POS", "NEG")
        verses.append((verse_a, verse_b))
    clean_and_print_verses(verses)


if __name__ == "__main__":
    main()

