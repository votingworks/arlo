import Papa from 'papaparse'

const DEFAULT_PARSE_OPTIONS = {
  chunkSize: 1024 * 1024, // 1MB
  delimiter: ',',
  skipEmptyLines: true,
} as const

function findCsvColumnIndex(
  file: File,
  columnName: string,
  numRowsToSkip: number
): Promise<number | null> {
  return new Promise((resolve, reject) => {
    Papa.parse<string[]>(file, {
      ...DEFAULT_PARSE_OPTIONS,
      preview: numRowsToSkip + 1,
      complete: ({ data, errors }) => {
        if (errors.length > 0) {
          reject(new Error(errors[0].message))
          return
        }
        if (data.length < numRowsToSkip + 1) {
          reject(new Error('Header row not found'))
          return
        }
        const headerRow = data[numRowsToSkip]
        const columnIndex = headerRow.indexOf(columnName)
        resolve(columnIndex === -1 ? null : columnIndex)
      },
      error: reject,
    })
  })
}

function redactCsvColumnAtIndex(
  file: File,
  columnIndexToRedact: number,
  numRowsToSkip: number
): Promise<File> {
  return new Promise((resolve, reject) => {
    let output = new Blob([])
    let rowsProcessed = 0
    Papa.parse<string[]>(file, {
      ...DEFAULT_PARSE_OPTIONS,
      chunk: ({ data, errors, meta }, parser) => {
        try {
          if (errors.length > 0) {
            throw new Error(errors[0].message)
          }
          if (data.length === 0) {
            return
          }
          const rows = data.map((row, rowIndex) =>
            row.map((value, columnIndex) => {
              if (rowsProcessed + rowIndex < numRowsToSkip + 1) {
                return value
              }
              if (columnIndex === columnIndexToRedact) {
                return 'REDACTED'
              }
              return value
            })
          )
          const csv = Papa.unparse(rows, {
            escapeFormulae: false,
            newline: meta.linebreak,
          })
          output = new Blob([output, csv, meta.linebreak])
          rowsProcessed += rows.length
        } catch (error) {
          // Call reject before parser.abort because parser.abort triggers the
          // complete callback
          reject(error)
          parser.abort()
        }
      },
      complete: () => {
        resolve(
          new File([output], file.name, {
            type: file.type,
            lastModified: file.lastModified,
          })
        )
      },
      error: reject,
    })
  })
}

interface RedactCsvColumnOptions {
  numRowsToSkip?: number
}

// eslint-disable-next-line import/prefer-default-export
export async function redactCsvColumn(
  file: File,
  columnName: string,
  { numRowsToSkip = 0 }: RedactCsvColumnOptions = {}
): Promise<File> {
  try {
    const columnIndex = await findCsvColumnIndex(
      file,
      columnName,
      numRowsToSkip
    )
    return columnIndex === null
      ? file
      : await redactCsvColumnAtIndex(file, columnIndex, numRowsToSkip)
  } catch (error) {
    // Return the file unchanged on error. We don't want a failure during
    // client-side redacting to interrupt server-side parsing.
    return file
  }
}
