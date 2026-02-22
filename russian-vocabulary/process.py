import re
import sys
from collections import Counter
import pymorphy3

def count_words(filepath, top_n=20):
    morph = pymorphy3.MorphAnalyzer()
    word_counter = Counter()
    ignored_pos = {'PREP', 'CONJ', 'PRCL'}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read().lower()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return

    words = re.findall(r'[а-яё]+', text)

    for word in words:
        parsed_word = morph.parse(word)[0]
        
        if parsed_word.tag.POS in ignored_pos:
            continue
            
        lemma = parsed_word.normal_form
        word_counter[lemma] += 1

    # Save all unique lemmas (base/normal forms) to current_thin
    output_file = 'current_thin'
    with open(output_file, 'w', encoding='utf-8') as f:
        for lemma in sorted(word_counter.keys()):
            f.write(lemma + '\n')
    print(f"Saved {len(word_counter)} unique lemmas → '{output_file}'")

    # Print the results
    print(f"\n{'WORD (LEMMA)':<20} | {'FREQUENCY'}")
    print("-" * 35)
    for word, count in word_counter.most_common(top_n):
        print(f"{word:<20} | {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_ru.py <filename>")
    else:
        file_to_read = sys.argv[1]
        count_words(file_to_read)