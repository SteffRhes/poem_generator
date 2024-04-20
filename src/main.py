import re
import math
import random
from transformers import pipeline


# random.seed(42)
PIPE = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
LIMIT_TEXT_LINES = None
DICT_WORD_TO_PHONEMES = {}
TEXT_LIST = []
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]


VERSE_STRUCTURE = [
    [20, 30, 1, "POS"],
    [20, 30, 1, "POS"],
    [20, 30, 1, "NEG"],
    [40, 50, 2, "NEG"],
    [40, 50, 2, "NEG"],
    [30, 40, 3, "POS"],
    [30, 40, 4, "NEG"],
    [30, 40, 3, "POS"],
    [30, 40, 4, "NEG"],
    [60, 70, 5, "NEG"],
    [60, 70, 5, "NEG"],
    [60, 70, 5, "NEG"],
    [50, 60, 5, "POS"],
    [20, 30, 6, "NEG"],
    [20, 30, 7, "POS"],
    [20, 30, 6, "NEG"],
    [20, 30, 7, "POS"],
]


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


def create_random_verse(verse_length, sentiment_target):
    found_random_verse = False
    while not found_random_verse:
        random_index = random.randint(0, len(TEXT_LIST) - 1)
        verse_a, random_word = build_potential_verse_from_word(verse_length, random_index, sentiment_target)
        if verse_a is not None:
            found_random_verse = True
    return verse_a, random_word
    
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
            sent_pred = PIPE(verse_potential)[0]
            if sent_pred["label"] == sentiment_target and sent_pred["score"] > 0.8:
                verse = verse_potential
    
    return verse, word


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


def create_matching_verse(verse_length, sent_verse_b, exclusion_set, verse_a, word_a):
    
    def create_all_matching_verses(verse_length, word_a, sent_verse_b):
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
    
    verse_b = None
    word_b = None
    rhyming_verses_b_word_list = create_all_matching_verses(verse_length, word_a, sent_verse_b)
    difference = math.inf
    if rhyming_verses_b_word_list != []:
        for verses_b_word_potential in rhyming_verses_b_word_list:
            verse_b_potential = verses_b_word_potential[0]
            word_b_potential = verses_b_word_potential[1]
            if word_b_potential.upper() not in exclusion_set:
                difference_potential = abs(len(verse_a) - len(verse_b_potential))
                if difference_potential < difference:
                    difference = difference_potential
                    verse_b = verse_b_potential
                    word_b = word_b_potential
    
    if word_b is not None:
        exclusion_set.add(word_a.upper())
        exclusion_set.add(word_b.upper())
    return (verse_b, word_b, exclusion_set)

    
def create_group(limit, verse_struct, exclusion_set):
    verse_current = None
    word_current = None
    results = []
    count_current = 0
    exclusion_set_current = exclusion_set.copy()
    while count_current < limit:
        if verse_current is None and word_current is None:
            count_current = 0
            verse_current, word_current = create_random_verse(
                (verse_struct[count_current][0], verse_struct[count_current][1]),
                verse_struct[count_current][3]
            )
            results = [verse_current]
            count_current += 1
            exclusion_set_current = {word_current.upper()}
        else:
            verse_current, word_current, exclusion_set_current = create_matching_verse(
                (verse_struct[count_current][0], verse_struct[count_current][1]),
                verse_struct[count_current][3],
                exclusion_set_current,
                verse_current,
                word_current,
            )
            if verse_current is not None:
                results.append(verse_current)
                count_current += 1
    
    return results, exclusion_set_current.copy()


def main():
    build_word_to_phoneme()
    parse_input_text()
    
    exclusion_set = set()
    groups_count_dict = {}
    for verse_struct in VERSE_STRUCTURE:
        group_count = groups_count_dict.get(verse_struct[2], 0)
        groups_count_dict[verse_struct[2]] = group_count + 1
    
    groups_verses_dict = {}
    for k, v in groups_count_dict.items():
        verse_struct_list = []
        for verse_struct in VERSE_STRUCTURE:
            if verse_struct[2] == k:
                verse_struct_list.append(verse_struct)
        results, exclusion_set = create_group(v, verse_struct_list, exclusion_set)
        groups_verses_dict[k] = results
        
    for verse_struct in VERSE_STRUCTURE:
        verses_list = groups_verses_dict[verse_struct[2]]
        verse = verses_list[0]
        del verses_list[0]
        print(verse)
        

if __name__ == "__main__":
    main()

