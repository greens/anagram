#!/usr/local/bin/python3

import sys, json, re, pickle, pptree, argparse
from itertools import combinations, chain
from functools import reduce
from operator import mul
from multiprocessing import Pool

# our mapping of word signatures -> admissable words
dictionary = {}
# the mapping of letters to prime numbers
primes = {'a': 2, 'b': 3, 'c': 5, 'd': 7, 'e': 11, 'f': 13, 'g': 17, 'h': 19, 'i': 23, 
					'j': 29, 'k': 31, 'l': 37, 'm': 41, 'n': 43, 'o': 47, 'p': 53, 'q': 59, 
					'r': 61, 's': 67, 't': 71, 'u': 73, 'v': 79, 'w': 83, 'x': 89, 'y': 97, 'z': 101}
# the signatures of the legal sub-words of our input phrase
perms = []
# stores the input phrase after spaces are removed
base = ""
# stores the computed signature of our phrase
base_signature = 0

# file location for our stored dictionary
DICTIONARY_PICKLE = "edited_dict"

class Node:
	''' 
	A class to be used as a node in an n-ary tree.

	...

	Attributes
	----------
	value : object
		the value of this particular node
	children : list (of Nodes)
		the children of this node of the tree
	'''
	def __init__(self, value, children=[]):
		self.value = value
		self.children = children

	def __str__(self):
		return str(self.value)

def factor_to_tree(value, numbers):
	"""
	Recursively factor an word signature to all of its factorizations using only the provided set 
	of factors. Intended to create a tree. The return value should be passed as the children 
	of a new Node whose value is the string whose value is passed to this function and whose children 
	are the result of this function.

	Args:
			value (int): the number to be factored
			numbers (list (ints)): a list of integers to use as factors to factor the value

	Returns:
			(list (Node)): a list of Nodes that are the factors of the value
	"""
	factorizations = []
	for number in numbers:
		# The number should divide evenly and not be equivalent
		if value != number and value % number == 0:
			# Factor the remainder
			factored = factor_to_tree(int(value/number), numbers)
			# If there are any factors...
			if len(factored) > 0:
				# add them to the list of this number's factors
				# convert the root value to its word equivalents first
				factorizations.append(Node(dictionary[number], factored))
		elif value == number:
			# we cannot factor any deeper, so return the value without any children
			return [Node([dictionary[value]])]
	return factorizations

def factor(value, numbers):
	"""
	Factor an integer to all of its factorizations using only the provided set of factors. 
	Stores the values as nested lists of dictionaries. Meant to be output as JSON.

	Args:
			value (int): the number to be factored
			numbers (list (ints)): a list of integers to use as factors to factor the value

	Returns:
			(list (dict)): a list of dictionaries that are the factors of the value
	"""
	factorizations = []
	for number in numbers:
		if value % number == 0 and int(value/number) != 1:
			factored = factor(int(value/number), numbers)
			if (type(factored) is int or len(factored) != 0):
				factorizations.append({str(dictionary[number]) : factored})
		elif value/number == 1:
			return dictionary[value]
	return factorizations

def prod(iterable):
	"""
	Multiply all the numbers of a list together.

	Args:
			iterable (iterable (ints)): a collection of integers

	Returns:
			int: the value of all the numbers mutliplied together
	"""	
	return reduce(mul, iterable, 1)

def word_signature(word):
	"""
	Encodes a word using the multiplicative sum of the prime numbers associated with
	its comoponent letters.

	Args:
			word (string): The word to generate the encoding of

	Returns:
			int: The word's encoding
	"""	
	return prod([primes[x] for x in word])

def sub_word_signatures(word):
	"""
	Generates all of the signatures of all of the sub-words in the dictionary for
	the given string of letters.

	Args:
			word (string): the collection of letters to find all sub-words of

	Returns:
			list (int): the signatures of all the legal sub-words
	"""	
	word_perms = []
	# for all lengths of letter combinations less than the full length of the test phrase...
	for i in range(1, len(word)+1):
		# add all the signatures of those letter combinations to a list
		word_perms.extend(map(word_signature, combinations(word, i)))
	# filter that list so it only contains signatures in our dictionary and remove duplicates	
	word_perms = filter(lambda signature: signature in dictionary, set(word_perms))
	# sort the list so that the longest words (biggest signatures) are returned first
	return sorted(list(word_perms), reverse=True)

def pre_filter(combs):
	"""
	Tests whether the total number of letters in a set of words is equal to the
	number of letters in the phrase we are generating anagrams for. Meant to filter
	out some of the combinations before the full testing is done.

	Args:
			combs (list (int)): a combination of legal sub-word signatures of the phrase in question

	Returns:
			boolean: Whether the phrase is the same length as the test phrase
	"""	
	# sum the length of each word in our list of signatures and compare it
	return sum(len(dictionary[x][0]) for x in combs) == len(base)

def combs_by_size(size):
	"""
	Given a length, return most combinations of legal sub-words of the test phrase
	containing that many words. Result is filtered by pre_filter.

	Args:
			size (int): number of words to include in the combination

	Returns:
			list(list(strings)): All combinations of [size] sub words whose total number
													 	of letters is equal to the test phrase
	"""	
	return filter(pre_filter, set(combinations(perms,size)))

