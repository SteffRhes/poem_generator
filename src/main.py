import re
import math
import random
from transformers import pipeline


PIPE = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
IS_TESTING = True
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
LIMIT_TEXT_LINES = None
DICT_WORD_TO_PHONEMES = {}
INDEX_VERSES = {}
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]
if IS_TESTING:
    random.seed(42)


VERSE_STRUCTURE = [
    [10, 20, 1, "POS"],
    [10, 20, 1, "POS"],
    [15, 25, 1, "POS"],
    [30, 40, 2, "NEG"],
    [30, 40, 2, "NEG"],
    [30, 40, 2, "NEG"],
    [20, 30, 4, "POS"],
    [20, 30, 4, "POS"],
    [40, 50, 5, "POS"],
    [40, 50, 5, "POS"],
    [40, 50, 6, "NEG"],
    [40, 50, 6, "NEG"],
    [40, 50, 7, "NEG"],
    [15, 25, 7, "POS"],
    [15, 25, 8, "NEG"],
    [15, 25, 8, "POS"],
    [15, 25, 7, "NEG"],
    [15, 25, 7, "NEG"],
]



def build_word_to_phoneme():
    global DICT_WORD_TO_PHONEMES
    with open(DICT_FILEPATH) as file:
        for line in file:
            list_tmp = line.split()
            word = list_tmp[0]
            phonemes = list_tmp[1:]
            DICT_WORD_TO_PHONEMES[word] = phonemes


def parse_and_index_text():
    
    def create_value_for_phonemes(phonemes_list):
        phonemes_values_list = []
        n = len(phonemes_list)
        if n > 1:
            step = 1 / (n - 1)
            score_current = 1
            for i in range(n):
                phonemes_values_list.append(score_current)
                score_current -= step
            phonemes_values_list[-1] = 0
        else:
            phonemes_values_list.append(1)
        return phonemes_values_list
    
    global INDEX_VERSES
    with open(RAW_INPUT_TEXT_FILEPATH) as f:
        for line in f:
            line_split = re.split(r"(?<=[^\w\s])", line)
            phrase_already_parsed_set = set()
            for phrase in line_split:
                phrase = phrase.strip()
                if len(phrase.strip()) >= 5 and phrase[-1] in PUNCTUATION_MARKS + ["-", "'", '"', "“"]:
                    word_list_all = re.split(r"[^\w]", phrase[:-1])
                    word_list_phonemes = []
                    phonemes_phrase = []
                    for word in word_list_all:
                        phonemes_word = DICT_WORD_TO_PHONEMES.get(word.upper())
                        if phonemes_word is not None:
                            phonemes_phrase.extend(phonemes_word)
                            word_list_phonemes.append(word.upper())
                    if phonemes_phrase != [] and phrase not in phrase_already_parsed_set:
                        phrase_already_parsed_set.add(phrase)
                        phonemes_phrase_inverted = phonemes_phrase[-1::-1]
                        phrases_dict_list_for_len = INDEX_VERSES.get(len(phrase), [])
                        if IS_TESTING:
                            is_pos = random.randint(0, 1)
                            if is_pos:
                                text_sent = "POS"
                            else:
                                text_sent = "NEG"
                        else:
                            # TODO: real sentiment analysis
                            text_sent = None
                        
                        verse_dict = {
                            "text": phrase,
                            "text_sent": text_sent,
                            "word_list_phonemes": word_list_phonemes[-1::-1],
                            "phonemes": phonemes_phrase_inverted,
                            # "phonemes_value": [],
                        }
                        # verse_dict["phonemes_value"] = create_value_for_phonemes(verse_dict["phonemes"])
                        phrases_dict_list_for_len.append(verse_dict)
                        INDEX_VERSES[len(phrase)] = phrases_dict_list_for_len
                        
                # elif IS_TESTING:
                #     print(f"discard: {phrase}")
                
                
