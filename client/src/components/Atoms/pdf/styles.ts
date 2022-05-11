import ReactPdf from '@react-pdf/renderer'

/**
 * Since @react-pdf/renderer doesn't export its Style type, we have to do some extra work to get to
 * it
 *
 * ReactPdf.NodeProps['style']         --> Style | Style[] | undefined
 * After excluding any[] and undefined --> Style
 */
export type PdfStyle = Exclude<
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Exclude<ReactPdf.NodeProps['style'], any[]>,
  undefined
>
