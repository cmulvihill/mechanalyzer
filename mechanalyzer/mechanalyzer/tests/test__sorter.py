""" test mechanalyzer.parser.sort for different mechanisms in 'data/'
    using different sorting options
"""
import sys
import os
import tempfile
import numpy as np
from automol.util.dict_ import filter_keys
from chemkin_io.writer.mechanism import write_chemkin_file
from mechanalyzer.builder import sorter
from mechanalyzer.parser import mech as mparser
from mechanalyzer.parser import spc as sparser
from ioformat import pathtools


# Set Paths to test/data directory and output directory
CWD = os.path.dirname(os.path.realpath(__file__))
TMP_OUT = tempfile.mkdtemp()

# Set types for parsing mechanisms
SPC_TYPE = 'csv'
MECH_TYPE = 'chemkin'

# Test data
BIG_ARRAY = np.array([1e15, 1e15, 1e15])
MIDDLE_ARRAY = np.array([1e14, 1e14, 1e14])
LITTLE_ARRAY = np.array([1e13, 1e13, 1e13])

AL_KTP_DCT = {
    (('H2', 'O'), ('OH', 'H'), (None,)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([0.157572885e+134, 2.79926202e+143, 1.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([6.57572885e+134, 8.79926202e+143, 4.72670689e+149]))},
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))}],
    (('H', 'O2'), ('OH', 'O'), (None,)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))},
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([4.6548277231154764e+45,
                      8.556998184634325e+52, 4.662500917095324e+56])),
         1: (np.array([500, 1000, 1500]),
             np.array([4.6548277231154764e+45,
                       8.556998184634325e+52, 4.662500917095324e+56])),
         10: (np.array([500, 1000, 1500]),
              np.array([4.6548277231154764e+45,
                        8.556998184634325e+52, 4.662500917095324e+56]))}],
    (('H2', 'O'), ('OH', 'OH'), (None,)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))},
        None],
    (('H', 'O'), ('OH',), (None,)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))},
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([1.420849319576619e+96,
                      2.8405686431169553e+77, 3.4922934313599517e+72])),
         1: (np.array([500, 1000, 1500]),
             np.array([5.8295576381190475e+100,
                       2.3308958102634265e+82, 4.2985260083885116e+77])),
         10: (np.array([500, 1000, 1500]),
              np.array([2.3917907260059445e+105,
                        1.912671707993609e+87, 5.2908858341829314e+82]))}],
    (('H', 'O'), ('OH',), ('(+M)',)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))},
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([9.813202359645695e+109,
                      1.569488025355258e+92, 6.512342336821681e+87])),
         1: (np.array([500, 1000, 1500]),
             np.array([4.0262276922599165e+114,
                       1.2878805345625882e+97, 8.015784887656628e+92])),
         10: (np.array([500, 1000, 1500]),
              np.array([1.6519081983453455e+119,
                        1.0568008449314422e+102, 9.866312924289953e+97]))}],
    (('H2', 'O(S)'), ('OH', 'H'), (None,)): [
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139]))},
        {'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139])),
         1: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139])),
         10: (np.array([500, 1000, 1500]),
              np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+139]))}],
    (('H2', 'O2'), ('HO2V', 'H'), (None,)): [None, {
        'high': (
            np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
        1: (np.array([500, 1000, 1500]),
            np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149])),
        10: (np.array([500, 1000, 1500]),
             np.array([3.57572885e+134, 4.79926202e+143, 2.72670689e+149]))}]}


def test__sort_with_input():
    """ sort by using the auxlilary input files to specify parameters
    """
    # use data/LLNL_species.csv, data/LLNL_mech.dat, data/sort.dat
    try:
        spc_name = os.path.join(CWD, sys.argv[1])
        mech_name = os.path.join(CWD, sys.argv[2])
        sort_inp = os.path.join(CWD, sys.argv[3])
    except IndexError:
        print('*ERROR: input files missing - put species, mechanism, and sort.dat files')
        sys.exit()

    sort_str = pathtools.read_file(CWD, sort_inp, remove_comments='#')
    isolate_species, sort_list = mparser.read_sort_section(sort_str)
    sortmech_name = os.path.join(TMP_OUT, 'sorted_mech.txt')
    print(sortmech_name)
    mech_rest_name = os.path.join(TMP_OUT, 'rest_mech.txt')
    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_list)


