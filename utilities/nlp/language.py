from packagelib import *

class ModuleType:
    NLTK = 0
    GINGERIT = 1
    SPELLCHECKER = 2

class CPGM: # Correcting Spelling and Grammar Mistakes

    def __init__(self, module: ModuleType) -> None:
        nltk.download('words') 
        self.__correct_words = words.words()
        self.__parser = GingerIt()
        self.__module = module
        self.__spell = SpellChecker()

    def correction(self, sentence: str) -> str:
        result = ""
        sentences_list = sentence.split('\n')
        if self.__module == ModuleType.NLTK:
            for s in sentences_list:
                incorrect_words = s.split()
                incorrect_words = list(filter(None, incorrect_words))
                for word in incorrect_words: 
                    temp = [(jaccard_distance(set(ngrams(word, 2)), 
                            set(ngrams(w, 2))),w) 
                            for w in self.__correct_words if w[0]==word[0]]
                    
                result += ' '.join(sorted(temp, key = lambda val:val[0])[0][1])
                result += '\n'

        elif self.__module == ModuleType.GINGERIT:
            for s in sentences_list:
                result += GingerIt().parse(s)

        elif self.__module == ModuleType.SPELLCHECKER:
            for s in sentences_list:
                incorrect_words = s.split()
                incorrect_words = list(filter(None, incorrect_words))
                cors = list()
                for word in incorrect_words: 
                    temp = word.lower()
                    if word not in self.__spell:
                        cors.append(self.__spell.correction(word))
                result += ' '.join(cors)
                result += '\n'

        else:
            print('No module found, return back the sentence')
            result = sentence
            
        return result


