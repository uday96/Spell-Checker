import json, argparse
from k_gram_overlap import get_candidate_wordsX,jaccard_scoreX,compute_edit_distance
from math import log,pow,exp

def compute_priors(candidate_words,corpus):
	priors = []
	for word in candidate_words:
		freq = 0
		if word in corpus:
			freq = corpus[word]
		priors.append(freq+1.5)
	return priors

def soundex_code(word):
    word = word.upper()
    code=""
    code=code+word[0]
    soundex_dict = {}
    soundex_dict["BPFV"] ="1"
    soundex_dict["CGJKQSXZ"] ="2"
    soundex_dict["DT"] ="3"
    soundex_dict["L"] ="4"
    soundex_dict["MN"] ="5"
    soundex_dict["R"] ="6"
    soundex_dict["AEIOUHWY"] ="."
    word = word[1:]
    for ch in word:
        for key in soundex_dict.keys():
            if ch in key:
                cd = soundex_dict[key]
                if cd != code[-1]:
                    code +=cd
    code = code.replace(".","")
    code = code[:4].ljust(4,"0")
    return code

def soundex_score(s1,s2):
	if s1==s2:
		return 100
	else:
		if s1[0]==s2[0]:
			if compute_edit_distance(s1[1:],s2[1:])==1:
				return 10
			elif compute_edit_distance(s1[1:],s2[1:])==2:
				return 1
			else:
				return 0.1
		else:
			if s1[1:]==s2[1:]:
				return 10
			else:
				return 0.1

def soundex_score2(s1,s2):
	if s1==s2:
		return 100
	else:
		if s1[0]==s2[0]:
			if compute_edit_distance(s1[1:],s2[1:])==1:
				return 50
			elif compute_edit_distance(s1[1:],s2[1:])==2:
				return 10
			else:
				return 0.1
		else:
			if s1[1:]==s2[1:]:
				return 50
			else:
				return 0.1

def get_candidate_words2(words,dictionary):
	words2 = set([])
	all_words2 = set([])
	for word in words:
		cwords, all_edit_2 = get_candidate_words(word,dictionary)
		words2.update(cwords)
		all_words2.update(all_edit_2)
	return words2,all_words2

def get_candidate_words(typo,dictionary):
	alphabets = "abcdefghijklmnopqrstuvwxyz"
	tn = len(typo)
	candidate_words = []
	all_edit_dist_1 = []
	#edit distance 1 - deletion
	for alphabet in alphabets:
		for i in range(tn+1):
			cword = typo[:i]+alphabet+typo[i:]
			all_edit_dist_1.append(cword)
			if cword in dictionary:
				candidate_words.append(cword)
	#edit distance 1 - insertion
	for i in range(tn+1):
		cword = typo[:i]+typo[i+1:]
		all_edit_dist_1.append(cword)
		if cword in dictionary:
			candidate_words.append(cword)
	#edit distance 1 - substitution
	for alphabet in alphabets:
		for i in range(tn+1):
			cword = typo[:i]+alphabet+typo[i+1:]
			all_edit_dist_1.append(cword)
			if cword in dictionary:
				candidate_words.append(cword)
	#edit distance 1 - reversal
	for i in range(tn-1):
		cword =  typo[:i]+typo[i+1]+typo[i]+typo[i+2:]
		all_edit_dist_1.append(cword)
		if cword in dictionary:
			candidate_words.append(cword)
	return candidate_words, all_edit_dist_1

def word_spell_check(word,dictionary,k_gram_index_map,corpus,k,jtol,limit,use_second_edit=True,use_k_gram=True,soundex_dict={}):
	s1 = soundex_code(word)
	if use_second_edit:
		candidate_words, all_edit_dist_1 = get_candidate_words(word,dictionary)
		candidate_words2, all_edit_dist_2 = get_candidate_words2(all_edit_dist_1,dictionary)
		candidate_words2.update(candidate_words)
	else:
		candidate_words2, all_edit_dist_1 = get_candidate_words(word,dictionary)
	candidate_words2 =set(candidate_words2)
	if use_k_gram:
		candidate_words2.update(get_candidate_wordsX(word,k_gram_index_map,k,jtol))
	candidate_words2 =set(candidate_words2)
	if s1 in soundex_dict:
		for x in soundex_dict[s1]:
			if compute_edit_distance(x,word)<=4:
				candidate_words2.update([x])
	candidate_words2 = list(candidate_words2)
	priors = compute_priors(candidate_words2,corpus)
	solution = [correction for _,correction in sorted(zip(priors,candidate_words2),reverse=True)]
	scores=[]
	for x in solution:
		s2 = soundex_code(x)
		s_score = soundex_score(s1,s2)
		#s_score = 1
		if use_k_gram:
			scores.append(s_score*jaccard_scoreX(x,word)*log(compute_priors([x],corpus)[0])/exp((compute_edit_distance(x,word)+1)))
		else:
			scores.append(s_score*log(compute_priors([x],corpus)[0])/exp((compute_edit_distance(x,word)+1)))
	solution =  [(x,y) for y,x in sorted(zip(scores,solution),reverse=True)]
	return solution[:limit]

if __name__ == "__main__":

	#parsing arguments from command line
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", help="path to test data file",type=str)
	parser.add_argument("--output", help="path to output file",type=str)
	args = parser.parse_args()

	try:
		infile = open(args.input,"r")
		outfile = open(args.output,"w")
	except Exception as e:
		parser.print_help()
		quit()

	# print "Loading dict..."
	dictionary = json.load(open("../data/dict.json"))
	soundex_dict = json.load(open("../data/soundex.json"))
	# print "Loading corpus..."
	corpus = json.load(open('../data/corpus-freq.json'))
	k_gram_index_map = json.load(open('../data/bi-gram-index-map.json'))
	k = 2
	jtol = 0.25
	limit_results = 10
	for word in infile.readlines():
		if word[-1] == "\n":
			word = word[:-1]
		solution = word_spell_check(word,dictionary,k_gram_index_map,corpus,k,jtol,limit_results,True,True,soundex_dict)
		# print "\n",solution,"\n"
		outfile.write(word)
		for correction in solution:
			outfile.write("\t"+correction[0])
		outfile.write("\n")
	infile.close()
	outfile.close()