def test__readwrite_thirdbody():
    """ test mechanalyzer.parser.sort

        Checks read/write of a small set of rxns involving third bodies
    """

    spc_name = os.path.join(CWD, 'data', 'NUIG_species.csv')
    mech_name = os.path.join(CWD, 'data', 'NUIG_mechred.dat')
    mech_rest_name = os.path.join(TMP_OUT, 'NUIG_mech_rest.txt')
    sortmech_name = os.path.join(
        TMP_OUT, 'NUIG_test_readwrite_thirdbody.txt')
    isolate_species = []
    sort_str = ['pes', 0]  # ARRANGE BY PES- NO HEADERS INCLUDED

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_mult():
    """ test mechanalyzer.parser.sort

        Sort by multiplicity of the reaction
    """

    spc_name = os.path.join(CWD, 'data', 'C10H10_species.csv')
    mech_name = os.path.join(CWD, 'data', 'C10H10_HP_mech.dat')
    mech_rest_name = os.path.join(TMP_OUT, 'C10H10_mech_rest.txt')
    sortmech_name = os.path.join(TMP_OUT, 'C10H10_test_sortby_mult.txt')
    isolate_species = []
    sort_str = ['mult', 0]  # NO HEADERS INCLUDED
    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_molec_r1():
    """ test mechanalyzer.parser.sort

        Sort by first (heavier) reactant and molecularity of the reaction
    """

    spc_name = os.path.join(CWD, 'data', 'C10H10_species.csv')
    mech_name = os.path.join(CWD, 'data', 'C10H10_HP_mech.dat')
    mech_rest_name = os.path.join(TMP_OUT, 'C10H10_mech_rest.txt')
    sortmech_name = os.path.join(
        TMP_OUT, 'C10H10_test_sortby_molec_R1.txt')
    isolate_species = []
    sort_str = ['r1', 'molecularity', 0]  # NO HEADERS INCLUDED
    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_rxnclass():
    """ test mechanalyzer.parser.sort

        sort by reaction class:
            both "broad" (based on multiplicity, reactants/products..)
        and "graph" (based on graph classification - warning, CPU intensive)
        prior to rxn class, the mech is also subdivided into PESs
    """

    spc_name = os.path.join(CWD, 'data', 'LLNL_species.csv')
    mech_name = os.path.join(CWD, 'data', 'LLNL_IC8_red_classes.dat')
    mech_rest_name = os.path.join(TMP_OUT, 'IC8_class_rest.txt')
    sortmech_name = os.path.join(
        TMP_OUT, 'IC8_test_sortby_rxnclass.txt')
    isolate_species = []
    print(sortmech_name)
    # HEADER INDICATING THE REACTION CLASS
    sort_str = ['pes', 'rxn_class_broad', 'rxn_class_graph', 1]

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_species_subpes():
    """ test mechanalyzer.parser.sort

        Select a species subset from a mechanism and
        extract all reactions they are involved to
        Within the reaction subset, classify according
        to subpes (or potentially any other criteria)
    """

    spc_name = os.path.join(CWD, 'data', 'LLNL_species.csv')
    mech_name = os.path.join(CWD, 'data', 'LLNL_mech.dat')
    mech_rest_name = os.path.join(
        TMP_OUT, 'LLNL_IC8_SPECIES_mech_rest.txt')
    sortmech_name = os.path.join(
        TMP_OUT, 'LLNL_test_sortby_species_subpes_IC8.txt')
    isolate_species = ['IC8', 'IC8-1R', 'IC8-3R', 'IC8-4R', 'IC8-5R']
    sort_str = ['species', 'subpes', 1]  # HEADER INDICATING THE SPECIES SUBSET

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)

    # NOW ORDER JUST BY SUBPES
    sortmech_name = os.path.join(
        TMP_OUT, 'LLNL_test_sortby_subpes_IC8.txt')
    sort_str = ['subpes', 0]  # NO HEADER
    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_submech():
    """ test mechanalyzer.parser.sort

        sort by fuel submechanism: extract reactions of
        fuel, fuel radicals, R+O2, R+O4
        then order by subpes
    """

    spc_name = os.path.join(CWD, 'data', 'LLNL_species.csv')
    mech_name = os.path.join(CWD, 'data', 'LLNL_mech.dat')
    mech_rest_name = os.path.join(
        TMP_OUT, 'LLNL_IC8_submech_mech_rest.txt')

    sortmech_name = os.path.join(
        TMP_OUT, 'LLNL_test_sortby_submech_IC8.txt')
    isolate_species = ['IC8']
    sort_str = ['submech', 1]  # HEADER INDICATING THE SPECIES SUBSET

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)

    # NOW ORDER JUST BY SUBPES
    sortmech_name = os.path.join(
        TMP_OUT, 'LLNL_test_sortby_submech_subpes_broadclass_IC8.txt')
    # NO HEADER
    sort_str = ['submech', 'subpes', 'rxn_class_broad', 1]

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sortby_submech_class():
    """ test mechanalyzer.parser.sort

        sort by fuel submechanism: extract reactions of
        fuel, fuel radicals, R+O2, R+O4
        then order by subpes
    """

    spc_name = os.path.join(CWD, 'data', 'LLNL_species.csv')
    mech_name = os.path.join(CWD, 'data', 'LLNL_IC8_red_mech.dat')
    mech_rest_name = os.path.join(
        TMP_OUT, 'LLNL_IC8_submech_class_mech_rest.txt')

    sortmech_name = os.path.join(
        TMP_OUT, 'LLNL_test_sortby_submech_class_IC8.txt')
    isolate_species = ['IC8', 'submech']
    # NO HEADER
    sort_str = ['submech', 'rxn_class_broad', 'rxn_class_graph', 1]

    sorter._sort_main(spc_name, mech_name, sortmech_name,
                      mech_rest_name, isolate_species, sort_str)


