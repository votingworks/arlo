import Papa from 'papaparse'

const DEFAULT_PARSE_OPTIONS = {
  chunkSize: 1024 * 1024, // 1MB
  delimiter: ',',

  /**
   * We don't know the file's encoding (UTF-8, Windows-1252, etc.), and
   * decoding with the wrong one could corrupt characters. Instead, decode as
   * x-user-defined, which maps ASCII bytes to themselves and bytes
   * 0x80-0xFF to U+F780-U+F7FF. See {@link encodeXUserDefined} for the inverse
   * logic.
   *
   * This makes it such that we can detect CSV delimiters and line breaks
   * without issue but treat all values as opaque blobs and round trip them
   * unchanged.
   */
  encoding: 'x-user-defined',
} as const

export const BOM = {
  UTF8: new Uint8Array([0xef, 0xbb, 0xbf]),
  UTF16LE: new Uint8Array([0xff, 0xfe]),
  UTF16BE: new Uint8Array([0xfe, 0xff]),
} as const

type BomType = keyof typeof BOM

interface FileContents {
  bom?: { type: BomType; bytes: Uint8Array<ArrayBuffer> }
  fileWithoutBom: File
}

/**
 * Given a string decoded as an x-user-defined string, returns the original
 * bytes.
 */
function encodeXUserDefined(text: string): Uint8Array<ArrayBuffer> {
  const bytes = new Uint8Array(text.length)
  for (let i = 0; i < text.length; i += 1) {
    const charCode = text.charCodeAt(i)
    bytes[i] = charCode < 0x80 ? charCode : charCode - 0xf700
  }
  return bytes
}

async function fileStartsWith(
  file: File,
  prefix: Uint8Array
): Promise<boolean> {
  const fileFirstBytes = new Uint8Array(
    await file.slice(0, prefix.length).arrayBuffer()
  )
  return (
    fileFirstBytes.length === prefix.length &&
    prefix.every((byte, i) => fileFirstBytes[i] === byte)
  )
}

async function parseBom(file: File): Promise<FileContents> {
  for (const [bomType, bomBytes] of Object.entries(BOM)) {
    // oxlint-disable-next-line no-await-in-loop
    if (await fileStartsWith(file, bomBytes)) {
      return {
        bom: { type: bomType as BomType, bytes: bomBytes },
        fileWithoutBom: new File([file.slice(bomBytes.length)], file.name, {
          lastModified: file.lastModified,
          type: file.type,
        }),
      }
    }
  }
  return {
    bom: undefined,
    fileWithoutBom: file,
  }
}

function findCsvColumnIndex(
  { fileWithoutBom }: FileContents,
  columnName: string,
  numRowsToSkip: number
): Promise<number | null> {
  return new Promise((resolve, reject) => {
    Papa.parse<string[]>(fileWithoutBom, {
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
  { bom, fileWithoutBom }: FileContents,
  columnIndexToRedact: number,
  numRowsToSkip: number
): Promise<File> {
  return new Promise((resolve, reject) => {
    let output = bom ? new Blob([bom.bytes]) : new Blob([])
    let rowsProcessed = 0
    Papa.parse<string[]>(fileWithoutBom, {
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
            rowsProcessed + rowIndex < numRowsToSkip + 1 // + 1 for the header row
              ? row
              : row.map((value, columnIndex) =>
                  columnIndex === columnIndexToRedact ? 'REDACTED' : value
                )
          )
          const csv = Papa.unparse(rows, {
            escapeFormulae: false,
            newline: meta.linebreak,
          })
          output = new Blob([
            output,
            encodeXUserDefined((rowsProcessed > 0 ? meta.linebreak : '') + csv),
          ])
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
          new File([output], fileWithoutBom.name, {
            lastModified: fileWithoutBom.lastModified,
            type: fileWithoutBom.type,
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

export async function redactCsvColumn(
  file: File,
  columnName: string,
  { numRowsToSkip = 0 }: RedactCsvColumnOptions = {}
): Promise<File> {
  try {
    const fileContents = await parseBom(file)
    if (
      fileContents.bom?.type === 'UTF16LE' ||
      fileContents.bom?.type === 'UTF16BE'
    ) {
      throw new Error('UTF-16-encoded files not yet handled')
    }

    const columnIndex = await findCsvColumnIndex(
      fileContents,
      columnName,
      numRowsToSkip
    )
    return columnIndex === null
      ? file
      : await redactCsvColumnAtIndex(fileContents, columnIndex, numRowsToSkip)
  } catch (error) {
    // oxlint-disable-next-line no-console
    console.error(error instanceof Error ? error.message : String(error))

    // Return the file unchanged on error. We don't want a failure during
    // client-side redacting to interrupt server-side parsing.
    return file
  }
}
