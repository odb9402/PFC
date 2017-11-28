import time
import os
import glob
import re
from multiprocessing import Process, Manager, cpu_count
import multiprocessing

from ..optimizeHyper import run as optimizeHyper
from ..calculateError import run as calculateError
from ..loadParser.parseLabel import run as parseLabel
from ..loadParser.loadPeak import run as loadPeak
from SICER import run as SICER

def learnSICERparam(args, test_set, validation_set, PATH, kry_file=None):
    """

    :param args:
    :param test_set:
    :param validation_set:
    :param PATH:
    :param kry_file:
    :return:
    """

    input_file = args.input
    control = args.control
    chromosome_list = []
    cpNum_files = []
    cpNum_controls = []

    manager = Manager()
    return_dict = manager.dict()

    if not os.path.exists(PATH + '/SICER'):
        os.makedirs(PATH + '/SICER')

    parameters_bounds = {'windowSize': (1.0/12.0 , 1.0)\
                         ,'fragmentSize': (1.0/9.0 , 1.0)\
                         ,'gapSize': (1.0/6.0, 1.0)}

    number_of_init_sample = 2

    if not os.path.exists(PATH+'/SICER/control/'):
        os.makedirs(PATH + '/SICER/control/')

    if kry_file is None:
        for label in validation_set + test_set:
            chromosome_list.append(label.split(':')[0])
        chromosome_list = sorted(list(set(chromosome_list)))
        for chromosome in chromosome_list:
            output_dir = PATH + '/SICER/' + chromosome + '/'
            if not os.path.exists(PATH + '/SICER/' + chromosome):
                os.makedirs(output_dir)
    else:
        cpNum_files = glob.glob(PATH + "/" + input_file.split(".")[0] + ".CP[1-9].bam")
        cpNum_controls = glob.glob(PATH + "/" + control.split(".")[0] + ".CP[1-9].bam")
        str_cpnum_list = []
        for cp in cpNum_files:
            str_cpnum_list.append(re.search("CP[1-9]", cp).group(0))
        for str_cpnum in str_cpnum_list:
            output_dir = PATH + '/SICER/' + str_cpnum + '/'
            if not os.path.exists(PATH + '/SICER/' + str_cpnum):
                os.makedirs(output_dir)


    reference_char = ".REF_"
    bam_name = input_file[:-4]
    cr_bam_name = control[:-4]

    MAX_CORE = cpu_count()
    learning_processes = []


    ###############################################################


    if kry_file is None:
        for chromosome in chromosome_list:
            def wrapper_function(windowSize, fragmentSize, gapSize):
                target = PATH + '/' + bam_name + reference_char + chromosome + '.bam'
                cr_target = PATH + '/' + cr_bam_name + reference_char + chromosome + '.bam'
                accuracy = run(target, cr_target, validation_set + test_set \
                               , str(int(windowSize*600.0))\
                               , str(int(fragmentSize*450.0)), str(int(gapSize*6.0)), False, )
                print chromosome, \
                    "windowSize : " + str(int(windowSize*600.0)),\
                    "fragmentSize : " + str(int(fragmentSize*450.0)),\
                    "gapSize : " + str(int(gapSize*6.0)),\
                    "score:" + str(round(accuracy, 4)) + '\n'
                return accuracy

            function = wrapper_function
            learning_process = multiprocessing.Process(target=optimizeHyper, \
                args=(function, parameters_bounds, number_of_init_sample, return_dict, 20, 'ei', chromosome,))

            parallel_learning(MAX_CORE, learning_process, learning_processes)
    else:
        for index in range(len(cpNum_files)):
            cpNum_str = re.search("CP[1-9]", cpNum_files[index]).group(0)
            cpNum = int(cpNum_str[2:3])
            def wrapper_function(windowSize, fragmentSize, gapSize):
                accuracy = run(cpNum_files[index], cpNum_controls[index], validation_set + test_set \
                               , str(int(windowSize*600.0))\
                               , str(int(fragmentSize*450.0)), str(int(gapSize*6.0)), False, kry_file, )
                print cpNum_str, \
                    "windowSize : " + str(int(windowSize*600.0)),\
                    "fragmentSize : " + str(int(fragmentSize*450.0)),\
                    "gapSize : " + str(int(gapSize*6.0)),\
                    "score:" + str(round(accuracy, 4)) + '\n'
                return accuracy
            function = wrapper_function
            learning_process = multiprocessing.Process(target=optimizeHyper,\
                args=(function, parameters_bounds, number_of_init_sample, return_dict, 20, 'ei', cpNum,))

            parallel_learning(MAX_CORE, learning_process, learning_processes)

    for proc in learning_processes:
        proc.join()

    print "finish learning parameter of SICER ! "
    print "Running SICER with learned parameter . . . . . . . . . . . . . . ."

    learning_processes = []

    if kry_file is None:
        for chromosome in chromosome_list:
            parameters = return_dict[chromosome]['max_params']
            target = bam_name + reference_char + chromosome + '.bam'
            windowSize = parameters['windowSize']
            fragmentSize = parameters['fragmentSize']
            gapSize = parameters['gapSize']

            learning_process = multiprocessing.Process(target=run,\
                args=( PATH + '/' + target, PATH + '/' + cr_bam_name + reference_char + chromosome + '.bam'\
                    , validation_set + test_set, str(int(windowSize*600.0)), str(int(fragmentSize*450.0)), str(int(gapSize*6.0)), True,))

            parallel_learning(MAX_CORE, learning_process, learning_processes)

    else:
        for index in range(len(cpNum_files)):
            cpNum_str = re.search("CP[1-9]", cpNum_files[index]).group(0)
            cpNum = int(cpNum_str[2:3])

            parameters = return_dict[cpNum]['max_params']
            windowSize = parameters['windowSize']
            fragmentSize = parameters['fragmentSize']
            gapSize = parameters['gapSize']

            learning_process = multiprocessing.Process(target=run,\
                args=(cpNum_files[index], cpNum_controls[index], validation_set + test_set, str(int(windowSize*600.0)),\
                    str(int(fragmentSize*450.0)), str(int(gapSize*6.0)), True, kry_file,))

            parallel_learning(MAX_CORE, learning_process, learning_processes)

    for proc in learning_processes:
        proc.join()

    return return_dict


