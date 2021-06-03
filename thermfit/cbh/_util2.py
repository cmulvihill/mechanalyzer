""" Computes the Heat of Formation at 0 K for a given species
"""

import os
import numpy as np
import automol.inchi
import automol.graph
import automol.formula
# from mechlib.amech_io import printer as ioprinter
from thermfit import _util as util


# Path  the database files (stored in the thermo src directory)
SRC_PATH = os.path.dirname(os.path.realpath(__file__))


def remove_hyd_from_adj_atms(atms, adj_atms, othersite=(), other_adj=()):
    """ Removes H atoms from all atms adjacent to a set of atoms requested
        by the user
    """

    new_adj_atms = ()
    for atm in adj_atms:
        if atms[atm][0] != 'H' and atm not in othersite:
            if atm not in other_adj:
                new_adj_atms += (atm,)

    return new_adj_atms


def branchpoint(adj_atms_i, adj_atms_j=(), adj_atms_k=()):
    """ Branch point?
    """
    return max(1, len(adj_atms_i) + len(adj_atms_j) + len(adj_atms_k) - 1)


def terminalmoity(adj_atms_i, adj_atms_j=(), adj_atms_k=(), endisterm=True):
    """ Get moiety of termial groups?
    """

    ret = 1
    if len(adj_atms_i) + len(adj_atms_j) < 2:
        ret = 0
    if ret == 0 and len(adj_atms_k) > 0 and not endisterm:
        ret = 1

    return ret


def _ts_graph(gra, site1, site2=None):
    """ Get a transition state graph.
    """

    rad_atms = list(automol.graph.sing_res_dom_radical_atom_keys(gra))
    atm_vals = automol.graph.atom_element_valences(gra)
    atms = automol.graph.atoms(gra)
    bnd_ords = automol.graph.one_resonance_dominant_bond_orders(gra)
    adj_atms = automol.graph.atoms_neighbor_atom_keys(gra)

    sites = [site1]
    if site2:
        sites.append(site2)
    for site in sites:
        frm = [site[0], site[1]]
        brk = [site[1], site[2]]
        frm.sort()
        brk.sort()
        # update adjacent atms list to consider TS connected
        if site[1] in adj_atms[site[0]]:
            if site[1] in adj_atms[site[2]]:
                if site[1] in rad_atms:
                    new_bnd_ords = bnd_ords.copy()
                    bnd_dic = {}
                    for key in bnd_ords:
                        bnd_dic[key] = (list(new_bnd_ords[key])[0], None)
                    new_gra = (atms, bnd_dic)
                    new_rad_atms = list(
                        automol.graph.sing_res_dom_radical_atom_keys(new_gra))
                    if site[1] not in new_rad_atms:
                        rad_atms.remove(site[1])
                bnd_ords[frozenset({*frm})] = frozenset(
                    {list(bnd_ords[frozenset({*frm})])[0] + 0.6})
                bnd_ords[frozenset({*brk})] = frozenset(
                    {list(bnd_ords[frozenset({*brk})])[0] - 0.6})
            else:
                if site[2] in rad_atms:
                    new_bnd_ords = bnd_ords.copy()
                    new_bnd_ords[frozenset({*frm})] = frozenset(
                        {list(bnd_ords[frozenset({*frm})])[0] - 1})
                    new_bnd_ords[frozenset({*brk})] = frozenset({1})
                    bnd_dic = {}
                    for key in bnd_ords:
                        bnd_dic[key] = (list(new_bnd_ords[key])[0], None)
                    new_gra = (atms, bnd_dic)
                    new_rad_atms = list(
                        automol.graph.sing_res_dom_radical_atom_keys(new_gra))
                    if site[2] not in new_rad_atms:
                        rad_atms.remove(site[2])
                bnd_ords[frozenset({*frm})] = frozenset(
                    {list(bnd_ords[frozenset({*frm})])[0] - 0.4})
                bnd_ords[frozenset({*brk})] = frozenset({0.4})
                adj_atms[site[2]] = frozenset({site[1], *adj_atms[site[2]]})
                adj_atms[site[1]] = frozenset({site[2], *adj_atms[site[1]]})
        else:
            if site[0] in rad_atms:
                new_bnd_ords = bnd_ords.copy()
                new_bnd_ords[frozenset({*brk})] = frozenset(
                    {list(bnd_ords[frozenset({*brk})])[0] - 1})
                new_bnd_ords[frozenset({*frm})] = frozenset({1})
                bnd_dic = {}
                for key in bnd_ords:
                    bnd_dic[key] = (list(new_bnd_ords[key])[0], None)
                new_gra = (atms, bnd_dic)
                new_rad_atms = list(
                    automol.graph.sing_res_dom_radical_atom_keys(new_gra))
                if site[0] not in new_rad_atms:
                    rad_atms.remove(site[0])
            bnd_ords[frozenset({*frm})] = frozenset({0.6})
            bnd_ords[frozenset({*brk})] = frozenset(
                {list(bnd_ords[frozenset({*brk})])[0] - 0.6})
            adj_atms[site[0]] = frozenset({site[1], *adj_atms[site[0]]})
            adj_atms[site[1]] = frozenset({site[0], *adj_atms[site[1]]})

    return rad_atms, atms, bnd_ords, atm_vals, adj_atms