def prod_and_filter(combination):
	"""
	Takes a list of word signatures and passes them through if they are an anagram of the 
	test phrase. Returns false otherwise. Written this way so that it can be parallelized.

	Args:
			combination (list(int)): List of word signatures to test

	Returns:
			list(int) or False: If the input is a full anagram, it is passed through, otherwise
														false is returned.
	"""	
	if prod(combination) == base_signature:
		return combination
	else:
		return False

def create_dict(args):
	"""
	Create the mapping of word signatures -> legal words and store it in a binary file for
	re-use. By default uses the 20k most common words appearing in a corpus gathered from
	several (US English) sources.

	Args:
			args.f (File): File to use as our source of words.
	"""	
	global dictionary
	scrabble_words = []

	# generate a list of admissible scrabble words (i.e. not proper nouns) that we can
	# use to filter out very small "words" that don't make good anagrams
	with open("scrabble_words.txt") as infile:
		scrabble_words = [word.strip().lower() for word in infile.readlines() if len(word.strip()) > 1 and len(word.strip()) < 5]

	# read in the words from our dictionary
	with args.f as infile:
		for word in infile.read().split('\n'):
			# guarantee we're working with a lowercase word with no spaces
			word = word.strip().lower()
			# the only one-letter words we want are 'a' and 'i'
			if len(word) == 1 and word != 'a' and word != 'i':
				continue
			# the only short words we want are ones in the scrabble dictionary
			elif len(word) > 1 and len(word) < 5 and word not in scrabble_words:
				continue
			# compute the word's signature
			product = word_signature(word)
			if product != 1:
				# if we don't yet have an entry for this word, create it
				if product not in dictionary:
					dictionary[product] = [word]
				# if we already have an entry, extend it. This ensures we get a list of all words that are anagrams
				# of each other for each signature
				else:
					dictionary[product].append(word)

	with open(DICTIONARY_PICKLE, 'wb') as outfile:
		# write our dictionary to a file to read it later
		pickle.dump(dictionary, outfile)

def prepare_data(word):
	"""
	Loads the dictionary, sanitizes the input phrase, and computes its signature

	Args:
			word (list(strings)): the input phrase
	"""	
	global base
	global dictionary
	global base_signature
	global perms
	base = ''.join(word[0]).lower()

	with open(DICTIONARY_PICKLE, 'rb') as infile:
		dictionary = pickle.load(infile)

	base_signature = word_signature(base)
	perms = sub_word_signatures(base)

def recursive(args):
	"""
	Recursive method for computing anagrams. Prints the result as either JSON or a tree.

	Args:
			args.words (list(strings)): the input phrase
			args.json (boolean): flag that determines output format
	"""	
	prepare_data(args.words)
	if args.json:
		anagrams = factor(base_signature, perms)
		print(json.dumps(anagrams, indent=2))
	else:
		anagrams = Node(base,factor_to_tree(base_signature, perms))
		# third-party library for printing trees in a human-friendly format
		pptree.print_tree(anagrams)

def iterative(args):
	"""
	Iterative method for computing anagrams. Prints the result as a series of anagrams.

	Args:
			args.words (list(strings)): the input phrase
	"""	
	prepare_data(args.words)
	# limit the length of anagram strings based on the size of the word, 
	# we don't want 4 word anagrams of short words as they are rarely interesting
	max_words = min(round(len(base)/4) + 1, 5)

	with Pool(8) as p:
		# generate all possible combinations of sub-words
		all_combs = chain.from_iterable(p.imap_unordered(combs_by_size, range(1,max_words)))
		# test the combinations for whether they are an anagram or not
		for possibility in p.imap_unordered(prod_and_filter, all_combs, 250):
			# if it is an anagram
			if (possibility):
				#print it
				print(" ".join(map(lambda x: str(dictionary[x]), possibility)))

def main():
	# this just sets up our command-line parsing
	parser = argparse.ArgumentParser("Find anagrams of a given word or phrase.")
	subparsers = parser.add_subparsers(help='sub commands', dest="sub_parser")

	dict_parser = subparsers.add_parser('build', help='build dictionary')
	dict_parser.add_argument('-f', default='20k_words.txt', type=argparse.FileType('r'), help='File containing ine-separated list of words to build a dictionary from.')
	dict_parser.set_defaults(func=create_dict)

	recursive_parser = subparsers.add_parser('recursive', help="parse recursively")
	recursive_parser.add_argument('words', metavar='word', nargs='+', action='append', help="The word(s) to find anagrams for. Spaces will be ignored.")
	recursive_parser.add_argument('--json', action='store_true', help='Write the output as json.')
	recursive_parser.set_defaults(func=recursive)

	iterative_parser = subparsers.add_parser('iterative', help="parse iteratively")
	iterative_parser.add_argument('words', metavar='word', nargs='+', action='append', help="The word(s) to find anagrams for. Spaces will be ignored.")
	iterative_parser.set_defaults(func=iterative)

	args = parser.parse_args()
	args.func(args)

if __name__ == "__main__":
	main()