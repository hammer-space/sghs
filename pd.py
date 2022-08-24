import pickle
import pprint
from sys import argv

pp = pprint.PrettyPrinter(indent=4)

with open(argv[1], 'rb') as F:
	event = pickle.load(F)
	pp.pprint(event)

