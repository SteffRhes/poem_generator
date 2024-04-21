import math
import pickle
import random
import re

from transformers import pipeline


VERSE_STRUCTURE = [
    [20, 30, 1, "NEG"],
    [20, 30, 1, "NEG"],
    # [15, 25, 1, "NEG"],
    # [30, 40, 2, "NEG"],
    # [30, 40, 2, "NEG"],
    # [30, 40, 3, "NEG"],
    # [20, 30, 3, "NEG"],
    # [15, 30, 4, "NEG"],
    # [15, 30, 5, "NEG"],
    # [15, 30, 4, "NEG"],
    # [15, 30, 5, "NEG"],
    # [30, 40, 6, "NEG"],
    # [30, 40, 6, "NEG"],
    # [15, 25, 7, "NEG"],
    # [15, 25, 7, "NEG"],
    # [15, 25, 8, "NEG"],
    # [15, 25, 8, "NEG"],
    # [15, 25, 8, "NEG"],
]
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]
DICT_FILEPATH = "../data/cmu_pronouncing_dictionary.txt"
RAW_INPUT_TEXT_FILEPATH  = "../data/cleaned_text_only.txt"
INDEX_VERSES_FILEPATH = "../data/index/index_1.pickle"
INDEX_VERSES = None
PIPE = None
IS_TESTING = True
IS_CREATING_INDEX = False


def parse_and_index_text():
    
    def create_word_to_phoneme_dict():
        word_to_phoneme_dict = {}
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
                    word_to_phoneme_dict[word] = phonemes
                    
        return word_to_phoneme_dict
    
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
    
    def create_index():
        global INDEX_VERSES
        INDEX_VERSES = {}
        word_to_phoneme_dict = create_word_to_phoneme_dict()
        with open(RAW_INPUT_TEXT_FILEPATH) as f:
            for line in f:
                line_split = re.split(r"(?<=[^\w\s])", line)
                phrase_already_parsed_set = set()
                for phrase in line_split:
                    phrase = phrase.strip()
                    if len(phrase.strip()) >= 5 and phrase[-1] in PUNCTUATION_MARKS + ["-", "'", '"', "“"]:
                        word_phoneme_list = []
                        for word in re.split(r"[^\w]", phrase[:-1])[::-1]:
                            word = word.upper()
                            if word != "":
                                word_phoneme_list.append([word, None])
                        for word_phoneme in word_phoneme_list:
                            phonemes = word_to_phoneme_dict.get(word_phoneme[0])
                            if phonemes is not None:
                                phonemes = phonemes[::-1]
                            word_phoneme[1] = phonemes
                        if (
                            any(wp is not None for wp in word_phoneme_list)
                            and phrase not in phrase_already_parsed_set
                        ):
                            phrase_already_parsed_set.add(phrase)
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
                                "word_phoneme_list": word_phoneme_list,
                            }
                            # verse_dict["phonemes_value"] = create_value_for_phonemes(verse_dict["phonemes"])
                            phrases_dict_list_for_len = INDEX_VERSES.get(len(phrase), [])
                            phrases_dict_list_for_len.append(verse_dict)
                            INDEX_VERSES[len(phrase)] = phrases_dict_list_for_len
                    
                    # elif IS_TESTING:
                    #     print(f"discard: {phrase}")
    
    create_word_to_phoneme_dict()
    create_index()
    
    
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
    
    
def find_matching_verses(verse_length, verse_dict_a, score_count_tmp):
    verse_dict_b_list = []
    for vl in range(verse_length[0], verse_length[1] + 1):
        verse_dict_b_list.extend(INDEX_VERSES[vl])
    verses_scores_list = []
    for verse_dict_b in verse_dict_b_list:
        score_limit = 2.8
        score = 0
        i = 1
        word_phoneme_ab_list = [wp_ab for wp_ab in zip(verse_dict_a["word_phoneme_list"], \
            verse_dict_b["word_phoneme_list"])]
        for wp_a, wp_b in word_phoneme_ab_list[:3]:
            if wp_a[0] != wp_b[0] and abs(len(wp_a[0]) - len(wp_b[0])) < 3 \
                and wp_a[1] is not None and wp_b[1] is not None:
                j = i
                for phoneme_a, phoneme_b in zip(wp_a[1], wp_b[1]):
                    if phoneme_a == phoneme_b:
                        score += j
                    j /= 2
            i /= 2
            
        if score >= score_limit:
            verses_scores_list.append((verse_dict_b, score))
        count = score_count_tmp.get(score, 0)
        score_count_tmp[score] = count + 1
    verses_scores_list = sorted(verses_scores_list, key=lambda x: - x[1])
    if verses_scores_list != []:
        return verses_scores_list
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
    score_count_tmp = {}
    for verses_dict_a in verses_dict_a_list:
        if (
            verses_dict_a["text_sent"][0] == verse_struct[0][3]
            and verses_dict_a["text_sent"][1] > 0.9
        ):
            exclusion_words_set_tmp = exclusion_words_set.copy()
            exclusion_words_set_tmp.add(verses_dict_a['word_phoneme_list'][0][0])
            result = find_matching_verses(verse_length, verses_dict_a, score_count_tmp)
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
    
    score_count_tmp
    l = [[k, v] for k, v in score_count_tmp.items()]
    l = sorted(l, key=lambda x: - x[0])
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
        for verse in verse_list:
            with open("../README.md", "a") as f:
                f.write("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                f.write("```\n")
                for verse in verse_list:
                    f.write(verse + "\n")
                f.write("```\n")
                
    def loop_for_testing():
        verse_length = [10, 20]
        while verse_length[1] <= 50:
            verses_dict_a_list = []
            for vl in range(verse_length[0], verse_length[1]):
                verses_dict_a_list.extend(INDEX_VERSES[vl])
            for verses_dict_a in verses_dict_a_list:
                verses_scores_list = find_matching_verses(verse_length, verses_dict_a, {})
                if verses_scores_list is not None:
                    verses_dict_b, _ = verses_scores_list[0]
                    print(verses_dict_a["text"])
                    print(verses_dict_b["text"])
                    print()
            print(verse_length)
            verse_length = [verse_length[0] + 5, verse_length[1] + 5]
        
    set_up()
    create_or_load_index()
    loop_for_testing()
    # verse_list_all = create_poem()
    # persist_poem(verse_list_all)

if __name__ == "__main__":
    main()
