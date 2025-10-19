def is_good_edge_messy(x):
    if x[2] in ["biolink:Disease --> biolink:SmallMolecule --> biolink:Gene --> biolink:SmallMolecule", "biolink:Disease --> biolink:ChemicalEntity --> biolink:Gene --> biolink:SmallMolecule", "biolink:Disease --> biolink:SmallMolecule --> biolink:Disease --> biolink:SmallMolecule"]:
        if x[3] in ["{'biolink:treats_or_applied_or_studied_to_treat'}", "{'biolink:treats'}", "{'biolink:has_adverse_event', 'biolink:treats', 'biolink:treats_or_applied_or_studied_to_treat'}", "{'biolink:causes', 'biolink:treats_or_applied_or_studied_to_treat'}", "{'biolink:contributes_to'}" , "{'biolink:causes'}", "{'biolink:has_adverse_event'}", "{'biolink:contraindicated_in'}", "{'biolink:related_to'}"]:
            return False
    return True

def is_not_chemical_start_edge(x):
    if x[2].startswith("biolink:Disease --> biolink:SmallMolecule") or x[2].startswith("biolink:Disease --> biolink:ChemicalEntity") or x[2].startswith("biolink:Disease --> biolink:MolecularMixture"):
        return False
    return True

def no_dupe_types(x):
    types = x[2].split(" --> ")
    newtypes = []
    for tp in types:
        if tp in ["biolink:ChemicalEntity", "biolink:SmallMolecule", "biolink:MolecularMixture", "biolink:ComplexMolecularMixture"]:
            newtypes.append("biolink:ChemicalEntity")
        elif tp in ["biolink:Protein"]:
            newtypes.append("biolink:Gene")
        else:
            newtypes.append(tp)
    n = len(set(newtypes))
    return n == 4

def no_end_pheno(x):
    if x[2].endswith("biolink:PhenotypicFeature --> biolink:SmallMolecule"):
        return False
    return True

def no_expression(x):
    return not "expressed_in" in x[4]

def no_related_to(x):
    return not "{'biolink:related_to'}" in x[2:6]

def all_edges(x):
    return True

with open("paths.tsv","r") as inf, open("keeper_paths.tsv","w") as outf:
    nall = 0
    nkept = 0
    nkit = 0
    nkitkept = 0
    nhist = 0
    nhistkept = 0
    for line in inf:
        x = line.strip().split('\t')
        if " KIT " in x[0]:
            nkit += 1
        if " Histamine " in x[0]:
            nhist += 1
        nall += 1
        #ruleset = [no_dupe_types, no_expression, no_end_pheno, no_related_to]
        ruleset = [no_dupe_types, no_expression,  no_related_to]
        passedge = True
        for rule in ruleset:
            passedge = passedge and rule(x)
        if passedge:
            nkept += 1
            outf.write(line)
            if " KIT " in x[0]:
                nkitkept += 1
            if " Histamine " in x[0]:
                nhistkept += 1
    print (f"{nkit} / {nall} {nkit/nall}")
    print (f"{nkitkept} / {nkept} {nkitkept/nkept}")

    print (f"{nhist} / {nall} {nhist/nall}")
    print (f"{nhistkept} / {nkept} {nhistkept/nkept}")

