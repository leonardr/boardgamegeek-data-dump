from pdb import set_trace
import os
from game import Game
import jsonpickle
import datetime
import sys

INPUT_PATH = "BoardGameGeek.xml/%s/boardgame_batches/"
OUTPUT_PATH = "BoardGameGeek.json/%s/boardgame_batches/"

if len(sys.argv) > 1:
    DATE_DIR = sys.argv[1]
else:
    DATE_DIR = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m")

input_dir = INPUT_PATH % DATE_DIR
output_dir = OUTPUT_PATH % DATE_DIR
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for filename in sorted(os.listdir(input_dir)):
    output_filename = filename.replace(".xml", ".json")
    output_path = os.path.join(output_dir, output_filename)
    if os.path.exists(output_path):
        print "Skipping %s" % output_filename
    else:
        print "Writing %s" % output_path
        game = Game.from_xml(open(os.path.join(input_dir, filename)))
        open(output_path, "w").write(jsonpickle.encode(game))


