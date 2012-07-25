""" Simple HIT group classification algorithm based on keywords analysis. """

import string


ITERABLE = (list, tuple)

CLASSES = {
#    "audio": (
#        ("keywords", "any", ("sound", "transcription", "transcribe")),
#        ("title", "any", ("transcribe", "transcript", "title")),
#    ),
    "image": (
        ("keywords", "any", ("photo", "image", "color", "picture",
                             "pictures")),
    ),
}


class Classify(object):

    @classmethod
    def _in(cls, smaller, larger):
        return map(lambda sm: sm in larger, smaller)

    @classmethod
    def _any(cls, smaller, larger):
        """ Returns True if larger list contains any element from smaller
            list. """
        return any(cls._in(smaller, larger))

    @classmethod
    def _all(cls, smaller, larger):
        """ Returns True if larger list contains all elements from smaller
            list. """
        return all(cls._in(smaller, larger))

    def __init__(self, classes=CLASSES):
        self.classes = classes

    def __call__(self, obj):
        return self.classify(obj)

    def classify(self, obj):
        classes = self.classes
        for name in classes:
            conditions = classes[name]
            assert isinstance(conditions, ITERABLE)
            function = {"any": self._any, "all": self._all}
            for condition in conditions:
                attribute = getattr(obj, condition[0])
                if isinstance(attribute, basestring):
                    # Will raise UnicodeEncodeError in case of not latin
                    # chars but is required by stripping.
                    attribute = str(attribute)
                    # Strip punctation chars.
                    stripped = string.translate(attribute,
                                                string.maketrans("", ""),
                                                string.punctuation)
                    # Split string to separated words.
                    splitted = map(string.lower, stripped.split(" "))
                     if function[condition[1]](condition[2], splitted):
                        print "Name: {} by {}".format(name, condition[0])


