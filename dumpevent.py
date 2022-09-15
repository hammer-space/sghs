import sys
import pickle
import pprint

import shothammer


EVENT = sys.argv[1]
PP = pprint.PrettyPrinter(indent=4)

with open(EVENT, 'rb') as F:
    data = pickle.load(F)

PP.pprint(data)