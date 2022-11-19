import { readFileSync } from 'fs'
import { join } from 'path'

export const jurisdictionFile = new File(
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

export const standardizedContestsFile = new File(
  [
    readFileSync(
      join(__dirname, '../../../../../public/sample_standardized_contests.csv'),
      'utf8'
    ),
  ],
  'standardized-contests.csv',
  { type: 'text/csv' }
)

export default jurisdictionFile
