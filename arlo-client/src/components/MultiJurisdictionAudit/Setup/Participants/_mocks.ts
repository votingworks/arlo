import { readFileSync } from 'fs'
import { join } from 'path'

const jurisdictionFile = new File(
  [
    readFileSync(
      join(
        __dirname,
        '../../../../../public/sample_jurisdiction_filesheet.csv'
      ),
      'utf8'
    ),
  ],
  'jurisdictions.csv',
  { type: 'text/csv' }
)

export default jurisdictionFile
