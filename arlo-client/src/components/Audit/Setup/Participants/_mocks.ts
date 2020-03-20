const jurisdictionFile = new File(
  [
    'Jurisdiction","Admin Email"',
    '"Death Star","wtarkin@empire.gov"',
    '"Hoth","admin@rebelalliance.ninja"',
    '"Tatooine","jabba@hutt.biz"',
  ],
  'jurisdictions.csv',
  { type: 'text/csv' }
)

export default jurisdictionFile
