from k_gram_overlap import *
from word_spell_check import *
import math, operator, argparse
from copy import deepcopy

def phrase_prob(phrase_combinations,ngram_freq1,corpus):
	prob_scores = []
	for phraseX in phrase_combinations:
		phrase = phraseX[0]
		edit_dist = phraseX[1]
		s_score = phraseX[2]
		words = phrase.split()
		prob_score = 1
		for x in range(0,len(words)-1):
			if ((words[x] in ngram_freq1) and (words[x+1] in ngram_freq1[words[x]])) and (words[x] in corpus):
				prob_score=prob_score*((ngram_freq1[words[x]][words[x+1]]+0.5)/(corpus[words[x]]+len(corpus)))
			elif words[x] in corpus:
				prob_score=prob_score*((0.5)/(corpus[words[x]]+len(corpus)))
			elif ((words[x] in ngram_freq1) and (words[x+1] in ngram_freq1[words[x]])):
				prob_score=prob_score*((ngram_freq1[words[x]][words[x+1]]+0.5)/(len(corpus)))
			else:
				prob_score=prob_score*((0.5)/(len(corpus)))
		prob_scores.append(s_score*prob_score/(edit_dist+1))
	return prob_scores

def find_misspelled(phrase,dictionary):
	parts = phrase.split(" ")
	for i in range(len(parts)):
		if parts[i].lower() not in dictionary:
			return parts[i],i
	return "",-1

def context_spell_check_naive(parts,windex,ngram_freq1,corpus,homonyms_map,soundex_dict):
	phrase_combinations = []
	permute_indices = []
	if windex > -1:
		permute_indices.append(windex)
	else:
		permute_indices = [i for i in range(len(parts))]
	for index in permute_indices:
		s1 = soundex_code(parts[index])
		left_part_str = ' '.join(parts[:index])
		right_part_str = ' '.join(parts[index+1:])
		candidate_words = []
		if index != windex:
			limit_results = 20
			if parts[index].lower() in homonyms_map:
				candidate_words.extend(homonyms_map[parts[index].lower()])
			candidate_words.extend([ w[0] for w in word_spell_check(parts[index].lower(),dictionary,k_gram_index_map,corpus,k,jtol,limit_results,False,False,soundex_dict)])
		else:
			limit_results = 20
			candidate_words.extend([ w[0] for w in word_spell_check(parts[index].lower(),dictionary,k_gram_index_map,corpus,k,jtol,limit_results,True,True,soundex_dict)])
		candidate_words = list(set(candidate_words))
		for cword in candidate_words:
			if cword not in parts and cword.title() not in parts:
				s2 = soundex_code(cword)
				new_phrase = ' '.join([left_part_str,cword,right_part_str]).strip()
				if new_phrase != ' '.join(parts):
					phrase_combinations.append((new_phrase,compute_edit_distance(cword,parts[index]),soundex_score(s1,s2)))
	prob_scores = phrase_prob(phrase_combinations,ngram_freq1,corpus)
	return [(x[0],y) for y,x in sorted(zip(prob_scores,phrase_combinations), reverse=True)][:3]

if __name__ == "__main__":

	#parsing arguments from command line
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", help="path to test data file",type=str)
	parser.add_argument("--output", help="path to output file",type=str)
	args = parser.parse_args()
	alphabets = "abcdefghijklmnopqrstuvwxyz".upper()
	try:
		infile = open(args.input,"r")
		outfile = open(args.output,"w")
	except Exception as e:
		parser.print_help()
		quit()

	# print "Loading dict..."
	dictionary = json.load(open("../data/dict.json"))
	soundex_dict = json.load(open("../data/soundex.json"))
	# print "Loading index maps..."
	k_gram_index_map = json.load(open('../data/bi-gram-index-map.json'))
	ngram_freq1 = json.load(open("../data/bigram_dict.json"))
	ngram_freq2 = json.load(open("../data/bigram_dict_reverse.json"))
	homonyms_map = json.load(open("../data/homonyms-dict.json"))
	# print "Loading corpus..."
	corpus = json.load(open('../data/corpus-freq.json'))
	k = 2
	jtol = 0.25
	for phrase in infile.readlines():
		if phrase[-1]=='\n':
			phrase = phrase[:-1]
		if phrase[-1]=='.':
			phrase = phrase[:-1]
		words = phrase.split( )
		wordX,indx = find_misspelled(phrase,dictionary)
		candidate_words = []
		if len(wordX)>0:
			req_dict = {}
			try:
				if indx==len(words)-1:
					req_dict = deepcopy(ngram_freq1[words[indx-1]])
				elif indx==0:
					req_dict = deepcopy(ngram_freq2[words[1]])
				else:
					req_dict = deepcopy({ k: ngram_freq1[words[indx-1]].get(k, 0) + ngram_freq2[words[indx+1]].get(k, 0) for k in set(ngram_freq1[words[indx-1]]) | set(ngram_freq2[words[indx+1]]) })
			except Exception as e:
				req_dict = {}
			for key in req_dict.keys():
				if compute_edit_distance(key,wordX) > 3:
					del req_dict[key]
			if len(req_dict)>0:
				for x in req_dict:
					edit_dist = compute_edit_distance(x,wordX)
					freq = req_dict[x]
					req_dict[x] = math.log(freq)/math.exp(edit_dist)
				sorted_x = sorted(req_dict.items(), key=operator.itemgetter(1), reverse = True)
				outfile.write(wordX)
				count = 3
				ls = [wordX.lower()]
				for correction in sorted_x:
					if (correction[0].lower() in ls) or (correction[0][0] in alphabets and correction[0][0].lower()!=wordX[0].lower()) or (correction[0].lower() not in dictionary):
						continue
					else:
						ls.append(correction[0].lower())
						count=count-1
						outfile.write("\t"+correction[0])
					if count==0:
						break
				outfile.write("\n")
				continue
			else:
				candidate_phrases =  context_spell_check_naive(words,indx,ngram_freq1,corpus,homonyms_map,soundex_dict)
		else:
			candidate_phrases =  context_spell_check_naive(words,indx,ngram_freq1,corpus,homonyms_map,soundex_dict)
		ll = candidate_phrases[0][0].split()
		wfile = [y for y,x in zip(words,ll) if x.lower()!=y.lower()][0]
		outfile.write(wfile)
		for correction in candidate_phrases[:3]:
			cc = list(set(correction[0].split())-set(words))
			if len(cc) > 0:
				outfile.write("\t"+cc[0])
		outfile.write("\n")
	infile.close()
	outfile.close()
