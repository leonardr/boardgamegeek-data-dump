import os
from game import Geeklist
import jsonpickle

from pdb import set_trace
import os
from game import Game
import datetime
import sys


INPUT_PATH = "BoardGameGeek.xml/%s/geeklist/"
OUTPUT_PATH = "BoardGameGeek.json/%s/geeklist/"

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
        input_path = os.path.join(input_dir, filename)
        print "%s -> %s" % (input_path, output_path)
        geeklist = Geeklist.from_xml(open(input_path))
        if geeklist is None:
            print "Couldn't scrape that one."
        else:
            open(output_path, "w").write(jsonpickle.encode(geeklist))

