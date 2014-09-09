
import argparse
from AttrLib.parser import Parser
from setting import LANGS_BY_NAME

def main(src_dir, dst_dir, targets):
    parser = Parser()
    rep = parser.parse_dir(src_dir)
    for target in targets:
        print "Compiling to {}".format(target)
        writer = LANGS_BY_NAME[target].writer()
        writer.construct(rep)
        writer.write(dst_dir)

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="compile .atr files into an implmentation language")
    p.add_argument("SRC_DIR", help="Directory containing .atr files")
    p.add_argument("DST_DIR", help="Directory to put created files")
    p.add_argument("TARGET", nargs="+", choices=LANGS_BY_NAME,
                   help="The target languages")
    args = p.parse_args()
    src_dir = args.SRC_DIR
    dst_dir = args.DST_DIR
    targets = set(args.TARGET)
    main(src_dir, dst_dir, targets)
