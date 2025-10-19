## Key APIs

Entities are identified using curies, but the same conceptual entity may have multiple curies. To find all the curies a given input curie we can use nodenormalizer found here: https://nodenormalization-sri.renci.org/docs. We are only interested in the get\_normalized\_nodes function, and especially in its POST implementation, which is much more efficient.  This function takes one CURIE and returns every other CURIE that it knows about for the same concept.  Here is an example payload:
```
{
  "curies": [
    "MESH:D014867",
    "NCIT:C34373"
  ],
  "conflate": true,
  "description": false,
  "drug_chemical_conflate": true
}
```
In this payload we are sending two curies that we want to ask about.  We are also saying to merge certain types of entities (conflation) and we always want these to be true. always.

The result of this query will look like:
```
{
  "MESH:D014867": {
    "id": {
      "identifier": "CHEBI:15377",
      "label": "Water"
    },
    "equivalent_identifiers": [
      {
        "identifier": "CHEBI:15377",
        "label": "water"
      },
      {
        "identifier": "UNII:059QF0KO0R",
        "label": "WATER"
      },
      {
        "identifier": "PUBCHEM.COMPOUND:962",
        "label": "Water"
      },
      {
        "identifier": "CHEMBL.COMPOUND:CHEMBL1098659",
        "label": "WATER"
      },
      {
        "identifier": "DRUGBANK:DB09145",
        "label": "Water"
      },
      {
        "identifier": "MESH:D014867",
        "label": "Water"
      },
      {
        "identifier": "CAS:231-791-2"
      },
      {
        "identifier": "CAS:7732-18-5"
      },
      {
        "identifier": "HMDB:HMDB0002111",
        "label": "Water"
      },
      {
        "identifier": "KEGG.COMPOUND:C00001",
        "label": "H2O"
      },
      {
        "identifier": "INCHIKEY:XLYOFNOQVPJJNP-UHFFFAOYSA-N"
      },
      {
        "identifier": "UMLS:C0043047",
        "label": "water"
      },
      {
        "identifier": "RXCUI:11295"
      }
    ],
    "type": [
      "biolink:SmallMolecule",
      "biolink:MolecularEntity",
      "biolink:ChemicalEntity",
      "biolink:PhysicalEssence",
      "biolink:ChemicalOrDrugOrTreatment",
      "biolink:ChemicalEntityOrGeneOrGeneProduct",
      "biolink:ChemicalEntityOrProteinOrPolypeptide",
      "biolink:NamedThing",
      "biolink:PhysicalEssenceOrOccurrent"
    ],
    "information_content": 47.7
  },
  "NCIT:C34373": {
    "id": {
      "identifier": "MONDO:0004976",
      "label": "amyotrophic lateral sclerosis"
    },
    "equivalent_identifiers": [
      {
        "identifier": "MONDO:0004976",
        "label": "amyotrophic lateral sclerosis"
      },
      {
        "identifier": "DOID:332",
        "label": "amyotrophic lateral sclerosis"
      },
      {
        "identifier": "orphanet:803"
      },
      {
        "identifier": "UMLS:C0002736",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "MESH:D000690",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "MEDDRA:10002026"
      },
      {
        "identifier": "MEDDRA:10052889"
      },
      {
        "identifier": "NCIT:C34373",
        "label": "Amyotrophic Lateral Sclerosis"
      },
      {
        "identifier": "SNOMEDCT:86044005"
      },
      {
        "identifier": "medgen:274"
      },
      {
        "identifier": "icd11.foundation:1982355687"
      },
      {
        "identifier": "ICD10:G12.21"
      },
      {
        "identifier": "ICD9:335.20"
      },
      {
        "identifier": "KEGG.DISEASE:05014"
      },
      {
        "identifier": "HP:0007354",
        "label": "Amyotrophic lateral sclerosis"
      }
    ],
    "type": [
      "biolink:Disease",
      "biolink:DiseaseOrPhenotypicFeature",
      "biolink:BiologicalEntity",
      "biolink:ThingWithTaxon",
      "biolink:NamedThing"
    ],
    "information_content": 74.9
  }
}
```

Notice that each entity returns a list of other identifiers.  Note also that types are returned. These are ordered, and we are always interested in the first element in the list, which should be the most specific. Note also that each input has an id element - this contains the _preferred_ identifier for the clique of identifiers.
