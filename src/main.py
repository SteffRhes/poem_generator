import math
import pickle
import random
import re

from transformers import pipeline


VERSE_STRUCTURE = [
    [10, 20, 1, "NEG"],
    [10, 20, 1, "NEG"],
    [15, 25, 1, "NEG"],
    [30, 40, 2, "NEG"],
    [30, 40, 2, "NEG"],
    [30, 40, 3, "NEG"],
    [20, 30, 3, "NEG"],
    [15, 30, 4, "NEG"],
    [15, 30, 5, "NEG"],
    [15, 30, 4, "NEG"],
    [15, 30, 5, "NEG"],
    [30, 40, 6, "NEG"],
    [30, 40, 6, "NEG"],
    [15, 25, 7, "NEG"],
    [15, 25, 7, "NEG"],
    [15, 25, 8, "NEG"],
    [15, 25, 8, "NEG"],
    [15, 25, 8, "NEG"],
]
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
INDEX_VERSES_FILEPATH = "../data/index/index_1.pickle"
DICT_WORD_TO_PHONEMES = None
INDEX_VERSES = None
PIPE = None
IS_TESTING = True
IS_CREATING_INDEX = True


def parse_and_index_text():
    
    def build_word_to_phoneme_dict():
        global DICT_WORD_TO_PHONEMES
        DICT_WORD_TO_PHONEMES = {}
        with open(DICT_FILEPATH) as file:
            for i, line in enumerate(file):
                if i >= 54:
                    line_split = line.split()
                    word = line_split[0]
                    phonemes = []
                    for c in line_split[1:]:
                        if c[-1] in ["0", "1", "2"]:
                            c = c[:-1]
                        phonemes.append(c)
                    DICT_WORD_TO_PHONEMES[word] = phonemes
    
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
    
    def build_index():
        global INDEX_VERSES
        INDEX_VERSES = {}
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
                                if random.randint(0, 1):
                                    text_sent = ("POS", 0.99)
                                else:
                                    text_sent = ("NEG", 0.99)
                            else:
                                text_sent = PIPE(phrase)[0]
                                text_sent = (text_sent["label"], text_sent["score"])
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
    
    build_word_to_phoneme_dict()
    build_index()
    
    
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
    
    
def find_matching_verses(verse_length, verse_dict_a):
    
    def not_contains_identical_words(word_list_a, word_list_b):
        limit = 3
        for i in range(limit):
            for j in range(limit):
                if i < len(word_list_a) and j < len(word_list_b) and word_list_a[i] == word_list_b[j]:
                    return False
        return True
    
    verse_dict_b_list = []
    for vl in range(verse_length[0], verse_length[1] + 1):
        verse_dict_b_list.extend(INDEX_VERSES[vl])
    
    scores_verses_list = []
    for verse_dict_b in verse_dict_b_list:
        score_limit = 5
        if not_contains_identical_words(verse_dict_a["word_list_phonemes"], verse_dict_b["word_list_phonemes"]):
            score = 0
            phonemes_list_a = verse_dict_a["phonemes"]
            phonemes_list_b = verse_dict_b["phonemes"]
            for i in range(score_limit):
                if i < len(phonemes_list_a) and i < len(phonemes_list_b):
                    phoneme_a = phonemes_list_a[i]
                    phoneme_b = phonemes_list_b[i]
                    if phoneme_a == phoneme_b:
                        score += 1
            
            if score >= score_limit:
                scores_verses_list.append((verse_dict_b, score))
            
    scores_verses_list = sorted(scores_verses_list, key=lambda x: - x[1])
    if scores_verses_list != []:
        return scores_verses_list
    else:
        return None
    

def create_group(limit, verse_struct, exclusion_words_set):
    # TODO verse_length should not be hardcoded to the first target
    verse_length = (verse_struct[0][0], verse_struct[0][1])
    verses_dict_a_list = []
    for vl in range(verse_length[0], verse_length[1]):
        verses_dict_a_list.extend(INDEX_VERSES[vl])
    random.shuffle(verses_dict_a_list)
        
    verses_dict_b_list = []
    for verses_dict_a in verses_dict_a_list:
        if (
            verses_dict_a["text_sent"][0] == verse_struct[0][3]
            and verses_dict_a["text_sent"][1] > 0.9
        ):
            exclusion_words_set_tmp = exclusion_words_set.copy()
            exclusion_words_set_tmp.add(verses_dict_a["word_list_phonemes"][0])
            result = find_matching_verses(verse_length, verses_dict_a)
            if result is not None and len(result) >= limit - 1:
                num_found = 1
                for i in range(limit - 1):
                    for verses_dict_b, _ in result:
                        if (
                            verses_dict_b["text_sent"][0] == verse_struct[i + 1][3]
                            and verses_dict_b["text_sent"][1] > 0.9
                            and verses_dict_b["word_list_phonemes"][0] not in exclusion_words_set_tmp
                        ):
                            exclusion_words_set_tmp.add(verses_dict_b["word_list_phonemes"][0])
                            verses_dict_b_list.append(verses_dict_b)
                            num_found += 1
                            break
                        
                if num_found == limit:
                    exclusion_words_set = exclusion_words_set_tmp
                    break
    
    return ([verses_dict_a] + verses_dict_b_list, exclusion_words_set)
    

def main():
    
    def set_up():
        if IS_TESTING:
            random.seed(42)
        else:
            global PIPE
            PIPE = pipeline("text-classification", model="finiteautomata/bertweet-base-sentiment-analysis")
        
    def create_or_load_index():
        global INDEX_VERSES
        if IS_CREATING_INDEX:
            parse_and_index_text()
            with open(INDEX_VERSES_FILEPATH, "wb") as f:
                pickle.dump(INDEX_VERSES, f)
        
        else:
            with open(INDEX_VERSES_FILEPATH, "rb") as f:
                INDEX_VERSES = pickle.load(f)
        
    def create_poem():
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
            results = [r["text"] for r in results]
            if IS_TESTING:
                for r in results:
                    print(r)
            groups_verses_dict[k] = results

        verse_list_all = []
        if not IS_TESTING:
            for verse_struct in VERSE_STRUCTURE:
                verses_list = groups_verses_dict[verse_struct[2]]
                verse = verses_list[0]
                del verses_list[0]
                verse_list_all.append(verse)
        
        for verse in verse_list_all:
            print(verse)
        return verse_list_all
    
    def persist_poem(verse_list):
        for verse in verse_list_all:
            with open("../README.md", "a") as f:
                f.write("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                f.write("```\n")
                for verse in verse_list_all:
                    f.write(verse + "\n")
                f.write("```\n")
        
    set_up()
    create_or_load_index()
    verse_list_all = create_poem()
    persist_poem(verse_list_all)

if __name__ == "__main__":
    main()

