const flattree = [
    {'name': 'Collections', 'parent': null, 'info': 'Collection Name, Collection Description, LeadPIID, LeadPIName, DataCustodian, DataCustodianEmail, InstitutionID, InstitutionName, ProtocolID, ProtocolName, ProtcolAbbreviatedName, Discipline, DataCategory, Organ, EDRNCollaborativeGroup, ResultsAndConclusionSummary, PubMedID, ReferenceURL, Consortium, Species, OwnerPrincipal, DOI, DOIURL, CollectionVersion, CollectionID'},
    {'name': 'Datasets', 'parent': 'Collections', 'info': 'DatasetName, DatasetDescription, InvestigatorID, InvestigatorName, Institution, InstitutionName, BlindedSiteID, MethodDetails, Instrument, SpecimenType, Discipline, DataCategory, AssayType, ProcessingSoftware, ContentType, DOI, DOI URL, DateDatasetFrozen, DatasetVersion, DatasetID'},
    {'name': 'Files', 'parent': 'Datasets', 'info': 'FileName, DateFileGenerated, SubmittingSiteID, SubmittingPersonID, ProcessingLevel, ContentType, AssayType, Processing software, Processing software version, Instrument, md5sum, DOI, DOI URL, FileSubmissionDate, SubmissionVersion, FileType, FileSize'}
];

let opennodelist=['Datasets'];
