from torchmd.forcefields.forcefield import ForceField
from math import radians
import numpy as np
import yaml


class YamlForcefield(ForceField):
    def __init__(self, mol, prm):
        self.mol = mol
        self.prm = yaml.load(open(prm), Loader=yaml.FullLoader)

    def _get_x_variants(self, atomtypes):
        from itertools import product

        permutations = np.array(
            sorted(
                list(product([False, True], repeat=len(atomtypes))),
                key=lambda x: sum(x),
            )
        )
        variants = []
        for per in permutations:
            tmpat = atomtypes.copy()
            tmpat[per] = "X"
            variants.append(tmpat)
        return variants

    def get_parameters(self, term, atomtypes):
        from itertools import permutations

        atomtypes = np.array(atomtypes)
        variants = self._get_x_variants(atomtypes)
        if term == "bonds" or term == "angles" or term == "dihedrals":
            variants += self._get_x_variants(atomtypes[::-1])
        elif term == "impropers":
            # Position 2 is the improper center
            perms = np.array([x for x in list(permutations((0, 1, 2, 3))) if x[2] == 2])
            for perm in perms:
                variants += self._get_x_variants(atomtypes[perm])
        variants = sorted(variants, key=lambda x: sum(x == "X"))

        termpar = self.prm[term]
        for var in variants:
            atomtypestr = ", ".join(var)
            if len(var) > 1:
                atomtypestr = "(" + atomtypestr + ")"
            if atomtypestr in termpar:
                return termpar[atomtypestr]
        raise RuntimeError(f"{atomtypes} doesn't have {term} information in the FF")

    def getAtomTypes(self):
        return np.unique(self.prm["atomtypes"])

    def getCharge(self, at):
        params = self.get_parameters("electrostatics", [at,])
        return params["charge"]

    def getMass(self, at):
        return self.prm["masses"][at]

    def getLJ(self, at):
        params = self.get_parameters("lj", [at,])
        return params["sigma"], params["epsilon"]

    def getBond(self, at1, at2):
        params = self.get_parameters("bonds", [at1, at2])
        return params["k0"], params["req"]

    def getAngle(self, at1, at2, at3):
        params = self.get_parameters("angles", [at1, at2, at3])
        return params["k0"], radians(params["theta0"])

    def getDihedral(self, at1, at2, at3, at4):
        params = self.get_parameters("dihedrals", [at1, at2, at3, at4])

        terms = []
        for term in params["terms"]:
            terms.append([term["phi_k"], radians(term["phase"]), term["per"]])

        return terms

    def get14(self, at1, at2, at3, at4):
        params = self.get_parameters("dihedrals", [at1, at2, at3, at4])

        terms = []
        for term in params["terms"]:
            terms.append([term["phi_k"], radians(term["phase"]), term["per"]])

        lj1 = self.get_parameters("lj", [at1,])
        lj4 = self.get_parameters("lj", [at4,])
        return (
            params["scnb"],
            params["scee"],
            lj1["sigma14"],
            lj1["epsilon14"],
            lj4["sigma14"],
            lj4["epsilon14"],
        )

    def getImproper(self, at1, at2, at3, at4):
        params = self.get_parameters("impropers", [at1, at2, at3, at4])
        return params["phi_k"], radians(params["phase"]), params["per"]