def test__sort_ktp():
    """ test mechanalyzer.parser.sort

        sort ktp dictionary according to highest rate values/ratios
    """
    # al_ktp_dct_sorted = mechparser.reordered_mech(AL_KTP_DCT, sortd_idx)
    # MODIFY THIS SECTION WITH INPUT NAMES AND SORTING OPTIONS

    spc_names = ['data/spc2.csv', 'data/spc1B.csv']
    # mech_names = ['data/mech2.txt', 'data/mech1.txt']
    # if you want sorted rxn param dct: also read mechs
    isolate_species = []
    sort_str = ['molecularity', 'rxn_max_vals',
                'rxn_max_ratio', 'rxn_class_broad', 0]

    ############ input reading ####################

    # READ FILE# READ FILE AND BUILD DICTIONARIES
    with open(spc_names[1], 'r') as spc_obj:
        spc_str = spc_obj.read()

    # Build mech information
    spc_dct_full = sparser.build_spc_dct(spc_str, SPC_TYPE)

    # BUILD  MECH INFORMATION
    mech_info = mparser._mech_info(AL_KTP_DCT, spc_dct_full)

    # SORTING: sort the mech and build the sorted rxn param dct
    srt_mch = mparser.sorting(
        mech_info, spc_dct_full, sort_str, isolate_species)

    sorted_idx, _, _ = mparser.sorted_mech(srt_mch)
    al_ktp_dct_sorted = mparser.reordered_mech(AL_KTP_DCT, sorted_idx)

    print(al_ktp_dct_sorted)


def test__build_sorted_pesdct():
    """
    sort by subpes for a subset of species and get the corresponding subpes dictionaries
    """

    spc_name = os.path.join(CWD, 'data', 'LLNL_species.csv')
    mech_name = os.path.join(CWD, 'data', 'LLNL_mech.dat')
    isolate_species = ['IC8', 'IC8-1R', 'IC8-3R', 'IC8-4R', 'IC8-5R']
    sort_str = ['subpes', 0]  # HEADER INDICATING THE SPECIES SUBSET
    pes_dct = sorter._sort_pes(spc_name, mech_name, isolate_species, sort_str)

    print(pes_dct)


if __name__ == '__main__':
    # test__sortby_species_subpes()
    # test__sortby_submech()
    # test__sortby_mult()
    # test__sortby_molec_r1()
    # test__sortby_rxnclass()
    # test__sortby_submech_class()
    # test__sort_ktp()
    test__sort_with_input()
    # test__build_sorted_pesdct()
    # test__readwrite_thirdbody()
