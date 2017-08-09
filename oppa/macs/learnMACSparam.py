"""
this module is actual fix some parameter by using
bayesian optimization. if we run this function in parallel,
we need to satisfied many condition which mentioned in the paper
named 'practical bayesian optimization in machine learning algorithm'
"""
from math import exp
import subprocess
import time
import os
from multiprocessing import cpu_count
from multiprocessing import Process , Manager
import multiprocessing

from ..optimizeHyper import run as optimizeHyper
from ..calculateError import run as calculateError
from ..loadParser.loadLabel import run as loadLabel
from ..loadParser.parseLabel import run as parseLabel


def learnMACSparam(args, test_set, validation_set, PATH):
	"""
    this function actually control learning steps. args is given by
    OPPA1 ( main function of this program ) from command line.
    and make wrapper_function to use BayesianOptimization library,
    only wrapper_function`s arguments will be learned by library.

    :param args:
        argument from command lines

    :param test_set:
        python list of test set

    :param validation_set:
        python list of validation set

    :return: learned parameter.
	"""
	input_file = args.input
	control = args.control
	call_type = args.callType

	# result value about bayesian optimization
	manager = Manager()
	return_dict = manager.dict()	

	# make result directory
	os.makedirs(PATH + '/MACS')

	# set parameter bounds
	if call_type == "broad":
		parameters_bounds = {'opt_Qval':(10**-8,60.0),\
				'opt_cutoff':(10**-7,60.0)}
	else:
		parameters_bounds = {'opt_Qval':(10**-8,60.0)}
	
	# set number of initialize sample in bayesian optimization
	number_of_init_sample = 1 

	# get chromosome list
	chromosome_list = []
	for label in validation_set + test_set:
		chromosome_list.append(label.split(':')[0])
	chromosome_list = sorted(list(set(chromosome_list)))

	# set file name
	reference_char = ".REF_"
	bam_name = input_file[:-4]  ## delete '.bam'
	if control is not None:
		cr_bam_name = control[:-4]

	# multiprocessing queue
	MAX_CORE = cpu_count()
	learning_processes = []

	# create process to run in parallel by each benchmark data
	for chromosome in chromosome_list:
		
		if call_type == "broad":
			# create wrapper function about broad peak calling
			def wrapper_function_broad(opt_Qval, opt_cutoff):
				target = bam_name + reference_char + chromosome + '.bam'
				cr_target = None
				if control is not None:
					cr_target = cr_bam_name + '.bam'
				accuracy = run(target, validation_set, str(exp(opt_Qval/100)-1),\
						call_type, PATH, cr_target, broad=str(exp(opt_cutoff/100)-1))
				print chromosome,\
					"Qval :" + str(round(exp(opt_Qval/100)-1,4)),\
					"Broad-cutoff:" + str(round(exp(opt_cutoff/100)-1,4)),\
					"score:" + str(round(accuracy,4))
				return accuracy
			# set function will be input of bayesian optimization
			function = wrapper_function_broad
		else:
			# create wrapper function about narrow peak calling
			def wrapper_function_narrow(opt_Qval):
				target = bam_name + reference_char + chromosome + '.bam'
				cr_target = None
				if control is not None:
					cr_target = cr_bam_name + '.bam'
				accuracy = run(target, validation_set, str(exp(opt_Qval/100)-1)\
						, call_type, PATH, cr_target)
				print chromosome,\
					"Qval :" + str(round(exp(opt_Qval/100)-1,4)),\
					"score:" + str(round(accuracy,4))
				return accuracy
			# set function will be input of bayesian optimization
			function = wrapper_function_narrow
		
		# each learning_process and wrapper function will be child process of OPPA
		learning_process = multiprocessing.Process(target=optimizeHyper, args=(function,\
					parameters_bounds, number_of_init_sample, return_dict, 10, 'ei', chromosome,))

		# running each bayesian optimization process in parallel by multiprocessing in python.
		if len(learning_processes) < MAX_CORE - 1:
			learning_processes.append(learning_process)
			learning_process.start()
		else:
			keep_wait = True
			while True:
				time.sleep(0.1)
				if not (keep_wait is True):
					break
				else:
					for process in reversed(learning_processes):
						if process.is_alive() is False:
							learning_processes.remove(process)
							learning_processes.append(learning_process)
							learning_process.start()
							keep_wait = False
							break
	for proc in learning_processes:
		  proc.wait()
	print return_dict
	return return_dict	

def run(input_file, valid_set, Qval, call_type, PATH, control = None, broad=None):
	"""
    this function run MACS and calculate error at once.
    each arguments will be given by learnMACSparam that from command line.

    :param input_file:
        input file name.
    :param valid_set:
        python list of labeled data
    :param Qval:
        Q-value of MACS. it will be learned.
    :param control:
        control bam file in MACS. not necessary.

    :return:
        error rate of between MACS_output and labeled Data.
	"""
	import MACS
	output_PATH = PATH + '/MACS/' + input_file
	input_file = PATH + '/' + input_file

	process = MACS.run(input_file, Qval, call_type, control=control, broad=broad)
	process.wait()

	if call_type == "broad":
		output_format_type = '.broadPeak'
	else:
		output_format_type = '.narrowPeak'

	peakCalled_file = output_PATH[:-4] + ".bam_peaks" + output_format_type

	if not valid_set:
		print "there are no matched validation set :p\n"
		exit()
	else:
		error_num, label_num = calculateError(peakCalled_file, parseLabel(valid_set, peakCalled_file))
		if os.path.isfile(peakCalled_file):
			os.remove(peakCalled_file)
		else:
			print "there is no result file."
	if label_num is 0:
		return 0.0
		
	return (1 - error_num/label_num)


def summerize_error(bam_name, validation_set, call_type):
	"""

    :param bam_name:
    :param validation_set:
    :return:
	"""
	sum_error_num = 0
	sum_label_num = 0
	reference_char = ".REF_chr"
	if call_type == "broad":
		output_format_name = '.broadPeak'
	else:
		output_format_name = '.narrowPeak'

	for chr_no in range(22):
		input_name = bam_name + reference_char + str(chr_no+1) + ".bam_peaks" + output_format_name
		error_num, label_num = calculateError(input_name, parseLabel(validation_set, input_name))
		sum_error_num += error_num
		sum_label_num += label_num

    # add about sexual chromosome
		input_name = bam_name + reference_char + 'X' + ".bam_peaks" + output_format_name
		error_num, label_num = calculateError(input_name, parseLabel(validation_set, input_name))
		sum_error_num += error_num
		sum_label_num += label_num
    
		input_name = bam_name + reference_char + 'Y' + ".bam_peaks" + output_format_name
		error_num, label_num = calculateError(input_name, parseLabel(validation_set, input_name))
		sum_error_num += error_num
		sum_label_num += label_num

	return sum_error_num , sum_label_num