def run(input_file, control, valid_set, windowSize='200', fragSize='150', gapSize='3', final=False, kry_file=None):
    """

    :param input_file:
    :param control:
    :param valid_set:
    :param final:
    :param kry_file:

    :return: accuracy rate about a result file.
    """
    result_file = input_file[:-4] + ".bam_peaks.bed"
    result_file = result_file.rsplit('/',1)[0] + '/SICER/' + result_file.rsplit('/',1)[1]

    SICER(input_file, control, windowSize, fragSize, gapSize, kry_file)

    if not valid_set:
        print "there are no matched validation set :p\n"
        exit()
    else:
        if not os.path.exists(result_file):
            return 0, 0
        peaks = loadPeak(result_file)

        if kry_file is None:
            error_num, label_num = calculateError(peaks, parseLabel(valid_set, result_file))
        else:
            error_num, label_num = 0, 0

            peaks_by_chr = []
            containor = []
            for index in range(len(peaks)):
                if not (index+1 == len(peaks)):
                    if peaks[index]['chr'] != peaks[index+1]['chr']:
                        containor.append(peaks[index])
                        peaks_by_chr.append(containor)
                        containor = []
                    else:
                        containor.append(peaks[index])
                else:
                    peaks_by_chr.append(containor)

            for peak_by_chr in peaks_by_chr:
                if len(peak_by_chr) > 0:
                    chromosome = peak_by_chr[0]['chr']
                    temp_error, temp_label = calculateError(peak_by_chr, \
                        parseLabel(valid_set, result_file, input_chromosome=chromosome, cpNum_file_name=kry_file))
                    error_num += temp_error
                    label_num += temp_label

        if os.path.isfile(result_file) and (not final):
            os.remove(result_file)
        elif final:
            print result_file + " is stored."
        else:
            print "there is no result file.."

    if label_num is 0:
        return 0.0

    if final:
        print "Test Score ::" + str(1 - error_num / label_num)

    return (1 - error_num / label_num)


def parallel_learning(MAX_CORE, learning_process, learning_processes):
    """

    :param MAX_CORE:
    :param learning_process:
    :param learning_processes:
    :return:
    """
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