def remove_zero_order_bnds(gra):
    """ Remove bonds of zero-order from a molecular graph.
    """

    atms, bnds = gra
    new_bnds = {}
    for bnd in bnds:
        if bnds[bnd][0] > 0:
            new_bnds[bnd] = bnds[bnd]

    return (atms, new_bnds)


def split_beta_gras(gras):
    """ ?
    """

    rct_ichs = ['']
    prd_ichs = ['', '']
    atms, bnd_ords = gras
    atms = atms.copy()
    bnd_ords = bnd_ords.copy()
    # ioprinter.debug_message('rct gra at start', atms, bnd_ords)
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order + 0.6, 1), tmp)
            atmai, atmbi = bnd_ord
            if not abs(np.floor(atms[atmai][1]) - (atms[atmai][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atma[1] = round(atma[1] - 0.6, 1)
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if abs(np.floor(atms[atmi][1]) - (atms[atmi][1]-0.4)) < .01:
                    atm = list(atms[atmi])
                    atm[1] = round(atm[1] - 0.4, 1)
                    atms[atmi] = tuple(atm)
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    bnd_ords[frozenset({atmbi, atmi})] = (round(
                        order - 0.6, 1), tmp)
            rct_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = rct_gra
    rct_gras = automol.graph.connected_components(rct_gra)
    for idx, rgra in enumerate(rct_gras):
        if rgra:
            rct_ichs[idx] = automol.graph.inchi(rgra)
    rct_ichs = automol.inchi.sorted_(rct_ichs)
    atms, bnd_ords = gras
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order - 0.4, 1), tmp)
            atmai, atmbi = bnd_ord
            if not abs(np.floor(atms[atmai][1]) - (atms[atmai][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atma[1] = round(atma[1] - 0.6, 1)
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if abs(np.floor(atms[atmi][1]) - (atms[atmi][1]-0.4)) < 0.01:
                    atm = list(atms[atmi])
                    atm[1] = round(atm[1] - 0.4, 1)
                    atms[atmi] = tuple(atm)
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    bnd_ords[frozenset({atmbi, atmi})] = (round(
                        order + 0.4, 1), tmp)
            prd_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = prd_gra
    prd_gras = automol.graph.connected_components(prd_gra)
    for idx, pgra in enumerate(prd_gras):
        prd_ichs[idx] = automol.graph.inchi(pgra)
    prd_ichs = automol.inchi.sorted_(prd_ichs)

    return (rct_ichs, prd_ichs)


def split_radradabs_gras(gras):
    """ Split a graph from radical-radical abstraction TS into the constituent
        reactant/products graphs.
    """

    rct_ichs = []
    prd_ichs = []
    atms, bnd_ords = gras
    atms = atms.copy()
    bnd_ords = bnd_ords.copy()
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order + 0.6, 1), tmp)
            atmai, atmbi = bnd_ord
            if abs(np.floor(atms[atmbi][1]) - (atms[atmbi][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atmb[1] = np.floor(atmb[1])
            atma[1] = np.floor(atma[1])
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if frozenset({atmi, atmbi}) in bnd_ords and atmi != atmai:
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        bnd_ords[frozenset({atmbi, atmi})] = (round(
                            order - 0.6, 1), tmp)
                if frozenset({atmi, atmai}) in bnd_ords and atmi != atmbi:
                    order, tmp = bnd_ords[frozenset({atmai, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        bnd_ords[frozenset({atmai, atmi})] = (round(
                            order - 0.6, 1), tmp)
            rct_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = rct_gra
    rct_gras = automol.graph.connected_components(rct_gra)
    for rgra in rct_gras:
        rct_ichs.append(automol.graph.inchi(rgra))
    if len(rct_ichs) > 1:
        rct_ichs = automol.inchi.sorted_(rct_ichs)
    atms, bnd_ords = gras
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order - 0.4, 1), tmp)
            atmai, atmbi = bnd_ord
            if abs(np.floor(atms[atmbi][1]) - (atms[atmbi][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atmb[1] = np.floor(atmb[1])
            atma[1] = np.floor(atma[1])
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if frozenset({atmi, atmbi}) in bnd_ords and atmi != atmai:
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        atms[atmi] = tuple(atm)
                        order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                        bnd_ords[frozenset({atmbi, atmi})] = (round(
                            order + 0.4, 1), tmp)
                if frozenset({atmi, atmai}) in bnd_ords and atmi != atmbi:
                    order, tmp = bnd_ords[frozenset({atmai, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        order, tmp = bnd_ords[frozenset({atmai, atmi})]
            prd_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = prd_gra
    prd_gras = automol.graph.connected_components(prd_gra)
    for pgra in prd_gras:
        prd_ichs.append(automol.graph.inchi(pgra))
    if len(prd_ichs) > 1:
        prd_ichs = automol.inchi.sorted_(prd_ichs)
    return (rct_ichs, prd_ichs)


def split_elim_gras(gras):
    """ Split a graph from elimination TS into the constituent
        reactant/products graphs.
    """

    rct_ichs = []
    prd_ichs = []
    atms, bnd_ords = gras
    atms = atms.copy()
    bnd_ords = bnd_ords.copy()
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order + 0.6, 1), tmp)
            atmai, atmbi = bnd_ord
            if abs(np.floor(atms[atmbi][1]) - (atms[atmbi][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atmb[1] = np.floor(atmb[1])
            atma[1] = np.floor(atma[1])
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if frozenset({atmi, atmbi}) in bnd_ords and atmi != atmai:
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        bnd_ords[frozenset({atmbi, atmi})] = (round(
                            order - 0.6, 1), tmp)
            rct_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = rct_gra
    rct_gras = automol.graph.connected_components(rct_gra)
    for rgra in rct_gras:
        rct_ichs.append(automol.graph.inchi(rgra))
    if len(rct_ichs) > 1:
        rct_ichs = automol.inchi.sorted_(rct_ichs)
    atms, bnd_ords = gras
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order - 0.4, 1), tmp)
            atmai, atmbi = bnd_ord
            if abs(np.floor(atms[atmbi][1]) - (atms[atmbi][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atmb[1] = np.floor(atmb[1])
            atma[1] = np.floor(atma[1])
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if frozenset({atmi, atmbi}) in bnd_ords and atmi != atmai:
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = np.floor(atm[1])
                        atms[atmi] = tuple(atm)
                        order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                        bnd_ords[frozenset({atmbi, atmi})] = (round(
                            order + 0.4, 1), tmp)
            # ioprinter.info_message(atms, bnd_ords)
            prd_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = prd_gra
    prd_gras = automol.graph.connected_components(prd_gra)
    for pgra in prd_gras:
        prd_ichs.append(automol.graph.inchi(pgra))
    if len(prd_ichs) > 1:
        prd_ichs = automol.inchi.sorted_(prd_ichs)
    return (rct_ichs, prd_ichs)


def split_gras(gras):
    """ Split graphs by ???
    """

    rct_ichs = []
    prd_ichs = []
    atms, bnd_ords = gras
    atms = atms.copy()
    bnd_ords = bnd_ords.copy()
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order + 0.6, 1), tmp)
            atmai, atmbi = bnd_ord
            if not abs(np.floor(atms[atmai][1]) - (atms[atmai][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atma[1] = round(atma[1] - 0.6, 1)
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if abs(np.floor(atms[atmi][1]) - (atms[atmi][1]-0.4)) < 0.01:
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    if abs(np.floor(order) - (order - 0.6)) < 0.01:
                        atm = list(atms[atmi])
                        atm[1] = round(atm[1] - 0.4, 1)
                        atms[atmi] = tuple(atm)
                        bnd_ords[frozenset({atmbi, atmi})] = (round(
                            order - 0.6, 1), tmp)
            rct_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = rct_gra
    rct_gras = automol.graph.connected_components(rct_gra)
    for rgra in rct_gras:
        rct_ichs.append(automol.graph.inchi(rgra))
    if len(rct_ichs) > 1:
        rct_ichs = automol.inchi.sorted_(rct_ichs)
    atms, bnd_ords = gras
    for bnd_ord in bnd_ords:
        order, tmp = bnd_ords[bnd_ord]
        if abs(np.floor(order) - (order - 0.4)) < 0.01:
            bnd_ords[bnd_ord] = (round(order - 0.4, 1), tmp)
            atmai, atmbi = bnd_ord
            if not abs(np.floor(atms[atmai][1]) - (atms[atmai][1]-0.6)) < 0.01:
                atmbi, atmai = atmai, atmbi
            atma = list(atms[atmai])
            atmb = list(atms[atmbi])
            atma[1] = round(atma[1] - 0.6, 1)
            atms[atmai] = tuple(atma)
            atms[atmbi] = tuple(atmb)
            for atmi in atms:
                if abs(np.floor(atms[atmi][1]) - (atms[atmi][1]-0.4)) < 0.01:
                    atm = list(atms[atmi])
                    atm[1] = round(atm[1] - 0.4, 1)
                    atms[atmi] = tuple(atm)
                    atms[atmi] = tuple(atm)
                    order, tmp = bnd_ords[frozenset({atmbi, atmi})]
                    bnd_ords[frozenset({atmbi, atmi})] = (round(
                        order + 0.4, 1), tmp)
            prd_gra = remove_zero_order_bnds((atms, bnd_ords))
            atms, bnd_ords = rct_gra
    prd_gras = automol.graph.connected_components(prd_gra)
    for pgra in prd_gras:
        prd_ichs.append(automol.graph.inchi(pgra))
    if len(prd_ichs) > 1:
        prd_ichs = automol.inchi.sorted_(prd_ichs)

    return (rct_ichs, prd_ichs)


def _simplify_gra_frags(frags):
    """ ?
    """

    new_frags = {}
    for i, frag in enumerate(frags.keys()):
        if abs(frags[frag]['coeff']) > 0.01:
            new_frags[i] = frags[frag]

    return new_frags


def _intersec(lst1, lst2):
    ret = None
    for atm in lst1:
        if atm in lst2:
            ret = atm
    assert ret is not None, (
        'brk_key {} and frm_key {} do not intersect'.format(lst1, lst2))
    return ret


def _xor(lst1, lst2):
    ret = None
    for atm in lst1:
        if atm not in lst2:
            ret = atm
    assert ret is not None, (
        'problem with bond_key {}'.format(lst1))
    return ret


def _remove_dummies(zma, frm_key, brk_key, geo=None):
    """get zma and bond key idxs without dummy atoms
    """
    zgeo = automol.zmat.geometry(zma)
    brk_key2 = None
    if isinstance(brk_key, list):
        brk_key, brk_key2 = brk_key
    dummy_idxs = automol.geom.dummy_atom_indices(zgeo)
    for idx in dummy_idxs:
        if frm_key:
            frm1, frm2 = frm_key
            if idx < frm1:
                frm1 -= 1
            if idx < frm2:
                frm2 -= 1
            frm_key = frozenset({frm1, frm2})
        if brk_key:
            brk1, brk2 = brk_key
            if idx < brk1:
                brk1 -= 1
            if idx < brk2:
                brk2 -= 1
            brk_key = frozenset({brk1, brk2})
        if brk_key2:
            brk3, brk4 = brk_key2
            if idx < brk3:
                brk3 -= 1
            if idx < brk4:
                brk4 -= 1
            brk_key2 = frozenset({brk3, brk4})
    if not geo:
        geo = automol.geom.without_dummy_atoms(zgeo)
    gra = automol.geom.graph(geo)
    return gra, frm_key, brk_key, brk_key2


def _remove_frm_bnd(gra, brk_key, frm_key):
    bond_keys = automol.graph.bond_keys(gra)
    if brk_key and brk_key not in bond_keys:
        gra = automol.graph.add_bonds(gra, [brk_key])
    if frm_key and frm_key in bond_keys:
        gra = automol.graph.remove_bonds(gra, [frm_key])
    return gra


def _add_appropriate_pi_bonds(gra):
    adj_atms = automol.graph.atoms_neighbor_atom_keys(gra)
    unsat_atms_dct = automol.graph.atom_unsaturated_valences(gra)
    atms, bnd_ords = gra
    brk_key = frozenset({})
    unsat_atms = []
    for atm in unsat_atms_dct:
        if unsat_atms_dct[atm] > 0:
            unsat_atms.append(atm)
    for atmi in unsat_atms:
        for atmj in unsat_atms:
            if atmi > atmj:
                if atmi in adj_atms[atmj]:
                    key = [atmi, atmj]
                    key.sort()
                    key = frozenset(key)
                    brk_key = key
                    bnd, tmp = bnd_ords[key]
                    bnd_ords[key] = (bnd + 1, tmp)

    return (atms, bnd_ords), brk_key


def _elimination_second_forming_bond(gra, brk_key1, brk_key2):
    frm_bnd2 = frozenset({})
    adj_atms = automol.graph.atoms_neighbor_atom_keys(gra)
    for atm1 in brk_key1:
        for atm2 in brk_key2:
            if atm2 in adj_atms[atm1]:
                frm_bnd2 = [atm1, atm2]
                frm_bnd2.sort()
                frm_bnd2 = frozenset(frm_bnd2)
    return frm_bnd2


def _ring_forming_forming_bond(gra, brk_key):
    """ Add in missing forming bond for ring forming scission reactions
    """
    frm_key = frozenset({})
    adj_atms = automol.graph.atoms_neighbor_atom_keys(gra)
    rad_atms = list(automol.graph.sing_res_dom_radical_atom_keys(gra))
    form_atm1 = rad_atms[0]
    for break_atm in brk_key:
        if adj_atms[break_atm] > 1:
            form_atm2 = break_atm
            frm_key = frozenset({form_atm1, form_atm2})
    return frm_key


def _elimination_find_brk_bnds(gra, frm_key):
    brk_key1 = frozenset({})
    brk_key2 = frozenset({})
    adj_atms = automol.graph.atoms_neighbor_atom_keys(gra)
    atms, _ = gra
    atm1, atm2 = frm_key
    atm3, atm4 = list(adj_atms[atm1])[0], list(adj_atms[atm2])[0]
    if atms[atm1][0] == 'H':
        brk_key1 = [atm1, atm3]
    elif atms[atm1][0] == 'O':
        for atm5 in adj_atms[atm3]:
            if atm5 != atm1:
                brk_key1 = [atm3, atm5]
    if atms[atm2][0] == 'H':
        brk_key2 = [atm2, atm4]
    elif atms[atm2][0] == 'O':
        for atm6 in adj_atms[atm4]:
            if atm6 != atm2:
                brk_key2 = [atm4, atm6]
    brk_key1.sort()
    brk_key2.sort()

    return frozenset(brk_key1), frozenset(brk_key2)


def _split_bnd_keys(bnd_keys):
    bnd_key1 = None
    bnd_key2 = None
    bnd_keys = list(bnd_keys)
    if len(bnd_keys) > 0:
        bnd_key1 = bnd_keys[0]
        if len(bnd_keys) > 1:
            bnd_key2 = bnd_keys[1]
    return bnd_key1, bnd_key2


def _add2dic(dic, key, val=1):
    """ helper function to add a key to dct
    """
    if key in dic:
        dic[key] += val
    else:
        dic[key] = val


def _lhs_rhs(frags):
    """ Determine the left-hand side and right-hand side of reaction
    """
    rhs = {}
    lhs = {}
    for frag in frags:
        if frags[frag] > 0:
            rhs[frag] = frags[frag]
        elif frags[frag] < 0:
            lhs[frag] = - frags[frag]
    return lhs, rhs


def print_lhs_rhs(ich, frags):
    """ print the fragments from each side of the reaction
    """
    lhs, rhs = _lhs_rhs(frags)
    lhsprint = automol.inchi.smiles(ich)
    rhsprint = ''
    for frag in rhs:
        if rhsprint:
            rhsprint += ' +  {:.1f} {} '.format(
                rhs[frag], automol.inchi.smiles(frag))
        else:
            rhsprint = ' {:.1f} {} '.format(
                rhs[frag], automol.inchi.smiles(frag))
    for frag in lhs:
        lhsprint += ' +  {:.1f} {} '.format(
            lhs[frag], automol.inchi.smiles(frag))
    return '{} --> {}'.format(lhsprint, rhsprint)


def _balance(ich, frags):
    """ balance the equation?
    """
    stoichs = {}
    for frag in frags:
        _stoich = util.stoich(frag)
        for atm in _stoich:
            if atm in stoichs:
                stoichs[atm] += _stoich[atm] * frags[frag]
            else:
                stoichs[atm] = _stoich[atm] * frags[frag]
    balance_ = {}
    _stoich = util.stoich(ich)
    for atom in _stoich:
        if atom in stoichs:
            balance_[atom] = _stoich[atom] - stoichs[atom]
        else:
            balance_[atom] = _stoich[atom]
    balance_ = {x: y for x, y in balance_.items() if y != 0}
    return balance_


def _balance_ts(gra, frags):
    """ balance the equation using graphs
    """
    stoichs = {}
    for frag in frags:
        if 'exp_gra' in frags[frag]:
            _stoich = automol.graph.formula(frags[frag]['exp_gra'])
        elif 'ts_gra' in frags[frag]:
            _stoich = util.stoich_gra(frags[frag]['ts_gra'])
        for atm in _stoich:
            if atm in stoichs:
                stoichs[atm] += _stoich[atm] * frags[frag]['coeff']
            else:
                stoichs[atm] = _stoich[atm] * frags[frag]['coeff']
    balance_ = {}
    _stoich = util.stoich_gra(gra)
    for atom in _stoich:
        if atom in stoichs:
            balance_[atom] = _stoich[atom] - stoichs[atom]
        else:
            balance_[atom] = _stoich[atom]
    balance_ = {x: y for x, y in balance_.items() if y != 0}
    return balance_


def _balance_frags(ich, frags):
    """ balance the equation?
    """
    balance_ = _balance(ich, frags)
    methane = automol.smiles.inchi('C')
    water = automol.smiles.inchi('O')
    ammonm = automol.smiles.inchi('N')
    hydrgn = automol.smiles.inchi('[H][H]')
    if 'C' in balance_:
        _add2dic(frags, methane, balance_['C'])
    if 'N' in balance_:
        _add2dic(frags, ammonm, balance_['N'])
    if 'O' in balance_:
        _add2dic(frags, water, balance_['O'])
    balance_ = _balance(ich, frags)
    if 'H' in balance_:
        _add2dic(frags, hydrgn, balance_['H']/2)
    return frags


def _balance_frags_ts(gra, frags):
    """ balance the equation?
    """
    balance_ = _balance_ts(gra, frags)
    methane = automol.smiles.inchi('C')
    water = automol.smiles.inchi('O')
    ammonm = automol.smiles.inchi('N')
    hydrgn = automol.smiles.inchi('[H][H]')
    methane = automol.inchi.graph(methane)
    water = automol.inchi.graph(water)
    ammonm = automol.inchi.graph(ammonm)
    hydrgn = automol.inchi.graph(hydrgn)
    idx_dct = []
    for spc in [methane, water, ammonm, hydrgn]:
        spc = automol.graph.explicit(spc)
        found = False
        for frag in frags:
            if 'exp_gra' in frags[frag]:
                if automol.graph.full_isomorphism(frags[frag]['exp_gra'], spc):
                    idx = frag
                    found = True
                    break
        if not found:
            idx = len(frags.keys())
            frags[idx] = {}
            frags[idx]['exp_gra'] = spc
            frags[idx]['coeff'] = 0.0
        idx_dct.append(idx)
    if 'C' in balance_:
        _add2dic(frags[idx_dct[0]], 'coeff', balance_['C'])
    if 'N' in balance_:
        _add2dic(frags[idx_dct[1]], 'coeff', balance_['N'])
    if 'O' in balance_:
        _add2dic(frags[idx_dct[2]], 'coeff', balance_['O'])
    balance_ = _balance_ts(gra, frags)
    if 'H' in balance_:
        _add2dic(frags[idx_dct[3]], 'coeff', balance_['H']/2)
    return frags
