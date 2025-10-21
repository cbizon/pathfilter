Our Knowledge Graph (KG) files come as two jsonlines files.  A nodes file and an edge file.

An example node looks like this:
```json
{"id":"PUBCHEM.COMPOUND:3009304","name":"1H-1,3-Diazepine-1,3(2H)-dihexanoic acid, tetrahydro-5,6-dihydroxy-2-oxo-4,7-bis(phenylmethyl)-, (4R,5S,6S,7R)-","category":["biolink:SmallMolecule","biolink:MolecularEntity","biolink:ChemicalEntity","biolink:PhysicalEssence","biolink:ChemicalOrDrugOrTreatment","biolink:ChemicalEntityOrGeneOrGeneProduct","biolink:ChemicalEntityOrProteinOrPolypeptide","biolink:NamedThing","biolink:PhysicalEssenceOrOccurrent"],"equivalent_identifiers":["PUBCHEM.COMPOUND:3009304","CHEMBL.COMPOUND:CHEMBL29089","CAS:152928-75-1","INCHIKEY:XGEGDSLAQZJGCW-HHGOQMMWSA-N"]}
```
Important elements: 
- id - this is the CURIE that the TMKP has assigned to the node.  It may not be the normalized identifier.
- category: A list of categories. These are hierarchical, and the first element is the most specific, and usually the one of interest.
- equivalent_identifiers: not too important for this, but notice that each entity can have many identifiers

An example edge looks like this:
```json
{"subject":"NCBITaxon:1661386","predicate":"biolink:subclass_of","object":"NCBITaxon:286","primary_knowledge_source":"infores:ubergraph","knowledge_level":"knowledge_assertion","agent_type":"manual_agent","original_subject":"NCBITaxon:1661386","original_object":"NCBITaxon:286"}
```

Important attributes:
- subject, object: These id's are from the nodes file
- predicate, \*qualifier.: The predicate defines the relations between the subject and object, but many edges also have things like object\_direction\_qualifier, and they are important in understanding the meaning of the edge
- sentences: these are the text from which that edge was derived.

