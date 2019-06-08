import json

def compute_edit_distance(s1,s2):
	if len(s1) > len(s2):
		s1, s2 = s2, s1
	if len(s1)==len(s2):
		for x in range(0,len(s1)-1):
			if s1==(s2[:x]+s2[x+1]+s2[x]+s2[x+2:]):
				return 1
	distances = range(len(s1) + 1)
	for i2, c2 in enumerate(s2):
		distances_ = [i2+1]
		for i1, c1 in enumerate(s1):
			if c1 == c2:
				distances_.append(distances[i1])
			else:
				distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
		distances = distances_
	return distances[-1]

def jaccard_scoreX(typo,correction,k=2):
	if len(typo) == 1 or len(correction) == 1:
		if typo == correction:
			return 1
		else:
			return 0.001
	k_grams_t = set([typo[i:i+k] for i in range(len(typo)-k+1)])
	k_grams_c = set([correction[i:i+k] for i in range(len(correction)-k+1)])
	return max(float(len(k_grams_t & k_grams_c))/(len(k_grams_t | k_grams_c )),0.05)

def get_candidate_wordsX(typo,k_gram_index_map,k,jtol):
	k_grams_t = [typo[i:i+k] for i in range(len(typo)-k+1)]
	num_k_grams_t = len(k_grams_t)
	# postings list walk-through
	ptrs = [0 for i in range(num_k_grams_t)]
	candidate_words = []
	scores = []
	while True:
		curr_postings = []
		for ind in range(num_k_grams_t):
			if k_grams_t[ind] in k_gram_index_map:
				if ptrs[ind] < len(k_gram_index_map[k_grams_t[ind]]):
					curr_postings.append(k_gram_index_map[k_grams_t[ind]][ptrs[ind]])
				else:
					curr_postings.append(None)
			else:
				curr_postings.append(None)
		if curr_postings.count(None) == len(curr_postings):
			break
		curr_word = min(posting for posting in curr_postings if posting is not None)
		to_update = [index for index, w in enumerate(curr_postings) if w == curr_word]
		# jaccard score
		num_common_k_grams = len(to_update)
		num_k_grams_c = len(curr_word)-k+1
		jaccard_score = float(num_common_k_grams)/(num_k_grams_t+num_k_grams_c-num_common_k_grams)
		#if jaccard_score >= jtol:
		candidate_words.append(curr_word)
		scores.append(jaccard_score)
		for ind in to_update:
			ptrs[ind] += 1
	return [x for _,x in sorted(zip(scores,candidate_words), reverse=True)][:25]

if __name__ == "__main__":
	k_gram_index_map = json.load(open('../data/bi-gram-index-map.json'))
	k = 2
	jtol = 0.6
	while True:
		word = raw_input("Enter word ($$$ to break): ")
		if word == "$$$":
			break
		candidate_words = get_candidate_wordsX(word,k_gram_index_map,k,jtol)
		print "\n",candidate_words,"\n"