def find_matching_verse(verse_length, verse_dict_a, exclusion_words_set):
    
    def not_contains_identical_words(word_list_a, word_list_b):
        if word_list_a[0] != word_list_b[0]:
            return True
        else:
            return False
    
    verse_dict_b_list = []
    for vl in range(verse_length[0], verse_length[1] + 1):
        verse_dict_b_list.extend(INDEX_VERSES[vl])
    
    scores_verses_list = []
    for verse_dict_b in verse_dict_b_list:
        if (
            verse_dict_b["word_list_phonemes"][0] not in exclusion_words_set
            and not_contains_identical_words(verse_dict_a["word_list_phonemes"], verse_dict_b["word_list_phonemes"])
        ):
            score = 0
            phonemes_list_a = verse_dict_a["phonemes"]
            phonemes_list_b = verse_dict_b["phonemes"]
            len_half_avg = int((len(phonemes_list_a) + len(phonemes_list_b)) / 4)
            for i in range(1, len_half_avg - 1):
                for j in (i - 1, i + 1):
                    for k in (i - 1, i + 1):
                        if (
                            j < len(phonemes_list_a) and k < len(phonemes_list_b)
                            and phonemes_list_a[j] == phonemes_list_b[k]
                        ):
                            score += 1 / i
            if score > 4:
                scores_verses_list.append((verse_dict_b, score))
    
    scores_verses_list = sorted(scores_verses_list, key=lambda x: - x[1])
    if scores_verses_list != []:
        return scores_verses_list[0]
    else:
        return None
    

def create_random_verse(verse_length, sentiment_target):
    found_random_verse = False
    while not found_random_verse:
        random_index = random.randint(0, len(INDEX_VERSES) - 1)
        verse_a, random_word = build_potential_verse_from_word(verse_length, random_index, sentiment_target)
        if verse_a is not None:
            found_random_verse = True
    return verse_a, random_word
    
    
def build_potential_verse_from_word(verse_length, i, sentiment_target):
    verse = None
    text = INDEX_VERSES[i]
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
            if sent_pred["label"] == sentiment_target and sent_pred["score"] > 0.9 and "@" not in verse_potential:
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
        for i in range(len(INDEX_VERSES)):
            word_b, _ = get_last_word_of_text(INDEX_VERSES[i])
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
                    if count_match >= 2:
                        verse_b_potential, _ = build_potential_verse_from_word(verse_length, i, sent_verse_b)
                        if verse_b_potential is not None:
                            rhyming_verses_b_word_list.append((count_match, verse_b_potential, word_b))
        
        rhyming_verses_b_word_list = sorted(rhyming_verses_b_word_list, key=lambda x: - x[0])
        return rhyming_verses_b_word_list
    
    verse_b = None
    word_b = None
    rhyming_verses_b_word_list = create_all_matching_verses(verse_length, word_a, sent_verse_b)
    difference = math.inf
    if rhyming_verses_b_word_list != []:
        count_match_highest = rhyming_verses_b_word_list[0][0]
        for verses_b_word_potential in rhyming_verses_b_word_list:
            count_match = verses_b_word_potential[0]
            verse_b_potential = verses_b_word_potential[1]
            word_b_potential = verses_b_word_potential[2]
            if word_b_potential.upper() not in exclusion_set and count_match == count_match_highest:
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
    parse_and_index_text()
    
    verses_dict_list = INDEX_VERSES[20]
    exclusion_words_set = set()
    while True:
        random_index = random.randint(0, len(verses_dict_list))
        verse_dict_a_random = verses_dict_list[random_index]
        result = find_matching_verse((18,22), verse_dict_a_random, exclusion_words_set)
        if result is not None:
            verse_dict_b_matching, score = result
            print(verse_dict_a_random["text"])
            print(verse_dict_b_matching["text"])
            print("-------")
        
    
    # exclusion_set = set()
    # groups_count_dict = {}
    # for verse_struct in VERSE_STRUCTURE:
    #     group_count = groups_count_dict.get(verse_struct[2], 0)
    #     groups_count_dict[verse_struct[2]] = group_count + 1
    #
    # groups_verses_dict = {}
    # for k, v in groups_count_dict.items():
    #     verse_struct_list = []
    #     for verse_struct in VERSE_STRUCTURE:
    #         if verse_struct[2] == k:
    #             verse_struct_list.append(verse_struct)
    #     results, exclusion_set = create_group(v, verse_struct_list, exclusion_set)
    #     groups_verses_dict[k] = results
    #
    # verse_list_all = []
    # for verse_struct in VERSE_STRUCTURE:
    #     verses_list = groups_verses_dict[verse_struct[2]]
    #     verse = verses_list[0]
    #     del verses_list[0]
    #     verse_list_all.append(verse)
    #     print(verse)
    #
    # with open("../README.md", "a") as f:
    #     f.write("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    #     f.write("```\n")
    #     for verse in verse_list_all:
    #         f.write(verse + "\n")
    #     f.write("```\n")
        

if __name__ == "__main__":
    main()

