import re
import sys
from collections import Counter
import pymorphy3
from bs4 import BeautifulSoup


IGNORED_POS   = {'PREP', 'CONJ', 'PRCL', 'INTJ', 'NPRO'}
IGNORED_TAGS  = {'Name', 'Patr', 'Surn', 'Geox'}   # proper nouns / names

# ── helpers ──────────────────────────────────────────────────────────────────

def extract_text(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    if filepath.lower().endswith(('.html', '.htm')) or raw.lstrip().startswith('<'):
        return BeautifulSoup(raw, 'html.parser').get_text(separator=' ')
    return raw


def load_word_set(filepath: str) -> set[str]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        return set()


def append_words(filepath: str, words: list[str]) -> None:
    with open(filepath, 'a', encoding='utf-8') as f:
        for w in words:
            f.write(w + '\n')

# ── core ─────────────────────────────────────────────────────────────────────

def lemmatise(text: str, morph: pymorphy3.MorphAnalyzer) -> Counter:
    counts: Counter = Counter()
    for raw in re.findall(r'[а-яё]+', text.lower()):
        p = morph.parse(raw)[0]
        if p.tag.POS in IGNORED_POS:
            continue
        if IGNORED_TAGS & set(str(p.tag).split(',')):   # any proper-noun tag
            continue
        counts[p.normal_form] += 1
    return counts


def find_new_words(
    text_filepath: str,
    known_filepath: str = 'known',
    interactive: bool = False,
    sort_alpha: bool = False,
) -> None:
    morph = pymorphy3.MorphAnalyzer()

    known = load_word_set(known_filepath)
    if not known:
        print(f"Warning: '{known_filepath}' is empty or missing — treating all words as new.")

    try:
        text = extract_text(text_filepath)
    except FileNotFoundError:
        sys.exit(f"Error: '{text_filepath}' not found.")

    counts   = lemmatise(text, morph)
    unknowns = {w: c for w, c in counts.items() if w not in known}

    if not unknowns:
        print("No new words — you know everything in this text!")
        return

    key       = (lambda x: x[0]) if sort_alpha else (lambda x: -x[1])
    sorted_wc = sorted(unknowns.items(), key=key)

    print(f"Found {len(unknowns)} new word(s) in '{text_filepath}':\n")

    if interactive:
        _interactive_loop(sorted_wc, known_filepath)
    else:
        _print_table(sorted_wc)

# ── display / interactive ─────────────────────────────────────────────────────

def _print_table(items: list[tuple[str, int]]) -> None:
    print(f"{'WORD (LEMMA)':<24} | FREQ")
    print('─' * 33)
    for word, count in items:
        print(f"{word:<24} | {count}")


def _interactive_loop(items: list[tuple[str, int]], known_filepath: str) -> None:
    total   = len(items)
    learned: list[str] = []

    print("  y = I know it  |  n = unknown  |  q = quit\n")
    for i, (word, count) in enumerate(items, 1):
        prompt = f"  [{i}/{total}]  {word:<22} (×{count})  > "
        try:
            choice = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice == 'q':
            break
        if choice == 'y':
            learned.append(word)

    if learned:
        append_words(known_filepath, learned)
        print(f"\n✓ Added {len(learned)} word(s) to '{known_filepath}'.")
    else:
        print("\nNothing added.")

# ── CLI ───────────────────────────────────────────────────────────────────────

USAGE = """\
Usage: python unknown_words.py <text_file> [known_file] [flags]

  known_file   path to known-words list  (default: ./known)

Flags:
  -i           interactive mode — mark words as known on the fly
  -a           sort output alphabetically instead of by frequency
"""

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(USAGE)

    text_file   = sys.argv[1]
    known_file  = 'known'
    interactive = False
    sort_alpha  = False

    for arg in sys.argv[2:]:
        if arg == '-i':
            interactive = True
        elif arg == '-a':
            sort_alpha = True
        else:
            known_file = arg

    find_new_words(text_file, known_file, interactive, sort_alpha)