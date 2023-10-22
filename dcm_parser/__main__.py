# dcm_parser/__main__.py
import argparse
from .parse_dcm import DCMParser


def main():
    parser = argparse.ArgumentParser(description="dcm parser")
    # Add an argument 
    parser.add_argument('-dcm', '--dcmfile', type=str,  help='Input dcm file  name')

    args = parser.parse_args()

    if args.dcmfile:
        parser = DCMParser(args.dcmfile)
        dcm_obj = DCMParser.parse_dcm()
        ## extned to your needs.
        # print (dcm_obj)

    else:
        print ('argument not valid')

if __name__ == '__main__':
    main()
