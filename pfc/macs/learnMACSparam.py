"""
this module is actual fix some parameter by using
bayesian optimization. if we run this function in parallel,
we need to satisfied many condition which mentioned in the paper
named 'practical bayesian optimization in machine learning algorithm'
"""

from subprocess import call
from subprocess import Popen
import argparse
import numpy as np

from ..calculateError import run as calculateError
from ..loadParser.loadLabel import run as loadLabel
from ..loadParser.parseLabel import run as parseLabel

def get_error(input_file, valid_set):
    """return calculated error that compare label with output of MACS"""

    error = calculateError(input_file, parseLabel(valid_set, input_file))
    return error


def run(args):
    import MACS

    learned_Qval = args.Qval

    """it will be runned by protoPFC.py"""
    bam_name = args.input[:-4]  ## delete '.bam'
    reference_char = ".REF_chr"

    """
    p1 = MACS.run(bam_name + reference_char + "1.bam", args)
    p2 = MACS.run(bam_name + reference_char + "2.bam", args)
    p3 = MACS.run(bam_name + reference_char + "3.bam", args)
    p4 = MACS.run(bam_name + reference_char + "4.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()

    p1 = MACS.run(bam_name + reference_char + "5.bam", args)
    p2 = MACS.run(bam_name + reference_char + "6.bam", args)
    p3 = MACS.run(bam_name + reference_char + "7.bam", args)
    p4 = MACS.run(bam_name + reference_char + "8.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()

    p1 = MACS.run(bam_name + reference_char + "9.bam", args)
    p2 = MACS.run(bam_name + reference_char + "10.bam", args)
    p3 = MACS.run(bam_name + reference_char + "11.bam", args)
    p4 = MACS.run(bam_name + reference_char + "12.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()

    p1 = MACS.run(bam_name + reference_char + "13.bam", args)
    p2 = MACS.run(bam_name + reference_char + "14.bam", args)
    p3 = MACS.run(bam_name + reference_char + "15.bam", args)
    p4 = MACS.run(bam_name + reference_char + "16.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()
    
    p1 = MACS.run(bam_name + reference_char + "17.bam", args)
    p2 = MACS.run(bam_name + reference_char + "18.bam", args)
    p3 = MACS.run(bam_name + reference_char + "19.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()

    p1 = MACS.run(bam_name + reference_char + "20.bam", args)
    p2 = MACS.run(bam_name + reference_char + "21.bam", args)
    p3 = MACS.run(bam_name + reference_char + "22.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()
    
    p1 = MACS.run(bam_name + reference_char + "M.bam", args)
    p2 = MACS.run(bam_name + reference_char + "X.bam", args)
    p3 = MACS.run(bam_name + reference_char + "Y.bam", args)
    p1.wait()
    p2.wait()
    p3.wait()

    """

    """The ErrorCalculation can be also parallel by choromosome.
    """

    ## load labeled file.
    exist_test_set = True
    test_set, validation_set = loadLabel(args.validSet)
    print "# of test set is      :: " + str(len(test_set))
    print "# of validation set is :: " + str(len(validation_set))

    ## there must be valid validation set and test set.
    if not test_set or not validation_set:
        print "there are no matched validation set :p\n"
        exit()

    ## actual learning part
    else:
        print calculateError("H3K4me3_CD4_Tcell.REF_chr11.broadPeak", parseLabel(validation_set, "H3K4me3_CD4_Tcell.REF_chr11.broadPeak"))
