import csv
import sys


csv.field_size_limit(sys.maxsize)
PUNCTUATION_MARKS = [".", ",", "!", "?", "…"]


def main():

    # twitter
    texts_twitter = []
    with open("../data/raw/twitter/trump_tweets.csv", "r") as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            text = row[1].replace("\n", "")
            if text[-1] not in PUNCTUATION_MARKS:
                text += "."
            texts_twitter.append(text)
    print(f"number of twitter texts: {len(texts_twitter)}")

    # truth_social
    texts_truth = []
    with open("../data/raw/truth_social/truths.tsv", "r") as f:

        # There were issues with the csv library and tab separated values, where a lot of data was
        # not parsed correctly. So, the rows are iterated over by newlines and searched and parsed
        # manually. This has produced better results.
        search_str = "https://truthsocial.com/@realDonaldTrump/posts"
        for row in f:
            if search_str in row:
                text = row.split(search_str)[0].split("\t")[-3].replace("\n", "")
                if text[-1] not in PUNCTUATION_MARKS:
                    text += "."
                texts_truth.append(text)
    print(f"number of truth social texts: {len(texts_truth)}")

    # write
    texts_all = texts_twitter + texts_truth
    with open("../data/cleaned_text_only.txt", "w") as f:
        texts_all_str = "\n".join(texts_all)
        f.write(texts_all_str)


if __name__ == "__main__":
    main()

