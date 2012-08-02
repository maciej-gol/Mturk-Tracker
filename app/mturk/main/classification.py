""" Simple HIT group classification algorithm based on keywords analysis. """

import re
import string

from unidecode import unidecode


class DocumentClassifier(object):

    # TODO complete this list.
    WORDS = set((
                # Prepositions
                "aboard", "about", "above", "across", "after", "against",
				"along", "amid", "among", "anti", "around", "as", "at",
				"before", "behind", "below", "beneath", "beside", "besides",
				"between", "beyond", "but", "by", "concerning", "considering",
				"despite", "down", "during", "except", "excepting",
				"excluding", "following", "for", "from", "in", "inside",
				"into", "like", "minus", "near", "of", "off", "on", "onto",
				"opposite", "outside", "over", "past", "per", "plus",
				"regarding", "round", "save", "since", "than", "through", "to",
				"toward", "towards", "under", "underneath", "unlike", "until",
				"up", "upon", "versus", "via", "with", "within", "without",

                # Conjunctions
                "although", "and", "far", "if", "long", "soon", "though",
                "well", "because", "both", "either", "even", "how", "however",
                "only", "case", "order", "that", "neither", "nor", "now",
                "once", "or", "provided", "rather", "so", "till", "unless ",
                "when", "whenever", "where", "whereas", "wherever", "whether",
                "while", "yet",

                # Articles
                "the", "a", "an", "some",

                # Other
                "i", "you", "he", "she", "it", "we", "they",
                "me", "your", "him", "her", "its", "us", "your", "them",
                "my", "your", "their", "our",
        ))

    NUMBER = re.compile(r"^\d+$")

    @classmethod
    def isvalid(cls, keyword):
        return keyword not in cls.WORDS and not cls.NUMBER.search(keyword)

    @classmethod
    def keywords(cls, document):
        result = set()
        for keywords in [getattr(document, "title"),
                         getattr(document, "description"),
                         getattr(document, "keywords")]:
            # Strip unicode characters, punctuation, etc.
            stripped =  string.translate(unidecode(keywords),
                                         string.maketrans("", ""),
                                         string.punctuation)
            # Split string into separate lowecase words.
            splitted = map(string.lower, stripped.split())
            # Filter out unwanted words.
            filtered = filter(cls.isvalid, splitted)
            result.update(filtered)
        return result

    @classmethod
    def increment(cls, dictionary, key, default_value=0):
        value = dictionary[key] = dictionary.get(key, default_value) + 1
        return value

    def __init__(self, *args, **kwargs):
        super(DocumentClassifier, self).__init__()
        training_set = kwargs.get('training_set', None)
        prior = kwargs.get('prior', None)
        posterior = kwargs.get('posterior', None)
        probabilities = kwargs.get('probabilities', None)
        if training_set:
            self.probabilities = self.train(training_set)
        elif prior and posterior:
            self.probabilities = prior, posterior
        elif probabilities:
            self.probabilities = probabilities
        else:
            raise Exception("Improperly configured")

    def __call__(self, doc_or_batch):
        if isinstance(doc_or_batch, (tuple, list)):
            return self.classify_batch(doc_or_batch)
        return self.classify(doc_or_batch)

    def classify(self, document):
        raise NotImplementedError

    def classify_batch(self, documents):
        raise NotImplementedError

    def train(self, training_set):
        raise NotImplementedError


class NaiveBayesClassifier(DocumentClassifier):
    """ Classifies documents using Naive Bayes Cassification.
    """

    EPSILON = 1E-5

    def classify(self, document):
        """ ??? """
        prior, posterior = self.probabilities
        result = {}
        from math import log
        for keyword in self.keywords(document):
            probability = posterior.get(keyword, {})
            if not probability:
                continue
            minimal = min(probability.values())
            if self.EPSILON < minimal:
                minimal = self.EPSILON
            else:
                minimal /= 10.0
            for label in prior:
                probability[label] = probability.get(label, self.EPSILON)
            for label in probability:
                result[label] = result.get(label, 0) + log(probability[label])
        for label in result:
            result[label] += log(prior[label])
#            result[label] = e ** result[label]
        return result

    def classify_batch(self, documents):
        """ ??? """
        result = []
        for document in documents:
            result.append(self.classify(document))
        return result

    def train(self, training_set):
        """ Calculates a prior probability of each label occurrence and a
            posterior probability of occurrence each word in a particular
            label.
        """
        # A prior probablity is stored as a dictionary which keys are
        # labels strings and values are calculated probabilities of
        # label occurrence. A posterior probability is stored as a dictionary
        # which keys are words strings with associated dictionaries that holds
        # conditional probability of word occurrence in a particular label.
        prior, posterior = {}, {}
        # Each word occurrences in the training set.
        occurrences = {}
        for test in training_set:
            # Each training entry is tuple storing a document and associated
            # label.
            document, label = test
            # Increase a number of this label occurrences.
            self.increment(prior, label)
            # For each word in the training document, calculate probability
            # of the word occurrence with the label.
            for keyword in self.keywords(document):
                probability = posterior.get(keyword, {})
                self.increment(probability, label)
                posterior[keyword] = probability
                self.increment(occurrences, keyword)
        # Divide each occurrences number to get probability value.
        for keyword in posterior:
            for label in posterior[keyword]:
#                from ipdb import set_trace; set_trace()
                posterior[keyword][label] /= float(occurrences[keyword])
        num_labels = sum(prior.values())
        for label in prior:
            prior[label] /= float(num_labels)
#        for w in occurrences:
#            print w, occurrences[w]
        return prior, posterior
