# Anagram Finder

A small python command-line tool for generating anagrams from an input phrase.

Uses some convenient characteristics of prime numbers for testing.

## Installation

First, be sure you have [python3](https://www.python.org/downloads/) installed.

Next, install the one 3rd-party package used (for tree-printing):

```
pip install pptree
```

Finally, construct the dictionary that is used by the program for checking whether words are acceptable:

```
python3 anagram.py build
```

## Usage

The tool includes two different algorithms for detecting anagrams.

### Recursive Algorithm

Works recursively by "factoring" the word by its "sub-words".

```
python3 anagram.py recursive [any number of words]
```

By default, this prints the output as a tree that may include duplicates due to difference in word order (TODO: remove duplicates):

```
        ┌['thin', 'hint']┐
        │                └[['all']]
        ├['hill']┐
        │        └[['tan', 'ant']]
        ├['than']┐
        │        └[['ill']]
        ├['halt']┐
        │        └[['nil', 'lin']]
        ├['tin']┐
        │       └[['hall']]
 anthill┤
        ├['all']┐
        │       └[['thin', 'hint']]
        ├['tan', 'ant']┐
        │              └[['hill']]
        ├['ill']┐
        │       └[['than']]
        ├['nil', 'lin']┐
        │              └[['halt']]
        └['hall']┐
                 └[['tin']]
```                 

Nodes are a list of all anagrams at that level, and a full anagramatic phrase can be created by tracing from the root to a leaf. The tree will only be output once the full tree has been discovered.

#### (Optional) JSON Output

If you'd like your output to be JSON-formatted, pass the `--json` flag:

```
python3 anagram.py recursive --json [any number of words]
```

You may find this useful if you'd like to pipe your output (using the `>` operator on the command line) to a separate json file that you can open in a text editor that supports collapse/expansion of nested elements.

### Iterative Algorithm

Works iteratively to find anagrams. Iterates over the entire set of possible sub-word combinations to discover ones that are anagrams of the input phrase. 

Example usage:

```
python3 iterative anthill
```

Output is printed as a compact list of anagrams without any repetitions due to word order:

```
['hill'] ['tan', 'ant']
['thin', 'hint'] ['all']
['tin'] ['hall']
['than'] ['ill']
['halt'] ['nil', 'lin']
```

This method will print matches as they are found, and starts with the anagrams using the fewest number of words and ends with anagrams using the most. The output can be interrupted if you've already got what you want and don't want to wait to see all possibilities. (`Ctrl-C`).