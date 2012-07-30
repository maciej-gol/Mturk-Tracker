""" Simple HIT group classification algorithm based on keywords analysis. """

import string

from unidecode import unidecode


ITERABLE = (list, tuple)


GRAPHICS = "graphics"
AUDIO = "audio"
VIDEO = "video"
TEXT = "text"


class TrainingObject(object):

    def __init__(self, title, description, keywords=''):
        self.title = title
        self.description = description
        self.keywords = keywords

_ = TrainingObject


TRAINING = (
    (
        _("Take a video pretending to be a ferocious dog",
          "Upload a video of yourself visibly attacking a camera as if you "
          "were ferocious dog. Of course this requires you to  have a "
          "recording device."),
        VIDEO,
    ),
    (
        _("Is the Mac Mini powerful enough to act like a TiVo/digital video "
          "recorder?", "Answer this question: Is the Mac Mini powerful enough "
          "to act like a TiVo/digital video recorder?"),
        VIDEO,
    ),
    (
        _("VOB2MP4 time. On an average computer, how long does it take to "
          "convert 1 hour of video in VOB format to MP4 format?", "Answer "
          "this question: VOB2MP4 time. On an average computer, how long does "
          "it take to convert 1 hour of video in VOB format to MP4 format?"
        ),
        VIDEO,
    ),
    (
        _("Mnemonic for International Phonetic Alphabet.", "Answer this "
          "question: Mnemonic for International Phonetic Alphabet. Is there a "
          "sentence or two that has all the words in the International "
          "Phonetic Alphabet (IPA)? The best I've come up with is 'Romeo and "
          "Juliet played Golf and danced the Foxtrot at the Sierra Hotel in "
          "India.' which only includes a few of the letters"),
        TEXT,
    ),
    (
        _("Rewrite this sentence (topic: Surprise visit to my parents' house",
          "Rewrite this sentence so that its meaning remains approximately "
          "the same but the wording is substantially changed"),
        TEXT,
    ),
    (
        _("Sentence Completion Task", "find the noun that best fits the "
          "context of the sentence"),
        TEXT,
    ),
    (
        _("Choose which sentence sounds better", "Choose which English "
          "sentence sounds more natural in 303 pairs of sentences."),
        TEXT,
    ),
    (
        _("Transcribe Audio Recording A278445 (audio length: 1 hour 2 minutes "
          "34 seconds", "Transcribe this audio recording to text"),
        AUDIO,
    ),
    (
        _("Tag Short Audio Clip", "Your task is to listen to this short audio "
          "recording and tag it. Much like you would tag a picture, but for "
          "the audio. "),
        AUDIO,
    ),
    (
        _("Create Audio Transcript from .aiff file", "create audio transcript "
          "from 5 min 15 second aiff files"),
        AUDIO,
    ),
    (
        _("Create a 10s mp3 sound clip of a song",
          "Create a 10s mp3 sound clip of a song, preferably an easily "
          "recognizable part"),
        AUDIO,
    ),

)


class Classificator(object):

    @classmethod
    def learn(cls, training):
        """ Calculates prior probability of classes and conditional probability
            of each word in particular classes. """
        probs = {}, {}
        for test in training:
            document, clazz = test
            # Increase number of the class occurrences.
            counter = probs[0].get(clazz, 0)
            probs[0][clazz] = counter + 1
            # For each word in the training document count probability within
            # class which is assigned to the document.
            for keyword in cls.words(document):
                dictionary = probs[1].get(keyword, {})
                counter = dictionary.get(clazz, 0)
                dictionary[clazz] = counter + 1
                probs[1][keyword] = dictionary
        for keyword in probs[1]:
            num = sum(probs[1][keyword].values())
            for clazz in probs[1][keyword]:
                probs[1][keyword][clazz] /= float(num)
        num = sum(probs[0].values())
        for clazz in probs[0]:
            probs[0][clazz] /= float(num)

        for k in probs[1]:
            print k
            for kk in probs[1][k]:
                print '    {}: {}'.format(kk, probs[1][k][kk])

        return probs

    @classmethod
    def words(cls, doc):
        result = []
        for sentence in [doc.title, doc.description, doc.keywords]:
            # Strip unicode characters, punctuation, etc.
            stripped = string.translate(unidecode(sentence),
                                        string.maketrans("", ""),
                                        string.punctuation)
            # Split string into separate words and append to the words list.
            result.extend(map(string.lower, stripped.split()))
        return result

    def __init__(self, training=TRAINING):
        self.probabilities = self.learn(training)

    def __call__(self, obj):
        return self.classify(obj)

    def classify(self, document):
        """ ??? """
        probabilities = self.probabilities
        result = {}
        for keyword in self.words(document):
            dictionary = probabilities[1].get(keyword, {})
            for clazz in dictionary:
                result[clazz] = result.get(clazz, 0) + dictionary[clazz]# * probabilities[0][clazz]
        return result

