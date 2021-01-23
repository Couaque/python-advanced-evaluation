import sys, os, time
from puzzlelib import parse_puzzle, parse_file, resolve

starttime = time.time()

puzzle = parse_file(sys.argv[1])
print(puzzle.isSolvable())

print('8-puzzle executed in %s seconds' % (time.time() - starttime))