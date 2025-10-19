Entities have many string names.  Going from CURIES(identifiers) to strings, and going from strings to CURIES is the job of the API called name resolver found here:  https://name-resolution-sri.renci.org/docs
This API has 3 functions of interest:  
1) lookup: Take a string and return possible curies that match
2) bulk-lookup: Take multiple strings and return possible curies for each (more efficient)
3) synonyms: Take a curie (which must be the preferred id from nodenorm) and return all known lexical synonyms for that curie.

Synonyms Input:
```
{
  "preferred_curies": [
    "MONDO:0005737",
    "MONDO:0009757"
  ]
}
```
Synonyms Output:
```
{
  "MONDO:0005737": {
    "curie": "MONDO:0005737",
    "names": [
      "EHF",
      "Ebola",
      "Ebola fever",
      "Ebola disease",
      "disease ebola",
      "EBOLA VIRUS DIS",
      "Ebola Infection",
      "Infection, Ebola",
      "Ebola virus disease",
      "Ebola Virus Disease",
      "ebola virus disease",
      "Ebolavirus Infection",
      "Infection, Ebolavirus",
      "Ebola Virus Infection",
      "Ebola virus infection",
      "Ebolavirus Infections",
      "ebola virus infection",
      "Infection, Ebola Virus",
      "Infections, Ebolavirus",
      "Virus Infection, Ebola",
      "Ebola Hemorrhagic Fever",
      "ebola fever hemorrhagic",
      "ebola hemorrhagic fever",
      "Ebola hemorrhagic fever",
      "Ebola haemorrhagic fever",
      "Hemorrhagic Fever, Ebola",
      "ebola haemorrhagic fever",
      "EVD - Ebola virus disease",
      "Ebolavirus infectious disease",
      "Ebola virus hemorrhagic fever",
      "Ebolavirus disease or disorder",
      "Viral hemorrhagic fever, Ebola",
      "Ebola virus disease (disorder)",
      "Viral haemorrhagic fever, Ebola",
      "Ebolavirus caused disease or disorder",
      "Ebola virus hemorrhagic fever (diagnosis)"
    ],
    "names_exactish": [
      "EHF",
      "Ebola",
      "Ebola fever",
      "Ebola disease",
      "disease ebola",
      "EBOLA VIRUS DIS",
      "Ebola Infection",
      "Infection, Ebola",
      "Ebola virus disease",
      "Ebola Virus Disease",
      "ebola virus disease",
      "Ebolavirus Infection",
      "Infection, Ebolavirus",
      "Ebola Virus Infection",
      "Ebola virus infection",
      "Ebolavirus Infections",
      "ebola virus infection",
      "Infection, Ebola Virus",
      "Infections, Ebolavirus",
      "Virus Infection, Ebola",
      "Ebola Hemorrhagic Fever",
      "ebola fever hemorrhagic",
      "ebola hemorrhagic fever",
      "Ebola hemorrhagic fever",
      "Ebola haemorrhagic fever",
      "Hemorrhagic Fever, Ebola",
      "ebola haemorrhagic fever",
      "EVD - Ebola virus disease",
      "Ebolavirus infectious disease",
      "Ebola virus hemorrhagic fever",
      "Ebolavirus disease or disorder",
      "Viral hemorrhagic fever, Ebola",
      "Ebola virus disease (disorder)",
      "Viral haemorrhagic fever, Ebola",
      "Ebolavirus caused disease or disorder",
      "Ebola virus hemorrhagic fever (diagnosis)"
    ],
    "types": [
      "Disease",
      "DiseaseOrPhenotypicFeature",
      "BiologicalEntity",
      "ThingWithTaxon",
      "NamedThing",
      "Entity"
    ],
    "preferred_name": "Ebola hemorrhagic fever",
    "shortest_name_length": 3,
    "clique_identifier_count": 15,
    "curie_suffix": 5737,
    "id": "259aaf70-b8a3-4cec-adf9-aa886867be29",
    "_version_": 1841051406731051000
  },
  "MONDO:0009757": {
    "curie": "MONDO:0009757",
    "names": [
      "NPC1",
      "NIEMANN PICK DIS TYPE D",
      "NIEMANN PICKS DIS TYPE D",
      "Niemann Pick Type D Disease",
      "Niemann-Pick disease type D",
      "Niemann pick disease type D",
      "Niemann Pick Disease Type D",
      "Niemann-Pick Disease Type D",
      "Niemann-Pick Type D Disease",
      "Niemann-Pick Disease, Type D",
      "Niemann-Pick disease, type D",
      "Niemann-Pick disease, type C",
      "Type C1 Niemann-Pick Disease",
      "Niemann-Pick disease type C1",
      "Niemann Pick Disease, Type D",
      "NIEMANN-PICK DISEASE, TYPE D",
      "type C1 Niemann-Pick disease",
      "Niemann Pick's Disease Type D",
      "Niemann-Pick's Disease Type D",
      "NIEMANN-PICK DISEASE, TYPE C1",
      "Niemann-Pick disease, type C1",
      "Niemann-Pick Disease, Type C1",
      "Niemann-PICK disease, type C1",
      "NIEMANN PICK DIS NOVE SCOTIAN",
      "Niemann Pick Disease, Type C1",
      "Niemann Pick Disease, Nova Scotian",
      "Niemann-Pick Disease, Nova Scotian",
      "Niemann-Pick disease, Nova Scotian",
      "Niemann-Pick disease, type D (disorder)",
      "Niemann-Pick disease type D (diagnosis)",
      "Niemann-Pick Disease, Nova Scotian Type",
      "Niemann-Pick disease, nova Scotian type",
      "NIEMANN-PICK DISEASE, NOVA SCOTIAN TYPE",
      "Niemann-Pick disease type C1 (diagnosis)",
      "Nova Scotia Niemann-Pick Disease (Type D)",
      "Nova Scotia Niemann Pick Disease (Type D)",
      "Niemann-Pick disease, type C, subacute form",
      "Niemann Pick disease, Subacute Juvenile Form",
      "Niemann-Pick disease, subacute juvenile form",
      "Niemann-Pick disease, Subacute Juvenile Form",
      "NIEMANN-PICK DISEASE, SUBACUTE JUVENILE FORM",
      "Niemann-Pick disease, chronic neuronopathic form",
      "Nova Scotia (Type D) Form of Niemann-Pick Disease",
      "Niemann-Pick disease, type C, subacute form (disorder)",
      "Niemann-Pick disease without sphingomyelinase deficiency",
      "Niemann-Pick disease with cholesterol esterification block",
      "neurovisceral storage disease with vertical supranuclear ophthalmoplegia"
    ],
    "names_exactish": [
      "NPC1",
      "NIEMANN PICK DIS TYPE D",
      "NIEMANN PICKS DIS TYPE D",
      "Niemann Pick Type D Disease",
      "Niemann-Pick disease type D",
      "Niemann pick disease type D",
      "Niemann Pick Disease Type D",
      "Niemann-Pick Disease Type D",
      "Niemann-Pick Type D Disease",
      "Niemann-Pick Disease, Type D",
      "Niemann-Pick disease, type D",
      "Niemann-Pick disease, type C",
      "Type C1 Niemann-Pick Disease",
      "Niemann-Pick disease type C1",
      "Niemann Pick Disease, Type D",
      "NIEMANN-PICK DISEASE, TYPE D",
      "type C1 Niemann-Pick disease",
      "Niemann Pick's Disease Type D",
      "Niemann-Pick's Disease Type D",
      "NIEMANN-PICK DISEASE, TYPE C1",
      "Niemann-Pick disease, type C1",
      "Niemann-Pick Disease, Type C1",
      "Niemann-PICK disease, type C1",
      "NIEMANN PICK DIS NOVE SCOTIAN",
      "Niemann Pick Disease, Type C1",
      "Niemann Pick Disease, Nova Scotian",
      "Niemann-Pick Disease, Nova Scotian",
      "Niemann-Pick disease, Nova Scotian",
      "Niemann-Pick disease, type D (disorder)",
      "Niemann-Pick disease type D (diagnosis)",
      "Niemann-Pick Disease, Nova Scotian Type",
      "Niemann-Pick disease, nova Scotian type",
      "NIEMANN-PICK DISEASE, NOVA SCOTIAN TYPE",
      "Niemann-Pick disease type C1 (diagnosis)",
      "Nova Scotia Niemann-Pick Disease (Type D)",
      "Nova Scotia Niemann Pick Disease (Type D)",
      "Niemann-Pick disease, type C, subacute form",
      "Niemann Pick disease, Subacute Juvenile Form",
      "Niemann-Pick disease, subacute juvenile form",
      "Niemann-Pick disease, Subacute Juvenile Form",
      "NIEMANN-PICK DISEASE, SUBACUTE JUVENILE FORM",
      "Niemann-Pick disease, chronic neuronopathic form",
      "Nova Scotia (Type D) Form of Niemann-Pick Disease",
      "Niemann-Pick disease, type C, subacute form (disorder)",
      "Niemann-Pick disease without sphingomyelinase deficiency",
      "Niemann-Pick disease with cholesterol esterification block",
      "neurovisceral storage disease with vertical supranuclear ophthalmoplegia"
    ],
    "types": [
      "Disease",
      "DiseaseOrPhenotypicFeature",
      "BiologicalEntity",
      "ThingWithTaxon",
      "NamedThing",
      "Entity"
    ],
    "preferred_name": "Niemann-Pick disease, type C1",
    "shortest_name_length": 4,
    "clique_identifier_count": 12,
    "curie_suffix": 9757,
    "id": "dcc793c5-8579-4773-a4e5-7819e0f9943b",
    "_version_": 1841051436057624600
  }
}
```

