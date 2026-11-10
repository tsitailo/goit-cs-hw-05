from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import logging
import re
import matplotlib.pyplot as plt
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

URL = "https://gutenberg.net.au/ebooks01/0100021.txt"


def fetch_text(url: str) -> str:
    """
    Downloads raw text from the specified URL.

    :param url: Web address of the text file.
    :return: Content of the text file as a string.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text

    except requests.RequestException as error:
        logging.error("Failed to download text from URL '%s': %s", url, error)
        raise


def map_mapper(text_chunk: str) -> list[tuple[str, int]]:
    """
    Map phase: Converts a text chunk into a list of (word, 1) tuples.

    :param text_chunk: Substring of full text.
    :return: List of key-value pairs (word, 1).
    """
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text_chunk.lower())
    return [(word, 1) for word in words]


def shuffle_function(
        mapped_results: list[list[tuple[str, int]]]
) -> dict[str, list[int]]:
    """
    Shuffle phase: Groups all mapped values by word.

    :param mapped_results: List of mapped results from threads.
    :return: Dictionary mapping words to lists of counts.
    """
    shuffled = defaultdict(list)
    for result in mapped_results:
        for word_key, count in result:
            shuffled[word_key].append(count)
    return shuffled


def reduce_key_value(key_values: tuple[str, list[int]]) -> tuple[str, int]:
    """
    Reduce phase: Sums up all counts for a single word.

    :param key_values: Tuple of (word, list of counts).
    :return: Tuple of (word, total_count).
    """
    word, counts = key_values
    return word, sum(counts)


def map_reduce(text: str, num_workers: int = 4) -> dict[str, int]:
    """
    Performs MapReduce word count analysis using multithreading.

    :param text: Full raw text.
    :param num_workers: Number of threads for parallel processing.
    :return: Dictionary containing word frequency counts.
    """
    # Split text into chunks for worker threads
    chunk_size = len(text) // num_workers
    chunks = [
        text[i: i + chunk_size] for i in range(0, len(text), chunk_size)
    ]

    # 1. Map phase with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        mapped_results = list(executor.map(map_mapper, chunks))

    # 2. Shuffle phase
    shuffled_values = shuffle_function(mapped_results)

    # 3. Reduce phase with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        reduced_results = list(
            executor.map(reduce_key_value, shuffled_values.items())
        )

    return dict(reduced_results)


def visualize_top_words(word_counts: dict[str, int], top_n: int = 10) -> None:
    """
    Plots a horizontal bar chart displaying the top N most frequent words.

    :param word_counts: Dictionary of word frequencies.
    :param top_n: Number of top words to visualize.
    """
    if not word_counts:
        logging.warning("No word count data to visualize.")
        return

    # Get top_n most frequent words
    sorted_words = sorted(
        word_counts.items(), key=lambda item: item[1], reverse=True
    )[:top_n]

    # Reverse list so highest frequency word is displayed at the top of the chart
    sorted_words.reverse()
    words, frequencies = zip(*sorted_words)

    plt.figure(figsize=(10, 6))
    plt.barh(words, frequencies, color="skyblue", edgecolor="navy")
    plt.xlabel("Frequency", fontsize=12)
    plt.ylabel("Words", fontsize=12)
    plt.title(f"Top {top_n} Most Frequent Words", fontsize=14, fontweight="bold")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()


def main() -> None:
    """
    Main entry point: downloads text, runs MapReduce, and visualizes top words.
    """
    logging.info("Downloading text from URL...")
    try:
        text = fetch_text(URL)
    except Exception:
        return

    logging.info("Analyzing word frequency with MapReduce...")
    word_counts = map_reduce(text, num_workers=4)

    logging.info("Visualizing top 10 words...")
    visualize_top_words(word_counts, top_n=10)


if __name__ == "__main__":
    main()