In these outputs we are interested in "names" and especially "preferred\_name".

Lookup input:
```
curl -X 'POST' \
  'https://name-resolution-sri.renci.org/lookup?string=doxorubicin&autocomplete=false&highlighting=false&offset=0&limit=10&biolink_type=SmallMolecule' \
  -H 'accept: application/json' \
  -d ''
```

Lookup output:
```
[
  {
    "curie": "CHEBI:28748",
    "label": "Doxorubicin",
    "highlighting": {},
    "synonyms": [
      "ADM",
      "ADR",
      "adr",
      ...
    ],
    "taxa": [],
    "types": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:Entity",
      "biolink:PhysicalEssenceOrOccurrent",
      "biolink:MolecularMixture",
      "biolink:ChemicalMixture",
      "biolink:Drug",
      "biolink:OntologyClass"
    ],
    "score": 9395.258,
    "clique_identifier_count": 132
  },
  {
    "curie": "CHEBI:64816",
    "label": "doxorubicin(1+)",
    "highlighting": {},
    "synonyms": [
      "doxorubicin",
      "Doxorubicin(1+)",
      "doxorubicin(1+)",
      "doxorubicin cation",
      "(1S,3S)-3,5,12-trihydroxy-3-(hydroxyacetyl)-10-methoxy-6,11-dioxo-1,2,3,4,6,11-hexahydrotetracen-1-yl 3-azaniumyl-2,3,6-trideoxy-alpha-L-lyxo-hexopyranoside"
    ],
    "taxa": [],
    "types": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:Entity",
      "biolink:PhysicalEssenceOrOccurrent"
    ],
    "score": 447.1852,
    "clique_identifier_count": 3
  },
]
```

Note that there are ways to filter names that will often give improved results. In particular, we can filter to a particular biolink class if we know it, or if we are looking up genes/proteins we can ask for a particular taxon (usually limiting to Humans (NCBITaxon:9606)
